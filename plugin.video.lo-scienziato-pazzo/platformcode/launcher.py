# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC Launcher (xbmc / kodi)
# ------------------------------------------------------------

import sys, xbmc
#from core.item import Item
from platformcode import filetools
from platformcode import config, logger, platformtools
from platformcode.logger import WebErrorException


def start():
    '''
    First function that is executed when entering the plugin.
    Within this function all calls should go to
    functions that we want to execute as soon as we open the plugin.
    '''
    logger.debug()

    if not config.dev_mode():
        try:
            with open(config.changelogFile, 'r') as fileC:
                changelog = fileC.read()
                if changelog.strip() and config.get_setting("addon_update_message"):
                    platformtools.dialog_ok('Lo scenziato pazzo', 'Aggiornamenti applicati:\n' + changelog)
            #filetools.remove(config.changelogFile)
        except:
            pass
