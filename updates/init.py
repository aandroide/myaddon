
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs, os,sys

import time
import downloader

from platformcode import logger,config,platformtools,filetools


from updates import file_helper,utills

AUTHOR='aandroide'
REPO='myaddon'
BRANCH='test'
ADDON_ID='plugin.video.lo-scienziato-pazzo'
CHECK_FOR_UPDATE_TITLE="Checking for update"
destpathname = xbmc.translatePath("special://home/addons/")
ADDON_DIR = filetools.join(destpathname, f"{ADDON_ID}")
trackingFile = "last_commit.txt"

def get_last_commit(dp):
    url='https://api.github.com/repos/'+AUTHOR+'/'+REPO+'/branches/'+BRANCH
    try:
        data=utills.open_link_json(url)
        sha= data['commit']['sha']
        message= data['commit']['commit']['message']
        return sha,message
    except Exception as ex:
        logger.log("error when check for updates")
        dp.close()
        platformtools.dialog_ok(CHECK_FOR_UPDATE_TITLE,"Error hapen when check for updates\n(may be connection or github not avilable now)")
        return None

def updateLastCommit(sha,message,addonDir=ADDON_DIR):
    localCommitFile = file_helper.fOpen(os.path.join(addonDir, trackingFile), 'wb')
    localCommitFile.write(str(sha+'\n').encode('utf-8'))
    localCommitFile.write(str(message).encode('utf-8'))
    localCommitFile.close()

def getSavedCommit(addonDir=ADDON_DIR):
    sha="???"
    message=""    

    try:
        track=  file_helper.fOpen(os.path.join(addonDir, trackingFile), 'r')
        sha= track.readline()
        message= track.readline()
    except Exception as ex:
        logger.log("ERROR in read commit")

    try:sha= sha.decode('utf-8')
    except:pass    
    
    try:message= message.decode('utf-8')
    except:pass    

    sha=sha.strip()
    message=message.strip()

    if sha=="": sha="???"
    return sha,message    

def refreshLang():
    from platformcode import config
    language = config.get_language()
    if language == 'eng':
        xbmc.executebuiltin("SetGUILanguage(resource.language.it_it)")
        xbmc.executebuiltin("SetGUILanguage(resource.language.en_en)")
    else:
        xbmc.executebuiltin("SetGUILanguage(resource.language.en_en)")
        xbmc.executebuiltin("SetGUILanguage(resource.language.it_it)")


def update(commitMessage):
    logger.log("STARTING UPDATE")
    dp=platformtools.dialog_progress("Updating","downloading....")
    # platform
    
    remotefilename = 'https://github.com/' + AUTHOR + "/" + REPO + "/archive/" + BRANCH + ".zip"
    localfilename = filetools.join(xbmc.translatePath("special://home/addons/"), f"{ADDON_ID}.update.zip")
    destpathname = xbmc.translatePath("special://home/addons/")
    extractedDir = filetools.join(destpathname, f"{REPO}-{BRANCH}")
    # addonDir = filetools.join(destpathname, f"fofa-{ADDON_ID}")
    
    
    try:
       os.remove(localfilename)
    except:
       pass
    downloader.download(remotefilename, localfilename, dp)
    # addonfolder = xbmcvfs.translatePath(os.path.join('special://','home'))
    time.sleep(2)
    xbmc.sleep(1000)
    
    dp.update(int(0),"\n installing...")
    hash = file_helper.extractZipFile(localfilename,destpathname,dp)
    

    dp.update(int(0),"\n finishing...")
    
    # clear 
    if extractedDir!= ADDON_DIR:
        file_helper.removeTree(ADDON_DIR)
    
    xbmc.sleep(1000)
    dp.update(int(30))
    file_helper.rename(extractedDir,ADDON_DIR)
    
    dp.update(int(60))
    file_helper.remove(localfilename)
    
    dp.update(int(100))
    dp.close()



    updateLastCommit(sha=hash,message=commitMessage)
    platformtools.dialog_ok("Update Completed", 'Addon updated successfuly \n\n click ok to restart addon')
    #restart addon
    # xbmc.executebuiltin(f'RunScript(special://home/addons/{ADDON_ID}/service.py)')
    xbmc.executebuiltin("UpdateLocalAddons")
    # xbmc.executebuiltin('Addon.Stop(' + ADDON_ID+ ')')
    xbmc.sleep(10)
    refreshLang()
    xbmc.executebuiltin('Addon.Stop(' + ADDON_ID+ ')')
    xbmc.executebuiltin('RunAddon(' + ADDON_ID + ')')
    
    # xbmc.executebuiltin(f'RunScript(special://home/addons/{ADDON_ID}/default.py)')
    # xbmc.executebuiltin('RunAddon(' + ADDON_ID + ')')

    

def run():
    logger.log("CHECK FOR UPDATES")
    dp=platformtools.dialog_progress(CHECK_FOR_UPDATE_TITLE,"Checking....")
    dp.update(30)
    last_sha,message=get_last_commit(dp)
    dp.update(70)
    cur_sha,cur_mesage=getSavedCommit()
    dp.close()
    
    cur_sha = str(cur_sha).replace('\n', '') 

    # cur_sha,cur_mes=getSavedCommit()
    # logger.log("FUCKER: ",'|'+cur_sha+'|')
    # logger.log("FUCKER: ",cur_mes)
    
    
    if last_sha ==None :
        return

    if cur_sha!=last_sha:
        update_ok=platformtools.dialog_yesno(CHECK_FOR_UPDATE_TITLE,"Thera are new version\nYou want to download it?")
        if update_ok:
            update(message)
    else :
        platformtools.dialog_ok(CHECK_FOR_UPDATE_TITLE,"addon are updated")