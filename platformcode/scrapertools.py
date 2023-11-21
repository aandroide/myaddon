# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Scraper tools for reading and processing web elements
# --------------------------------------------------------------------------------

#from future import standard_library
#standard_library.install_aliases()
#from builtins import str
#from builtins import chr
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import time

from platformcode.entities import html5
from platformcode import logger


# def get_header_from_response(url, header_to_get="", post=None, headers=None):
#     header_to_get = header_to_get.lower()
#     response = httptools.downloadpage(url, post=post, headers=headers, only_headers=True)
#     return response.headers.get(header_to_get)


# def read_body_and_headers(url, post=None, headers=None, follow_redirects=False, timeout=None):
#     response = httptools.downloadpage(url, post=post, headers=headers, follow_redirects=follow_redirects,
#                                       timeout=timeout)
#     return response.data, response.headers




def find_single_match(data, patron, index=0):
    try:
        if index == 0:
            matches = re.search(patron, data, flags=re.DOTALL)
            if matches:
                if len(matches.groups()) == 1:
                    return matches.group(1)
                elif len(matches.groups()) > 1:
                    return matches.groups()
                else:
                    return matches.group()
            else:
                return ""
        else:
            matches = re.findall(patron, data, flags=re.DOTALL)
            return matches[index]
    except:
        return ""

