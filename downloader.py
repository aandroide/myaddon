import xbmcgui
import urllib
import time
import sys

def download(url, dest, dp = None):
    if not dp:
        dp = xbmcgui.DialogProgress()
        dp.create(' ',"Download In Progress",' ', ' ')
    dp.update(0)
    start_time=time.time()
    urllib.request.urlretrieve(url, dest, lambda nb, bs, fs, url=url: _pbhook(nb, bs, fs, url, dp, start_time))

def _pbhook(numblocks, blocksize, filesize, url, dp, start_time):
        try: 
            percent = min(numblocks * blocksize * 100 / filesize, 100) 
            currently_downloaded = float(numblocks) * blocksize / (1024 * 1024) 
            kbps_speed = numblocks * blocksize / (time.time() - start_time) 
            if kbps_speed > 0: 
                eta = (filesize - numblocks * blocksize) / kbps_speed 
            else: 
                eta = 0 
            kbps_speed = kbps_speed / 1024 
            mbps_speed = kbps_speed / 1024 
            total = float(filesize) / (1024 * 1024) 
            mbs = '[COLOR white]%.02f MB[/COLOR] di %.02f MB' % (currently_downloaded, total)
            e = 'Speed: [COLOR lime]%.02f Mb/s ' % mbps_speed  + '[/COLOR]'
            e += 'Tempo rimanente: [COLOR yellow]%02d:%02d' % divmod(eta, 60) + '[/COLOR]'
            dp.update(int(percent),  str(mbs) + '\n' + str(e))
        except: 
            percent = int(100) 
            dp.update(percent) 
        if dp.iscanceled():
            dialog = xbmcgui.Dialog()
            dialog.ok("ATTENZIONE", 'Download cancellato.')
				
            sys.exit()
            dp.close()