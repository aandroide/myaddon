# -*- coding: utf-8 -*-
import io
import xbmc, os, shutil, json
import xbmcaddon, subprocess, xbmcgui
# functions that on kodi 19 moved to xbmcvfs
try:
    import xbmcvfs
    xbmc.translatePath = xbmcvfs.translatePath
    xbmc.validatePath = xbmcvfs.validatePath
    xbmc.makeLegalFilename = xbmcvfs.makeLegalFilename
except:
    pass
from platformcode import platformtools, logger, filetools, config, updater
from threading import Thread
try:
    import urllib.request as urllib
except ImportError:
    import urllib

branch = 'master'
user = 'aandroide'
repo = 'myaddon'
addonDir = os.path.dirname(os.path.abspath(__file__)) + '/'
maxPage = 5  # le api restituiscono 30 commit per volta, quindi se si è rimasti troppo indietro c'è bisogno di andare avanti con le pagine
trackingFile = "last_commit.txt"


def chooseBranch():
    global branch
    apiLink = 'https://api.github.com/repos/' + user + '/' + repo + '/branches'
    try:
        branches = urllib.urlopen(apiLink).read()
    except Exception as e:
        logger.exception(e, "Error in chooseBranch")
        platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(80031))
        return False
    branches = json.loads(branches)
    xbmcaddon.Addon(id="plugin.video.lo-scienziato-pazzo").setSetting('language', 'it')
    chDesc = [config.get_localized_string(80034), config.get_localized_string(80035)]
    chDesc.extend([b['name'] for b in branches if b['name'] not in ['stable', 'master']])
    chName = ['stable', 'master', 'main']
    chName.extend([b['name'] for b in branches if b['name'] not in ['stable', 'master']])
    sel = platformtools.dialog_select(config.get_localized_string(80033), chDesc)
    if sel == -1:
        return False
    branch = chName[sel]
    return True




def refreshLang():
    language = config.get_localized_string(20001)
    if language == 'eng':
        xbmc.executebuiltin("SetGUILanguage(resource.language.it_it)")
        xbmc.executebuiltin("SetGUILanguage(resource.language.en_en)")
    else:
        xbmc.executebuiltin("SetGUILanguage(resource.language.en_en)")
        xbmc.executebuiltin("SetGUILanguage(resource.language.it_it)")


def remove(file):
    if os.path.isfile(file):
        try:
            os.remove(file)
        except:
            logger.info('File ' + file + ' NON eliminato')



def rename(dir1, dir2):
    try:
        filetools.rename(dir1, dir2, silent=True, vfs=False)
    except:
        logger.info('cartella ' + dir1 + ' NON rinominata')



def download():
    hash = updater.updateFromZip()
    # se ha scaricato lo zip si trova di sicuro all'ultimo commit
    localCommitFile = fOpen(os.path.join(addonDir, trackingFile), 'wb')
    localCommitFile.write(hash.encode('utf-8'))
    localCommitFile.close()

    if xbmc.getCondVisibility('system.platform.linux'):
        # performs instllation steps if in Linux
        sudo_password = platformtools.dialog_input(heading="Enter your sudo password")
        # dp = platformtools.dialog_progress_bg(config.get_localized_string(20000), message)
        dp = platformtools.dialog_progress_bg("Installing", "Install for Linux")
        dp.update(0)
        coproc = subprocess.run("rm -rf xbmc", shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, cwd=addonDir)
        logger.info(f"command 1 (rm -rf xbmc) outcome: {coproc}, stdout: {coproc.stdout}, stderr: {coproc.stderr}, retcode: {coproc.returncode}")
        dp.update(10)
        coproc2 = subprocess.run("git clone --branch master https://github.com/xbmc/xbmc.git", shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, cwd=addonDir)
        logger.info(f"command 2 (git clone --branch master https://github.com/xbmc/xbmc.git) outcome: {coproc2}, stdout: {coproc2.stdout}, stderr: {coproc2.stderr}, retcode: {coproc2.returncode}")
        dp.update(20)
        coproc3 = subprocess.run("git clone https://github.com/kodi-pvr/pvr.iptvsimple.git", shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, cwd=addonDir)
        logger.info(f"command 3 (git clone https://github.com/kodi-pvr/pvr.iptvsimple.git) outcome: {coproc3}, stdout: {coproc3.stdout}, stderr: {coproc3.stderr}, retcode: {coproc3.returncode}")
        dp.update(30)
        coproc4 = subprocess.run("mkdir build", shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, cwd=os.path.join(addonDir, 'pvr.iptvsimple'))
        logger.info(f"command 4 (mkdir build) outcome: {coproc4}, stdout: {coproc4.stdout}, stderr: {coproc4.stderr}, retcode: {coproc4.returncode}")
        dp.update(40)
        coproc5 = subprocess.run("cmake -DADDONS_TO_BUILD=pvr.iptvsimple -DADDON_SRC_PREFIX=../.. -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX=../../xbmc/addons -DPACKAGE_ZIP=1 ../../xbmc/cmake/addons", shell=True, input=sudo_password.encode('utf-8'), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, cwd=os.path.join(addonDir, 'pvr.iptvsimple', 'build'))
        logger.info(f"command 5 ('cmake -DADDONS_TO_BUILD=pvr.iptvsimple -DADDON_SRC_PREFIX=../.. -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX=../../xbmc/addons -DPACKAGE_ZIP=1 ../../xbmc/cmake/addons') outcome: {coproc5}, stdout: {coproc5.stdout}, stderr: {coproc5.stderr}, retcode: {coproc5.returncode}")
        dp.update(60)
        coproc6 = subprocess.run("sudo make", shell=True, input=sudo_password.encode('utf-8')+b'/n', stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, cwd=os.path.join(addonDir, 'pvr.iptvsimple', 'build'))
        dp.update(100)
        print("outputtest")
        logger.info(f"command 6 (sudo make) outcome: {coproc6}, stdout: {coproc6.stdout}, stderr: {coproc6.stderr}, retcode: {coproc6.returncode}")
        dp.close()
    else:
        logger.info(f'Not Linux, skipping installation steps')

def run():
    logger.info('Downloader service started')
    refreshLang()
    if bch:=chooseBranch():
        logger.info(f"Chosen branch: {bch}")
        t = Thread(target=download)
        t.start()

        if not config.get_setting('show_once'):
            config.set_setting('show_once', True)

        t.join()
        refreshLang()

        xbmc.executebuiltin("RunScript(special://home/addons/plugin.video.lo-scienziato-pazzo/service.py)")


def fOpen(file, mode = 'r'):
    # per android è necessario, su kodi 18, usare FileIO
    # https://forum.kodi.tv/showthread.php?tid=330124
    # per xbox invece, è necessario usare open perchè _io è rotto :(
    # https://github.com/jellyfin/jellyfin-kodi/issues/115#issuecomment-538811017
    if xbmc.getCondVisibility('system.platform.linux') and xbmc.getCondVisibility('system.platform.android'):
        logger.info('android, uso FileIO per leggere')
        return io.FileIO(file, mode)
    else:
        return open(file, mode)

if __name__ == "__main__":
    run()
