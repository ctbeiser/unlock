#!/usr/bin/env python

"""
    Simple script to unlock your Northeastern University on campus, NFC
    enabled, dorm door.
"""

import sys
import json
import urllib
import urllib2
import httplib
import os.path
from bs4 import BeautifulSoup

BASE_URL = 'https://huskycardcenter.neu.edu'

def scrape(path):
    """ Scrape cookie and sesstoken from given page. """

    path = BASE_URL + path
    page = urllib2.urlopen('{}'.format(path))
    cookie = page.headers.get('set-cookie').split(';')[0]
    print '[i] Got cookie: {}'.format(cookie)
    soup = BeautifulSoup(page.read())
    sesstok = soup.find('script').text.split()[-1][1:-2]
    print '[i] Got sesstok: {}'.format(sesstok)
    return sesstok, cookie

def generate_headers(cookie):
    headers = {
        'Host': 'huskycardcenter.neu.edu',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'Cookie': cookie
    }
    return headers


def get_config():
    """
        Reads user config information (myNEU user, pass) from ~/.unlock.json
        and returns as dict
    """

    config_path = os.path.expanduser('~/.unlock.json')
    with open(config_path) as f:
        config = json.load(f)
    return config


def main():
    config = get_config()

    print '[+] Getting session token'

    sesstok, cookie = scrape('/login/ldap.php')
    post_body = urllib.urlencode({'__sesstok': sesstok, 'user': config['USER'],
                                  'pass': config['PASS']})

    print '[+] Logging in'

    login = httplib.HTTPSConnection('huskycardcenter.neu.edu')
    login.request('POST', '/login/ldap.php', post_body, generate_headers(cookie))
    r1 = login.getresponse()
    newcookie = r1.getheader('set-cookie').split(';')[0]
    print '[i] New cookie: {}'.format(newcookie)

    headers = generate_headers(newcookie)
    test = httplib.HTTPSConnection('huskycardcenter.neu.edu')
    test.request('GET', '/student/welcome.php', headers=headers)
    r2 = test.getresponse()

    if 'Welcome to CS Gold WebCard Center' in r2.read():
        print '[+] Authenticated Successfully!'
    else:
        print '[-] Authentication Failed'
        sys.exit()

    print '[+] Getting openmydoor.php session token'
    openmydoor = httplib.HTTPSConnection('huskycardcenter.neu.edu')
    openmydoor.request('GET', '/student/openmydoor.php', headers=headers)
    r3 = openmydoor.getresponse()
    soup = BeautifulSoup(r3.read())
    door_sesstok = soup.find('script').text.split()[-1][1:-2]
    print '[i] Got sesstok: {}'.format(door_sesstok)
    print '[?] Enter door to unlock (1 - Apt, 2 - Room):',
    choice = raw_input()

    if choice == '1':
        open_body = urllib.urlencode({'__sesstok': door_sesstok,
                                      'doorType': 1, 'answeredYes': 'yes'})
    elif choice == '2':
        open_body = urllib.urlencode({'__sesstok': door_sesstok,
                                      'doorType': 2, 'answeredYes': 'yes'})
    else:
        print '[-] Invalid choice'
        sys.exit()

    print '[+] Unlocking door! (it may take up to 10 seconds, wait for it)'
    boom = httplib.HTTPSConnection('huskycardcenter.neu.edu')
    boom.request('POST', '/student/openmydoor.php', open_body, headers)

if __name__ == '__main__':
    main()
