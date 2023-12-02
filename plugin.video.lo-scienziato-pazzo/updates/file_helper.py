import xbmc
import io,os,shutil
from platformcode import filetools,logger

def rename(dir1, dir2):
    try:
        filetools.rename(dir1, dir2, silent=True, vfs=False)
    except:
        logger.exception('cartella ' + dir1 + ' NON rinominata')

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

def move(src,dist):
    if os.path.isdir(src):
        try:
            shutil.move(src,dist)
        except Exception as e:
            logger.info('Cartella ' + dir + ' NON eliminata')
            logger.error(e)




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

def extractZipFile(localfilename,extractedDir,dp):
    import zipfile
    try:
        hash = fixZipGetHash(localfilename)
        logger.info("hash: %s", hash)

        with zipfile.ZipFile(filetools.file_open(localfilename, 'rb', vfs=False)) as zip:
            xbmc.sleep(1000)
            logger.info(f"extracting zip: {localfilename} to {extractedDir}")
            size = sum([zinfo.file_size for zinfo in zip.filelist])
            cur_size = 0
            for member in zip.infolist():
                zip.extract(member, extractedDir)
                cur_size += member.file_size
                dp.update(int(80 + cur_size * 15 / size))
            logger.info(f"extracted zip: {localfilename} to {extractedDir}")

        return  hash  
    except Exception as e:
        logger.info('Non sono riuscito ad estrarre il file zip')
        logger.error(e)
        import traceback
        logger.error(traceback.print_exc())
        dp.close()
        #remove(localfilename)
