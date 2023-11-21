# -*- coding: utf-8 -*-
import os
import sys
import threading
import traceback
import xbmc

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit
# on kodi 18 its xbmc.translatePath, on 19 xbmcvfs.translatePath
try:
    import xbmcvfs
    xbmc.translatePath = xbmcvfs.translatePath
except:
    pass
from platformcode import config
librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)
os.environ['TMPDIR'] = config.get_temp_file('')

#from core import db
from lib import schedule
from platformcode import logger, updater

# if this service need to be reloaded because an update changed it
needsReload = False
# list of threads
threads = []






def updaterCheck():
    global needsReload
    # updater check
    updated, needsReload = updater.check(background=True)



def run_threaded(job_func, args):
    job_thread = threading.Thread(target=job_func, args=args)
    job_thread.start()
    threads.append(job_thread)


def join_threads():
    logger.debug(threads)
    for th in threads:
        try:
            th.join()
        except:
            logger.error(traceback.format_exc())


class AddonMonitor(xbmc.Monitor):
    def __init__(self):
        self.updaterPeriod = None
        self.update_setting = None
        self.update_hour = None
        self.scheduleUpdater()

        super(AddonMonitor, self).__init__()



    def scheduleUpdater(self):
        if not config.dev_mode():
            updaterCheck()
            self.updaterPeriod = config.get_setting('addon_update_timer', default=1)
            schedule.every(self.updaterPeriod).hours.do(updaterCheck).tag('updater')
            logger.debug('scheduled updater every ' + str(self.updaterPeriod) + ' hours')



if __name__ == "__main__":
    logger.info('Starting Lo Scienziato Pazzo service')


    if config.get_setting('autostart'):
        xbmc.executebuiltin('RunAddon(plugin.video.' + config.PLUGIN_NAME + ')')

    # check if the user has any connection problems
    #from platformcode.checkhost import test_conn
    #run_threaded(test_conn, (True, not config.get_setting('resolver_dns'), True, [], [], True))

    monitor = AddonMonitor()

    while True:
        try:
            schedule.run_pending()
        except:
            logger.error(traceback.format_exc())

        if needsReload:
            join_threads()
            #db.close()
            logger.info('Relaunching service.py')
            xbmc.executeJSONRPC(
                '{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "plugin.video.lo-scienziato-pazzo", "enabled": false }}')
            xbmc.executeJSONRPC(
                '{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "plugin.video.lo-scienziato-pazzo", "enabled": true }}')
            logger.debug(threading.enumerate())
            break

        if monitor.waitForAbort(1): # every second
            logger.debug('Lo Scienziato Pazzo service EXIT')
            # db need to be closed when not used, it will cause freezes
            join_threads()
            logger.debug('Close Threads')
            #db.close()
            #logger.debug('Close DB')
            break
    logger.debug('Lo Scienziato Pazzo service STOPPED')
