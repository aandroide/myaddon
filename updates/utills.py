import re, requests

def open_link_json(url):
    headers = {'Accept': 'application/json','User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'}
    response = requests.get(url, headers = headers)
    return response.json()
