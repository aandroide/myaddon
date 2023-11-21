# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# platformtools
# ------------------------------------------------------------
# Tools responsible for adapting the different dialog boxes to a specific platform.
# version 2.0
# ------------------------------------------------------------

import sys
if sys.version_info[0] >= 3:
    PY3 = True
    import urllib.parse as urllib
    from concurrent import futures
else:
    PY3 = False
    import urllib
    from concurrent_py2 import futures


import os, xbmc, xbmcgui, xbmcplugin
from lib.past.utils import old_div
from platformcode import logger, config

addon = config.__settings__
addon_icon = os.path.join( addon.getAddonInfo( "path" ),'resources', 'media', "logo.gif" )

# class XBMCPlayer(xbmc.Player):

#     def __init__(self, *args):
#         pass


xbmc_player = xbmc.Player()

play_canceled = False


def dialog_ok(heading, message):
    dialog = xbmcgui.Dialog()
    return dialog.ok(heading, message)


def dialog_notification(heading, message, icon=3, time=5000, sound=True):
    dialog = xbmcgui.Dialog()
    try:
        l_icono = [xbmcgui.NOTIFICATION_INFO, xbmcgui.NOTIFICATION_WARNING, xbmcgui.NOTIFICATION_ERROR, addon_icon]
        dialog.notification(heading, message, l_icono[icon], time, sound)
    except:
        dialog_ok(heading, message)


def dialog_yesno(heading, message, nolabel=config.get_localized_string(70170), yeslabel=config.get_localized_string(30022), autoclose=0, customlabel=None):
    dialog = xbmcgui.Dialog()
    # customlabel only work on kodi 19
    if PY3 and customlabel:
        return dialog.yesnocustom(heading, message, customlabel=customlabel, nolabel=nolabel, yeslabel=yeslabel, autoclose=autoclose)
    else:
        return dialog.yesno(heading, message, nolabel=nolabel, yeslabel=yeslabel, autoclose=autoclose)


def dialog_select(heading, _list, preselect=0, useDetails=False):
    return xbmcgui.Dialog().select(heading, _list, preselect=preselect, useDetails=useDetails)


def dialog_multiselect(heading, _list, autoclose=0, preselect=[], useDetails=False):
    return xbmcgui.Dialog().multiselect(heading, _list, autoclose=autoclose, preselect=preselect, useDetails=useDetails)


def dialog_progress(heading, message):
    if get_window() in ('WINDOW_HOME', 'WINDOW_SETTINGS_MENU', 'WINDOW_SETTINGS_INTERFACE', 'WINDOW_SKIN_SETTINGS', 'SKIN'):
        # in widget, hide any progress
        class Dummy(object):
            def __getattr__(self, name):
                def _missing(*args, **kwargs):
                    pass
                return _missing
        return Dummy()
    else:
        dialog = xbmcgui.DialogProgress()
        dialog.create(heading, message)
        return dialog


def dialog_progress_bg(heading, message=""):
    try:
        dialog = xbmcgui.DialogProgressBG()
        dialog.create(heading, message)
        return dialog
    except:
        return dialog_progress(heading, message)


def dialog_input(default="", heading="", hidden=False):
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    else:
        return None


def dialog_numeric(_type, heading, default=""):
    dialog = xbmcgui.Dialog()
    d = dialog.numeric(_type, heading, default)
    return d


def dialog_textviewer(heading, text):  # available from kodi 16
    return xbmcgui.Dialog().textviewer(heading, text)


def dialog_browse(_type, heading, shares="files", mask="", useThumbs=False, treatAsFolder=False, defaultt="", enableMultiple=False):
    dialog = xbmcgui.Dialog()
    d = dialog.browse(_type, heading, shares, mask, useThumbs, treatAsFolder, defaultt, enableMultiple)
    return d


def dialog_register(heading, user=False, email=False, password=False, user_default='', email_default='', password_default='', captcha_img=''):
    class Register(xbmcgui.WindowXMLDialog):
        def Start(self, heading, user, email, password, user_default, email_default, password_default, captcha_img):
            self.result = {}
            self.heading = heading
            self.user = user
            self.email = email
            self.password = password
            self.user_default = user_default
            self.email_default = email_default
            self.password_default = password_default
            self.captcha_img = captcha_img
            self.doModal()

            return self.result

        def __init__(self, *args, **kwargs):
            self.mensaje = kwargs.get("mensaje")
            self.imagen = kwargs.get("imagen")

        def onInit(self):
            #### Kodi 18 compatibility ####
            if config.get_platform(True)['num_version'] < 18:
                self.setCoordinateResolution(2)
            height = 90
            self.getControl(10002).setText(self.heading)
            if self.user:
                self.getControl(10003).setText(self.user_default)
                height += 70
            else:
                self.getControl(10003).setVisible(False)

            if self.email:
                self.getControl(10004).setText(self.email_default)
                height += 70
            else:
                self.getControl(10004).setVisible(False)

            if self.password:
                self.getControl(10005).setText(self.password_default)
                height += 70
            else:
                self.getControl(10005).setVisible(False)

            if self.captcha_img:
                self.getControl(10007).setImage(self.captcha_img)
                height += 240
            else:
                self.getControl(10006).setVisible(False)
                self.getControl(10007).setVisible(False)
            height += 40
            if height < 250: height = 250
            self.getControl(10000).setHeight(height)
            self.getControl(10001).setHeight(height)
            self.getControl(10000).setPosition(255, old_div(720 - height, 2))
            self.setFocusId(30000)

        def onClick(self, control):
            if control in [10010]:
                self.close()

            elif control in [10009]:
                if self.user: self.result['user'] = self.getControl(10003).getText()
                if self.email: self.result['email'] = self.getControl(10004).getText()
                if self.password: self.result['password'] = self.getControl(10005).getText()
                if self.captcha_img: self.result['captcha'] = self.getControl(10006).getText()
                self.close()

    dialog = Register('Register.xml', config.get_runtime_path()).Start(heading, user, email, password, user_default, email_default, password_default, captcha_img)
    return dialog


def dialog_info(item, scraper):
    class TitleOrIDWindow(xbmcgui.WindowXMLDialog):
        def Start(self, item, scraper):
            self.item = item
            self.item.exit = False
            self.title = item.show if item.show else item.fulltitle
            self.id = item.infoLabels.get('tmdb_id', '') if scraper == 'tmdb' else item.infoLabels.get('tvdb_id', '')
            self.scraper = scraper
            self.idtitle = 'TMDB ID' if scraper == 'tmdb' else 'TVDB ID'
            self.doModal()
            return self.item

        def onInit(self):
            #### Kodi 18 compatibility ####
            if config.get_platform(True)['num_version'] < 18:
                self.setCoordinateResolution(2)
            self.HEADER = self.getControl(100)
            self.TITLE = self.getControl(101)
            self.ID = self.getControl(102)
            self.EXIT = self.getControl(103)
            self.EXIT2 = self.getControl(104)

            self.HEADER.setText(config.get_localized_string(60228) % self.title)
            self.TITLE.setLabel('[UPPERCASE]' + config.get_localized_string(60230).replace(':','') + '[/UPPERCASE]')
            self.ID.setLabel(self.idtitle)
            self.setFocusId(101)

        def onClick(self, control):
            if control in [101]:
                result = dialog_input(self.title)
                if result:
                    if self.item.contentType == 'movie': self.item.contentTitle = result
                    else: self.item.contentSerieName = result
                    self.close()
            elif control in [102]:
                result = dialog_numeric(0, self.idtitle, self.id)
                if result:
                    if self.scraper == 'tmdb': self.item.infoLabels['tmdb_id'] = result
                    elif self.scraper == 'tvdb': self.item.infoLabels['tvdb_id'] = result
                    self.close()

            elif control in [103, 104]:
                self.item.exit = True
                self.close()

        def onAction(self, action):
            action = action.getId()
            if action in [92, 10]:
                self.item.exit = True
                self.close()

    dialog = TitleOrIDWindow('TitleOrIDWindow.xml', config.get_runtime_path()).Start(item, scraper)
    return dialog


def dialog_select_group(heading, _list, preselect=0):
    class SelectGroup(xbmcgui.WindowXMLDialog):
        def start(self, heading, _list, preselect):
            self.selected = preselect
            self.heading = heading
            self.list = _list
            self.doModal()

            return self.selected

        def onInit(self):
            self.getControl(1).setText(self.heading)
            itemlist = []
            for n, it in enumerate(self.list):
                logger.debug(it)
                item = xbmcgui.ListItem(str(n))
                item.setProperty('title', it[0])
                item.setProperty('seasons', str(it[1]))
                item.setProperty('episodes', str(it[2]))
                item.setProperty('description', '\n' + it[3])
                item.setProperty('thumb', it[4])
                itemlist.append(item)

            self.getControl(2).addItems(itemlist)
            self.setFocusId(2)
            self.getControl(2).selectItem(self.selected)

        def onClick(self, control):
            if control in [100]:
                self.selected = -1
                self.close()
            elif control in [2]:
                self.selected = self.getControl(2).getSelectedPosition()
                self.close()

        def onAction(self, action):
            action = action.getId()
            if action in [10, 92]:
                self.selected = -1
                self.close()

    dialog = SelectGroup('SelectGroup.xml', config.get_runtime_path()).start(heading, _list, preselect)
    return dialog


def itemlist_refresh():
    # pos = Item().fromurl(xbmc.getInfoLabel('ListItem.FileNameAndPath')).itemlistPosition
    # logger.info('Current position: ' + str(pos))
    xbmc.executebuiltin("Container.Refresh")

    # while Item().fromurl(xbmc.getInfoLabel('ListItem.FileNameAndPath')).itemlistPosition != pos:
    #     win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    #     cid = win.getFocusId()
    #     ctl = win.getControl(cid)
    #     ctl.selectItem(pos)


def itemlist_update(item, replace=False):
    if replace:  # reset the path history
        xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ", replace)")
    else:
        xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ")")


def get_window():
    """
    Return if addon is used as widget
    For doing so, it check current window ID (https://kodi.wiki/view/Window_IDs)
    """
    winId = xbmcgui.getCurrentWindowId()
    if winId == 9999:
        return 'WINDOW_INVALID'
    elif winId == 10000:
        return 'WINDOW_HOME'
    elif winId == 10001:
        return 'WINDOW_PROGRAMS'
    elif winId == 10002:
        return 'WINDOW_PICTURES'
    elif winId == 10003:
        return 'WINDOW_FILES'
    elif winId == 10004:
        return 'WINDOW_SETTINGS_MENU'
    elif winId == 10007:
        return 'WINDOW_SYSTEM_INFORMATION'
    elif winId == 10011:
        return 'WINDOW_SCREEN_CALIBRATION'

    elif winId == 10016:
        return 'WINDOW_SETTINGS_START'
    elif winId == 10016:
        return 'WINDOW_SETTINGS_SYSTEM'
    elif winId == 10018:
        return 'WINDOW_SETTINGS_SERVICE'

    elif winId == 10021:
        return 'WINDOW_SETTINGS_MYPVR'
    elif winId == 10022:
        return 'WINDOW_SETTINGS_MYGAMES'

    elif winId == 10025:
        return 'WINDOW_VIDEO_NAV'
    elif winId == 10028:
        return 'WINDOW_VIDEO_PLAYLIST'

    elif winId == 10029:
        return 'WINDOW_LOGIN_SCREEN'

    elif winId == 10030:
        return 'WINDOW_SETTINGS_PLAYER'
    elif winId == 10031:
        return 'WINDOW_SETTINGS_MEDIA'
    elif winId == 10032:
        return 'WINDOW_SETTINGS_INTERFACE'

    elif winId == 10034:
        return 'WINDOW_SETTINGS_PROFILES'
    elif winId == 10035:
        return 'WINDOW_SKIN_SETTINGS'

    elif winId == 10040:
        return 'WINDOW_ADDON_BROWSER'

    elif winId == 10050:
        return 'WINDOW_EVENT_LOG'

    elif winId == 97:
        return 'WINDOW_SCREENSAVER_DIM'
    elif winId == 98:
        return 'WINDOW_DEBUG_INFO'
    elif winId == 10099:
        return 'WINDOW_DIALOG_POINTER'
    elif winId == 10100:
        return 'WINDOW_DIALOG_YES_NO'
    elif winId == 10101:
        return 'WINDOW_DIALOG_PROGRESS'
    elif winId == 10103:
        return 'WINDOW_DIALOG_KEYBOARD'
    elif winId == 10104:
        return 'WINDOW_DIALOG_VOLUME_BAR'
    elif winId == 10105:
        return 'WINDOW_DIALOG_SUB_MENU'
    elif winId == 10106:
        return 'WINDOW_DIALOG_CONTEXT_MENU'
    elif winId == 10107:
        return 'WINDOW_DIALOG_KAI_TOAST'
    elif winId == 10109:
        return 'WINDOW_DIALOG_NUMERIC'
    elif winId == 10110:
        return 'WINDOW_DIALOG_GAMEPAD'
    elif winId == 10111:
        return 'WINDOW_DIALOG_BUTTON_MENU'
    elif winId == 10114:
        return 'WINDOW_DIALOG_PLAYER_CONTROLS'
    elif winId == 10115:
        return 'WINDOW_DIALOG_SEEK_BAR'
    elif winId == 10116:
        return 'WINDOW_DIALOG_PLAYER_PROCESS_INFO'
    elif winId == 10120:
        return 'WINDOW_DIALOG_MUSIC_OSD'
    elif winId == 10121:
        return 'WINDOW_DIALOG_VIS_SETTINGS'
    elif winId == 10122:
        return 'WINDOW_DIALOG_VIS_PRESET_LIST'
    elif winId == 10123:
        return 'WINDOW_DIALOG_VIDEO_OSD_SETTINGS'
    elif winId == 10124:
        return 'WINDOW_DIALOG_AUDIO_OSD_SETTINGS'
    elif winId == 10125:
        return 'WINDOW_DIALOG_VIDEO_BOOKMARKS'
    elif winId == 10126:
        return 'WINDOW_DIALOG_FILE_BROWSER'
    elif winId == 10128:
        return 'WINDOW_DIALOG_NETWORK_SETUP'
    elif winId == 10129:
        return 'WINDOW_DIALOG_MEDIA_SOURCE'
    elif winId == 10130:
        return 'WINDOW_DIALOG_PROFILE_SETTINGS'
    elif winId == 10131:
        return 'WINDOW_DIALOG_LOCK_SETTINGS'
    elif winId == 10132:
        return 'WINDOW_DIALOG_CONTENT_SETTINGS'
    elif winId == 10133:
        return 'WINDOW_DIALOG_LIBEXPORT_SETTINGS'
    elif winId == 10134:
        return 'WINDOW_DIALOG_FAVOURITES'
    elif winId == 10135:
        return 'WINDOW_DIALOG_SONG_INFO'
    elif winId == 10136:
        return 'WINDOW_DIALOG_SMART_PLAYLIST_EDITOR'
    elif winId == 10137:
        return 'WINDOW_DIALOG_SMART_PLAYLIST_RULE'
    elif winId == 10138:
        return 'WINDOW_DIALOG_BUSY'
    elif winId == 10139:
        return 'WINDOW_DIALOG_PICTURE_INFO'
    elif winId == 10140:
        return 'WINDOW_DIALOG_ADDON_SETTINGS'
    elif winId == 10142:
        return 'WINDOW_DIALOG_FULLSCREEN_INFO'
    elif winId == 10145:
        return 'WINDOW_DIALOG_SLIDER'
    elif winId == 10146:
        return 'WINDOW_DIALOG_ADDON_INFO'
    elif winId == 10147:
        return 'WINDOW_DIALOG_TEXT_VIEWER'
    elif winId == 10148:
        return 'WINDOW_DIALOG_PLAY_EJECT'
    elif winId == 10149:
        return 'WINDOW_DIALOG_PERIPHERALS'
    elif winId == 10150:
        return 'WINDOW_DIALOG_PERIPHERAL_SETTINGS'
    elif winId == 10151:
        return 'WINDOW_DIALOG_EXT_PROGRESS'
    elif winId == 10152:
        return 'WINDOW_DIALOG_MEDIA_FILTER'
    elif winId == 10153:
        return 'WINDOW_DIALOG_SUBTITLES'
    elif winId == 10156:
        return 'WINDOW_DIALOG_KEYBOARD_TOUCH'
    elif winId == 10157:
        return 'WINDOW_DIALOG_CMS_OSD_SETTINGS'
    elif winId == 10158:
        return 'WINDOW_DIALOG_INFOPROVIDER_SETTINGS'
    elif winId == 10159:
        return 'WINDOW_DIALOG_SUBTITLE_OSD_SETTINGS'
    elif winId == 10160:
        return 'WINDOW_DIALOG_BUSY_NOCANCEL'

    elif winId == 10500:
        return 'WINDOW_MUSIC_PLAYLIST'
    elif winId == 10502:
        return 'WINDOW_MUSIC_NAV'
    elif winId == 10503:
        return 'WINDOW_MUSIC_PLAYLIST_EDITOR'

    elif winId == 10550:
        return 'WINDOW_DIALOG_OSD_TELETEXT'

    # PVR related Window and Dialog ID's

    elif 10600 < winId < 10613:
        return 'WINDOW_DIALOG_PVR'


    elif 10700 < winId < 10711:
        return 'WINDOW_PVR_ID'

    # virtual windows for PVR specific keymap bindings in fullscreen playback
    elif winId == 10800:
        return 'WINDOW_FULLSCREEN_LIVETV'
    elif winId == 10801:
        return 'WINDOW_FULLSCREEN_RADIO'
    elif winId == 10802:
        return 'WINDOW_FULLSCREEN_LIVETV_PREVIEW'
    elif winId == 10803:
        return 'WINDOW_FULLSCREEN_RADIO_PREVIEW'
    elif winId == 10804:
        return 'WINDOW_FULLSCREEN_LIVETV_INPUT'
    elif winId == 10805:
        return 'WINDOW_FULLSCREEN_RADIO_INPUT'

    elif winId == 10820:
        return 'WINDOW_DIALOG_GAME_CONTROLLERS'
    elif winId == 10821:
        return 'WINDOW_GAMES'
    elif winId == 10822:
        return 'WINDOW_DIALOG_GAME_OSD'
    elif winId == 10823:
        return 'WINDOW_DIALOG_GAME_VIDEO_FILTER'
    elif winId == 10824:
        return 'WINDOW_DIALOG_GAME_STRETCH_MODE'
    elif winId == 10825:
        return 'WINDOW_DIALOG_GAME_VOLUME'
    elif winId == 10826:
        return 'WINDOW_DIALOG_GAME_ADVANCED_SETTINGS'
    elif winId == 10827:
        return 'WINDOW_DIALOG_GAME_VIDEO_ROTATION'
    elif 11100 < winId < 11199:
        return 'SKIN'  # WINDOW_ID's from 11100 to 11199 reserved for Skins

    elif winId == 12000:
        return 'WINDOW_DIALOG_SELECT'
    elif winId == 12001:
        return 'WINDOW_DIALOG_MUSIC_INFO'
    elif winId == 12002:
        return 'WINDOW_DIALOG_OK'
    elif winId == 12003:
        return 'WINDOW_DIALOG_VIDEO_INFO'
    elif winId == 12005:
        return 'WINDOW_FULLSCREEN_VIDEO'
    elif winId == 12006:
        return 'WINDOW_VISUALISATION'
    elif winId == 12007:
        return 'WINDOW_SLIDESHOW'
    elif winId == 12600:
        return 'WINDOW_WEATHER'
    elif winId == 12900:
        return 'WINDOW_SCREENSAVER'
    elif winId == 12901:
        return 'WINDOW_DIALOG_VIDEO_OSD'

    elif winId == 12902:
        return 'WINDOW_VIDEO_MENU'
    elif winId == 12905:
        return 'WINDOW_VIDEO_TIME_SEEK'  # virtual window for time seeking during fullscreen video

    elif winId == 12906:
        return 'WINDOW_FULLSCREEN_GAME'

    elif winId == 12997:
        return 'WINDOW_SPLASH'  # splash window
    elif winId == 12998:
        return 'WINDOW_START'  # first window to load
    elif winId == 12999:
        return 'WINDOW_STARTUP_ANIM'  # for startup animations

    elif 13000 < winId < 13099:
        return 'PYTHON'  # WINDOW_ID's from 13000 to 13099 reserved for Python

    elif 14000 < winId < 14099:
        return 'ADDON'  # WINDOW_ID's from 14000 to 14099 reserved for Addons


def calcResolution(option):
    match = scrapertools.find_single_match(option, '([0-9]{2,4})(?:p|i|x[0-9]{2,4}|)')
    resolution = 0

    if match:
        resolution = int(match)
    elif 'sd' in option.lower():
        resolution = 480
    elif 'hd' in option.lower():
        resolution = 720
        if 'full' in option.lower():
            resolution = 1080
    elif '2k' in option.lower():
        resolution = 1440
    elif '4k' in option.lower():
        resolution = 2160
    elif 'auto' in option.lower():
        resolution = 10000

    return resolution

