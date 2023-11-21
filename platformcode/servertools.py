# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Server management
# --------------------------------------------------------------------------------

from __future__ import division
from __future__ import absolute_import
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3: import urllib.parse as urlparse
else: import urlparse

from future.builtins import range

import re

from platformcode import filetools, httptools, jsontools
from platformcode import config, logger, platformtools

dict_servers_parameters = {}
server_list = {}


def get_server_parameters(server):
    """
    Get data from server
    @param server: Server name
    @type server: str

    @return: server data
    @rtype: dict
    """
    # logger.info("server %s" % server)
    global dict_servers_parameters
    server = server.split('.')[0]
    if not server:
        return {}

    if server not in dict_servers_parameters and server not in ['servers']:
        try:
            path = ''
            # Servers
            if filetools.isfile(filetools.join(config.get_runtime_path(), "servers", server + ".json")):
                path = filetools.join(config.get_runtime_path(), "servers", server + ".json")

            # Debriders
            elif filetools.isfile(filetools.join(config.get_runtime_path(), "servers", "debriders", server + ".json")):
                path = filetools.join(config.get_runtime_path(), "servers", "debriders", server + ".json")

            # When the server is not well defined in the channel (there is no connector), it shows an error because there is no "path" and the channel has to be checked
            dict_server = jsontools.load(filetools.read(path))

            dict_server["name"] = translate_server_name(dict_server["name"])

            # Images: url and local files are allowed inside "resources / images"
            if dict_server.get("thumbnail") and "://" not in dict_server["thumbnail"]:
                dict_server["thumbnail"] = filetools.join(config.get_runtime_path(), "resources", "media",
                                                        "servers", dict_server["thumbnail"])
            for k in ['premium', 'id']:
                dict_server[k] = dict_server.get(k, list())

                if isinstance(dict_server[k], str):
                    dict_server[k] = [dict_server[k]]

            if "find_videos" in dict_server:
                dict_server['find_videos']["patterns"] = dict_server['find_videos'].get("patterns", list())
                dict_server['find_videos']["ignore_urls"] = dict_server['find_videos'].get("ignore_urls", list())

            if "settings" in dict_server:
                dict_server['has_settings'] = True
            else:
                dict_server['has_settings'] = False

            dict_servers_parameters[server] = dict_server

        except:
            mensaje = config.get_localized_string(59986) % server
            import traceback
            logger.error(mensaje + traceback.format_exc())
            return {}

    return dict_servers_parameters[server]

def get_server_controls_settings(server_name):
    dict_settings = {}

    list_controls = get_server_parameters(server_name).get('settings', [])
    import copy
    list_controls = copy.deepcopy(list_controls)

    # Conversion de str a bool, etc...
    for c in list_controls:
        if 'id' not in c or 'type' not in c or 'default' not in c:
            # If any control in the list does not have id, type or default, we ignore it
            continue

        # new dict with key(id) and value(default) from settings
        dict_settings[c['id']] = c['default']

    return list_controls, dict_settings


def get_server_setting(name, server, default=None):
    """
        Returns the configuration value of the requested parameter.

        Returns the value of the parameter 'name' in the own configuration of the server 'server'.

        Look in the path \addon_data\plugin.video.addon\settings_servers for the file server_data.json and read
        the value of the parameter 'name'. If the server_data.json file does not exist look in the servers folder for the file
        server.json and create a server_data.json file before returning the requested value. If the parameter 'name'
        also does not exist in the server.json file the default parameter is returned.


        @param name: parameter name
        @type name: str
        @param server: server name
        @type server: str
        @param default: return value in case the name parameter does not exist
        @type default: any

        @return: The parameter value 'name'
        @rtype: any

        """
    # We create the folder if it does not exist
    if not filetools.exists(filetools.join(config.get_data_path(), "settings_servers")):
        filetools.mkdir(filetools.join(config.get_data_path(), "settings_servers"))

    file_settings = filetools.join(config.get_data_path(), "settings_servers", server + "_data.json")
    dict_settings = {}
    dict_file = {}
    if filetools.exists(file_settings):
        # We get saved configuration from ../settings/channel_data.json
        try:
            dict_file = jsontools.load(filetools.read(file_settings))
            if isinstance(dict_file, dict) and 'settings' in dict_file:
                dict_settings = dict_file['settings']
        except EnvironmentError:
            logger.info("ERROR when reading the file: %s" % file_settings)

    if not dict_settings or name not in dict_settings:
        # We get controls from the file ../servers/server.json
        try:
            list_controls, default_settings = get_server_controls_settings(server)
        except:
            default_settings = {}
        if name in default_settings:  # If the parameter exists in the server.json we create the server_data.json
            default_settings.update(dict_settings)
            dict_settings = default_settings
            dict_file['settings'] = dict_settings
            # We create the file ../settings/channel_data.json
            if not filetools.write(file_settings, jsontools.dump(dict_file)):
                logger.error("ERROR saving file: %s" % file_settings)

    # We return the value of the local parameter 'name' if it exists, if default is not returned
    return dict_settings.get(name, default)


def set_server_setting(name, value, server):
    # We create the folder if it does not exist
    if not filetools.exists(filetools.join(config.get_data_path(), "settings_servers")):
        filetools.mkdir(filetools.join(config.get_data_path(), "settings_servers"))

    file_settings = filetools.join(config.get_data_path(), "settings_servers", server + "_data.json")
    dict_settings = {}

    dict_file = None

    if filetools.exists(file_settings):
        # We get saved configuration from ../settings/channel_data.json
        try:
            dict_file = jsontools.load(filetools.read(file_settings))
            dict_settings = dict_file.get('settings', {})
        except EnvironmentError:
            logger.error("ERROR when reading the file: %s" % file_settings)

    dict_settings[name] = value

    # we check if dict_file exists and it is a dictionary, if not we create it
    if dict_file is None or not dict_file:
        dict_file = {}

    dict_file['settings'] = dict_settings

    # We create the file ../settings/channel_data.json
    if not filetools.write(file_settings, jsontools.dump(dict_file)):
        logger.error("ERROR saving file: %s" % file_settings)
        return None

    return value


def get_servers_list():
    """
    Get a dictionary with all available servers

    @return: Diccionario cuyas claves son los nombre de los servidores (nombre del json) and as a value a dictionary with the server parameters.
    @rtype: dict
    """
    global server_list
    if not server_list:
        for server in filetools.listdir(filetools.join(config.get_runtime_path(), "servers")):
            if server.endswith(".json") and not server == "version.json":
                server_parameters = get_server_parameters(server)
                if server_parameters['active']:
                    server_list[server.split(".")[0]] = server_parameters

        if type(server_list) != dict: server_list = sort_servers(server_list)
    return server_list


def get_debriders_list():
    """
    Get a dictionary with all available debriders

    @return: Dictionary whose keys are the names of the debriders (name of the json) and as a value a dictionary with the server parameters.
    @rtype: dict
    """
    server_list = {}
    for server in filetools.listdir(filetools.join(config.get_runtime_path(), "servers", "debriders")):
        if server.endswith(".json"):
            server_parameters = get_server_parameters(server)
            if server_parameters["active"] == True:
                logger.info(server_parameters)
                server_list[server.split(".")[0]] = server_parameters
    return server_list


def sort_servers(servers_list):
    """
    If the option "Order servers" is activated in the server configuration and there is a list of servers
    favorites in settings use it to sort the servers_list list
    :param servers_list: List of servers to order. The items in the servers_list can be strings or Item objects. In both cases it is necessary to have an item.server attribute of type str.
    :return: List of the same type of objects as servers_list ordered according to the favorite servers.
    """
    def index(lst, value):
        if value in lst:
            return lst.index(value)
        else:
            logger.debug('Index not found: ' + value)
            return 999
    if not servers_list:
        return []

    blacklisted_servers = config.get_setting("black_list", server='servers', default=[])
    favorite_servers = config.get_setting('favorites_servers_list', server='servers', default=[])
    favorite_servers = [s for s in favorite_servers if s not in blacklisted_servers]
    if isinstance(servers_list[0], str):
        servers_list = sorted(servers_list, key=lambda x: favorite_servers.index(x) if x in favorite_servers else 999)
        return servers_list

    favorite_quality = ['4k', '2160p', '2160', '4k2160p', '4k2160', '4k 2160p', '4k 2160', '2k',
                    'fullhd', 'fullhd 1080', 'fullhd 1080p', 'full hd', 'full hd 1080', 'full hd 1080p', 'hd1080', 'hd1080p', 'hd 1080', 'hd 1080p', '1080', '1080p',
                    'hd', 'hd720', 'hd720p', 'hd 720', 'hd 720p', '720', '720p', 'hdtv',
                    'sd', '480p', '480', '360p', '360', '240p', '240']

    sorted_list = []
    inverted = False

    if config.get_setting('default_action') == 2:
        inverted = True

    # Priorities when ordering itemlist:
    #       0: Only Qualities
    #       1: Servers and Qualities
    #       2: Qualities and Servers

    priority = 0
    if config.get_setting('favorites_servers') and favorite_servers: priority = 1
    if config.get_setting('quality_priority'): priority = 2

    for item in servers_list:
        element = dict()

        # We check that it is a video item
        if 'server' not in item:
            continue

        if item.server.lower() in blacklisted_servers:
            continue

        element["index_server"] = index(favorite_servers, item.server.lower())
        element["index_quality"] = platformtools.calcResolution(item.quality)
        element['index_language'] = 0 if item.contentLanguage == 'ITA' else 1
        element['videoitem'] = item
        sorted_list.append(element)

    # We order according to priority
    if priority == 0: sorted_list.sort(key=lambda element: (element['index_language'], -element['index_quality'] if inverted else element['index_quality'] , element['videoitem'].server))
    elif priority == 1: sorted_list.sort(key=lambda element: (element['index_language'], element['index_server'], -element['index_quality'] if inverted else element['index_quality'])) # Servers and Qualities
    elif priority == 2: sorted_list.sort(key=lambda element: (element['index_language'], -element['index_quality'] if inverted else element['index_quality'], element['index_server'])) # Qualities and Servers

    return [v['videoitem'] for v in sorted_list if v]


# Checking links
def check_list_links(itemlist, numero='', timeout=3):
    """
    Check a list of video links and return it by modifying the title with verification.
    The number parameter indicates how many links to check (0:5, 1:10, 2:15, 3:20)
    The timeout parameter indicates a waiting limit to download the page
    """
    numero = numero if numero > 4 else ((int(numero) + 1) * 5) if numero != '' else 5
    import sys
    if sys.version_info[0] >= 3:
        from concurrent import futures
    else:
        from concurrent_py2 import futures
    with futures.ThreadPoolExecutor() as executor:
        checked = []
        for it in itemlist:
            if numero > 0 and it.server != '' and it.url != '':
                checked.append(executor.submit(check_video_link, it, timeout))
                numero -= 1
        for link in futures.as_completed(checked):
            res = link.result()
            if res:
                it = res[0]
                verificacion = res[1]
                it.title = verificacion + ' ' + it.title.strip()
                logger.debug('VERIFICATION= ' + verificacion)
                it.alive = verificacion
    return itemlist


def check_video_link(item, timeout=3):
    """
        Check if the link to a video is valid and return a 2-position string with verification.
        :param url, server: Link and server
        :return: str(2) '??':Could not be verified. 'Ok': The link seems to work. 'NO': It doesn't seem to work.
    """
    url = item.url
    server = item.server

    NK = u"[COLOR 0xFFF9B613][B]\u2022[/B][/COLOR]"
    OK = u"[COLOR 0xFF00C289][B]\u2022[/B][/COLOR]"
    KO = u"[COLOR 0xFFC20000][B]\u2022[/B][/COLOR]"

    try:
        server_module = __import__('servers.%s' % server, None, None, ["servers.%s" % server])
    except:
        server_module = None
        logger.error("[check_video_link] Cannot import server! %s" % server)
        return item, NK

    if hasattr(server_module, 'test_video_exists'):
        ant_timeout = httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT
        httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = timeout  # Limit download time

        try:
            video_exists, message = server_module.test_video_exists(page_url=url)
            if not video_exists:
                logger.error("[check_video_link] Does not exist! %s %s %s" % (message, server, url))
                resultado = KO
            else:
                logger.debug("[check_video_link] check ok %s %s" % (server, url))
                resultado = OK
        except:
            logger.error("[check_video_link] Can't check now! %s %s" % (server, url))
            resultado = NK

        finally:
            httptools.HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = ant_timeout  # Restore download time
            return item, resultado

    logger.debug("[check_video_link] There is no test_video_exists for server:", server)
    return item, NK


def translate_server_name(name):
    if '@' in name: return config.get_localized_string(int(name.replace('@','')))
    else: return name


# def get_server_json(server_name):
#     # logger.info("server_name=" + server_name)
#     try:
#         server_path = filetools.join(config.get_runtime_path(), "servers", server_name + ".json")
#         if not filetools.exists(server_path):
#             server_path = filetools.join(config.get_runtime_path(), "servers", "debriders", server_name + ".json")
#
#         # logger.info("server_path=" + server_path)
#         server_json = jsontools.load(filetools.read(server_path))
#         # logger.info("server_json= %s" % server_json)
#
#     except Exception as ex:
#         template = "An exception of type %s occured. Arguments:\n%r"
#         message = template % (type(ex).__name__, ex.args)
#         logger.error(" %s" % message)
#         server_json = None
#
#     return server_json
