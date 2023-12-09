# -*- coding: utf-8 -*-
import io
import os
import shutil
from lib.six import BytesIO

from platformcode import config, logger, platformtools, filetools
import json
import xbmc
import re
from lib import githash
try:
    import urllib.request as urllib
except ImportError:
    import urllib
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
addon = config.__settings__
addonname = addon.getAddonInfo('name')

_hdr_pat = re.compile("^@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@.*")

branch = 'test'
user = 'aandroide'
repo = 'myaddon'
addonDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
addonsDir =addonDir #os.path.dirname(addonDir)
maxPage = 5  # le api restituiscono 30 commit per volta, quindi se si è rimasti troppo indietro c'è bisogno di andare avanti con le pagine
trackingFile = "last_commit.txt"


def loadCommits(page=1):
    apiLink = 'https://api.github.com/repos/' + user + '/' + repo + '/commits?sha=' + branch + "&page=" + str(page)
    logger.info(apiLink)
    # riprova ogni secondo finchè non riesce (ad esempio per mancanza di connessione)
    for n in range(10):
        logger.info(f"try {n}")
        try:
            commitsLink = urllib.urlopen(apiLink).read()
            ret = json.loads(commitsLink)
            break
        except Exception as e:
            logger.exception(e, f"exception in try {n}")
            xbmc.sleep(1000)
    else:
        platformtools.dialog_notification(addonname, config.get_localized_string(70675))
        ret = None

    return ret


# ret -> aggiornato, necessita reload service
def check(background=False):
    from lib import patch
    if not config.get_setting('addon_update_enabled', default=True):
        return False, False
    logger.info('Cerco aggiornamenti...')
    commits = loadCommits()
    #logger.info(f'Commits trovati: {commits}') ##If you don't need to debug, comment out this, as it has lenghty output
    if not commits:
        return False, False

    try:
        localCommitFile = open(os.path.join(addonDir, trackingFile), 'r+')
    except:
        calcCurrHash()
        localCommitFile = open(os.path.join(addonDir, trackingFile), 'r+')
    localCommitSha = localCommitFile.readline()
    localCommitSha = localCommitSha.replace('\n', '') # da testare
    logger.info('Commit locale: ' + localCommitSha)
    updated = False
    serviceChanged = False

    pos = None
    for n, c in enumerate(commits):
        if c['sha'] == localCommitSha:
            pos = n
            break
    else:
        # evitiamo che dia errore perchè il file è già in uso
        #shas =
        logger.info(f"Evitiamo erroes: {len(commits)} commits: {localCommitSha}, en los commits {[comm['sha'] for comm in commits]}")
        localCommitFile.close()
        calcCurrHash()
        return True, False
    logger.info(f"Pos: {pos} de {len(commits)} commits")

    if pos > 0:
        changelog = ''
        poFilesChanged = False
        try:
            for c in reversed(commits[:pos]):
                commit = urllib.urlopen(c['url']).read()
                commitJson = json.loads(commit)
                # evitiamo di applicare i merge commit
                if 'Merge' in commitJson['commit']['message']:
                    continue
                logger.info(f"aggiornando a {commitJson['sha']} il directorio {addonDir}")

                # major update
                if len(commitJson['files']) > 50:
                    localCommitFile.close()
                    c['sha'] = updateFromZip(f"Aggiornamento in corso a commit {c['sha']}...")
                    localCommitFile = open(os.path.join(xbmc.translatePath("special://home/addons/"), 'plugin.video.lo-scienziato-pazzo', trackingFile), 'w')  # il file di tracking viene eliminato, lo ricreo
                    logger.info(f"sfolders {localCommitFile} {addonDir}")

                    changelog += commitJson['commit']['message'] + "\n"
                    poFilesChanged = True
                    serviceChanged = True
                    break

                patch_url = commitJson['html_url'] + '.patch'
                pafu = patch.fromurl(patch_url)
                logger.info(f"applicando {patch_url}, patch {pafu}")
                patchOk = pafu.apply(root=addonDir)

                for file in commitJson['files']:
                    if file["filename"] == trackingFile:  # il file di tracking non si modifica
                        continue
                    else:
                        logger.info(f"extraendo {file['filename']} sobre {addonsDir}, antes {addonDir}")
                        if 'resources/language' in file["filename"]:
                            poFilesChanged = True
                        if 'service.py' in file["filename"]:
                            serviceChanged = True
                        if (file['status'] == 'modified' and 'patch' not in file) or file['status'] == 'added' or (file['status'] == 'modified' and not patchOk):
                            # è un file NON testuale che è stato modificato, oppure è un file nuovo (la libreria non supporta la creazione di un nuovo file)
                            # lo devo scaricare
                            filename = os.path.join(addonsDir, file['filename'])
                            dirname = os.path.dirname(filename)
                            if not (filetools.isfile(os.path.join(addonsDir, file['filename'])) and getSha(filename) == file['sha']):
                                logger.info('scaricando ' + file['raw_url'])
                                if not os.path.exists(dirname):
                                    os.makedirs(dirname)
                                urllib.urlretrieve(file['raw_url'], filename)
                        elif file['status'] == 'removed':
                            remove(os.path.join(addonsDir, file["filename"]))
                        elif file['status'] == 'renamed':
                            # se non è già applicato
                            if not (filetools.isfile(os.path.join(addonsDir, file['filename'])) and getSha(os.path.join(addonsDir, file['filename'])) == file['sha']):
                                dirs = file['filename'].split('/')
                                partialdir = addonsDir
                                for d in dirs[:-1]:
                                    if not filetools.isdir(os.path.join(partialdir, d)):
                                        filetools.mkdir(os.path.join(partialdir, d))
                                    partialdir = os.path.join(partialdir, d)
                                filetools.move(os.path.join(addonsDir, file['previous_filename']), os.path.join(addonsDir, file['filename']))
                changelog += commitJson['commit']['message'] + "\n"
        except:
            import traceback
            logger.error("Error in check")
            logger.error(traceback.format_exc())
            # fallback
            localCommitFile.close()
            c['sha'] = updateFromZip('Aggiornamento in corso...')
            logger.error("New commit sha: " + c['sha'])
            localCommitFile = open(
                os.path.join(xbmc.translatePath("special://home/addons/"), 'plugin.video.lo-scienziato-pazzo', trackingFile),
                'w')  # il file di tracking viene eliminato, lo ricreo

        localCommitFile.seek(0)
        localCommitFile.truncate()
        logger.info(f"Aggiornato: Ultimo commit {c}")
        localCommitFile.writelines(c['sha'])
        localCommitFile.close()
        xbmc.executebuiltin("UpdateLocalAddons")
        if poFilesChanged:
            xbmc.sleep(1000)
            refreshLang()
            xbmc.sleep(1000)
        updated = True
        xbmc.executebuiltin("UpdateLocalAddons")
        xbmc.executebuiltin("StopScript(plugin.video.lo-scienziato-pazzo)")
        xbmc.executebuiltin("RunAddon(plugin.video.lo-scienziato-pazzo)")

        if config.get_setting("addon_update_message", default=True):
            if background:
                #notification = config.get_localized_string(80040)
                #xbmc.executebuiltin("UpdateLocalAddons")
                #notification = "Commits received: %s"
                platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80040) % commits[0]['sha'][:7], time=3000, sound=False)
                #platformtools.dialog_notification(config.get_localized_string(20000), notification % (commits[0]['sha'][:7],), time=3000, sound=False)
                platformtools.dialog_ok('Lo Scienziato Pazzo', 'Aggiornamenti applicati:\n' + changelog)
                try:
                    with open(config.changelogFile, 'a+') as fileC:
                        fileC.write(changelog)
                except:
                    import traceback
                    logger.error(traceback.format_exc())
            elif changelog:
                #changelog = config.get_changelog_text()
                platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(80041) + changelog)
                
    else:
        logger.info('Nessun nuovo aggiornamento')

    return updated, serviceChanged


def calcCurrHash():
    treeHash = githash.tree_hash(addonDir).hexdigest()
    logger.info('tree hash: ' + treeHash)
    commits = loadCommits()
    lastCommitSha = commits[0]['sha']
    page = 1
    while commits and page <= maxPage:
        found = False
        for n, c in enumerate(commits):
             if c['commit']['tree']['sha'] == treeHash:
                localCommitFile = open(os.path.join(addonDir, trackingFile), 'w')
                localCommitFile.write(c['sha'])
                localCommitFile.close()
                found = True
                break
        else:
            page += 1
            commits = loadCommits(page)

        if found:
            break
    else:
        logger.info('Non sono riuscito a trovare il commit attuale, scarico lo zip')
        hash = updateFromZip()
        # se ha scaricato lo zip si trova di sicuro all'ultimo commit
        localCommitFile = open(os.path.join(xbmc.translatePath("special://home/addons/"), 'plugin.video.lo-scienziato-pazzo', trackingFile), 'w')
        localCommitFile.write(hash if hash else lastCommitSha)
        localCommitFile.close()


def getSha(path):
    try:
        f = io.open(path, 'rb', encoding="utf8")
    except:
        return ''
    size = len(f.read())
    f.seek(0)
    return githash.blob_hash(f, size).hexdigest()


def getShaStr(str):
    if PY3:
        return githash.blob_hash(BytesIO(str.encode('utf-8')), len(str.encode('utf-8'))).hexdigest()
    else:
        return githash.blob_hash(BytesIO(str), len(str)).hexdigest()



def updateFromZip(message=config.get_localized_string(80050)):
    logger.info(f'Aggiornamento da zip: {message}')
    dp = platformtools.dialog_progress_bg(config.get_localized_string(20000), message)
    dp.update(0)

    remotefilename = 'https://github.com/' + user + "/" + repo + "/archive/" + branch + ".zip"
    localfilename = filetools.join(xbmc.translatePath("special://home/addons/"), "plugin.video.lo-scienziato-pazzo.update.zip")
    destpathname = xbmc.translatePath("special://home/addons/")
    extractedDir = filetools.join(destpathname, f"addon-{branch}-plugin.video.lo-scienziato-pazzo")
    
    logger.info("remotefilename=%s" % remotefilename)
    logger.info("localfilename=%s" % localfilename)
    logger.info('extract dir: ' + extractedDir)

    # pulizia preliminare
    remove(localfilename)
    removeTree(extractedDir)

    try:
        urllib.urlretrieve(remotefilename, localfilename,
                           lambda nb, bs, fs, url=remotefilename: _pbhook(nb, bs, fs, url, dp))
    except Exception as e:
        platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(80031))
        logger.info('Non sono riuscito a scaricare il file zip')
        logger.info(e)
        dp.close()
        return False

    # Lo descomprime
    logger.info("decompressione...")
    logger.info("destpathname=%s" % destpathname)

    if os.path.isfile(localfilename):
        logger.info(f'il file esiste {localfilename}')

    dp.update(80, config.get_localized_string(20000) + '\n' + config.get_localized_string(80032))

    import zipfile
    try:
        hash = fixZipGetHash(localfilename)
        logger.info("hash: %s", hash)

        with zipfile.ZipFile(filetools.file_open(localfilename, 'rb', vfs=False)) as zip:
            logger.info(f"extracting zip: {localfilename} to {extractedDir}")
            size = sum([zinfo.file_size for zinfo in zip.filelist])
            cur_size = 0
            for member in zip.infolist():
                zip.extract(member, extractedDir)
                cur_size += member.file_size
                dp.update(int(80 + cur_size * 15 / size))
            logger.info(f"extracted zip: {localfilename} to {extractedDir}")

    except Exception as e:
        logger.info('Non sono riuscito ad estrarre il file zip')
        logger.error(e)
        import traceback
        logger.error(traceback.print_exc())
        dp.close()
        #remove(localfilename)

        return False

    dp.update(95)
    logger.info("finalizado zip: %s hacia %s, %s"%(localfilename, destpathname, extractedDir))

    # rename addon.xml
    lwd = os.listdir(os.path.join(extractedDir, f"{repo}-{branch}"))
    logger.info(f"lwd: {lwd}")
    # addon_xml = os.path.join(extractedDir, f"{repo}-{branch}",  'addon.xml')
    #final_addon_xml = os.path.join(extractedDir, f"{repo}-{branch}", 'addon_subsequent.xml')
    #logger.info(f"Personalizing addon.xml: {os.path.exists(addon_xml)} - {os.path.exists(final_addon_xml)} ({addon_xml} to {final_addon_xml})")
    # if os.path.exists(addon_xml):
    #     remove(addon_xml)
    #fr = filetools.rename(final_addon_xml, addon_xml, silent=False, vfs=False)
    #logger.info(f"Personalized addon.xml: {fr}")
    #if not fr:
    #    assert 0, f"Error renaming {final_addon_xml} to {addon_xml}"

    #return
    # puliamo tutto
    global addonDir
    old_addonDir = addonDir
    addonDir = os.path.join(destpathname, 'plugin.video.lo-scienziato-pazzo')
    addonsDir = os.path.dirname(addonDir)
    logger.info(f"addonDir updated from {old_addonDir} to {addonDir}")

    extracted_subdir = os.path.join(extractedDir, "myaddon-" + branch, 'plugin.video.lo-scienziato-pazzo')
    if not os.path.exists(extracted_subdir):
        #I don't know what the hell happened with the folder name
        ld = os.listdir(extractedDir)
        logger.info(f"Folders under {extractedDir}: {ld}, caspita!")
        extracted_subdir = os.path.join(extractedDir, ld[-1])
    if os.path.exists(extracted_subdir):
        if extractedDir != addonDir:
            logger.info(f"Removing addon dir {addonDir}")
            removeTree(addonDir)
        xbmc.sleep(1000)
        logger.info(f"rinominazione from {extracted_subdir} to {addonDir} (from {destpathname}))")
        renameres = rename(extracted_subdir, addonDir)
        removeTree(extractedDir)
    else:
        logger.info(f"folder {extracted_subdir} inexistent!: {extractedDir}->({os.path.exists(extractedDir)}")
    logger.info("Cancellando il file zip...")
    remove(localfilename)

    dp.update(100)
    xbmc.sleep(1000)
    dp.close()
    if message != config.get_localized_string(80050):
        xbmc.executebuiltin("UpdateLocalAddons")
        xbmc.executebuiltin("StopScript(plugin.video.lo-scienziato-pazzo)")
        xbmc.executebuiltin("RunAddon(plugin.video.lo-scienziato-pazzo)")
        refreshLang()

    logger.info("hsh: %s, lf %s", hash, localfilename)

    return hash


def refreshLang():
    from platformcode import config
    language = config.get_language()
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


def onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

def removeTree(dir):
    if os.path.isdir(dir):
        try:
            shutil.rmtree(dir, ignore_errors=False, onerror=onerror)
        except Exception as e:
            logger.info('Cartella ' + dir + ' NON eliminata')
            logger.error(e)


def rename(dir1, dir2):
    try:
        filetools.rename(dir1, dir2, silent=True, vfs=False)
    except:
        logger.exception('cartella ' + dir1 + ' NON rinominata')


# https://stackoverflow.com/questions/3083235/unzipping-file-results-in-badzipfile-file-is-not-a-zip-file
def fixZipGetHash(zipFile):
    hash = ''
    with filetools.file_open(zipFile, 'r+b', vfs=False) as f:
        data = f.read()
        pos = data.find(b'\x50\x4b\x05\x06')  # End of central directory signature
        if pos > 0:
            f.seek(pos + 20)  # +20: see secion V.I in 'ZIP format' link above.
            hash = f.read()[2:]
            f.seek(pos + 20)
            f.truncate()
            f.write(
                b'\x00\x00')  # Zip file comment length: 0 byte length; tell zip applications to stop reading.

    return hash.decode('utf-8')


def _pbhook(numblocks, blocksize, filesize, url, dp):
    try:
        percent = min((numblocks*blocksize*80)/filesize, 80)
        dp.update(int(percent))
    except Exception as e:
        logger.error(e)
        percent = 80
        dp.update(percent)
