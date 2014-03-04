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
import getpass
import argparse
from bs4 import BeautifulSoup

BASE_URL = 'https://huskycardcenter.neu.edu'

def scrape(path):
    """ Scrape cookie and sesstoken from given page. """

    path = BASE_URL + path
    page = urllib2.urlopen('{}'.format(path))
    cookie = page.headers.get('set-cookie').split(';')[0]
    if args.verbose:
        print '[i] Got login cookie: {}'.format(cookie)
    soup = BeautifulSoup(page.read())
    sesstok = soup.find('script').text.split()[-1][1:-2]
    if args.verbose:
        print '[i] Got login session token: {}'.format(sesstok)
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
    try:
        with open(config_path) as f:
            config = json.load(f)
    except IOError:
        print '[!] You need a ~/.unlock.json config file. \
Create one now (y/n)?',
        input = raw_input()
        if input.lower() == 'y':
            config = create_config()
        else:
            print '[-] Exiting'
            sys.exit(1)
    return config

def get_args():
    """ Parse arguments and return dictionary. """

    parser = argparse.ArgumentParser(description="Unlock your Northeastern \
                                     University on campus, NFC enabled, dorm \
                                     door via the command line.")
    parser.add_argument('-r', '--room', help='unlock your actual room door \
                        instead of your apartment\'s door',
                        action='store_true')
    parser.add_argument('-v', '--verbose', help='display detailed info',
                        action='store_true')
    return parser.parse_args()


def create_config():
    """ Generate ~/.unlock.json config file. """

    print """[+] This will generate a ~/.unlock.json file for you, which is
    necessary for the script to authenticate you into huskycardcenter.neu.edu"""
    u = raw_input('myNEU username: ')
    p = getpass.getpass('myNEU password: ')
    config_path = os.path.expanduser('~/.unlock.json')
    with open(config_path, 'w') as f:
        json.dump({'USER': u, 'PASS': p}, f, indent=4)
    print '[+] Config file created'
    print '[-] Exiting'


def main():
    global args
    args = get_args()
    config = get_config()

    if args.verbose: print '[+] Starting'

    sesstok, cookie = scrape('/login/ldap.php')
    post_body = urllib.urlencode({'__sesstok': sesstok, 'user': config['USER'],
                                  'pass': config['PASS']})

    login = httplib.HTTPSConnection('huskycardcenter.neu.edu')
    login.request('POST', '/login/ldap.php', post_body, generate_headers(cookie))
    r1 = login.getresponse()
    newcookie = r1.getheader('set-cookie').split(';')[0]
    if args.verbose: print '[i] Got user cookie: {}'.format(newcookie)

    headers = generate_headers(newcookie)
    test = httplib.HTTPSConnection('huskycardcenter.neu.edu')
    test.request('GET', '/student/welcome.php', headers=headers)
    r2 = test.getresponse()

    if 'Welcome to CS Gold WebCard Center' in r2.read():
        if args.verbose: print '[+] Login Successful!'
    else:
        print '[-] Login Failed!'
        print '[-] Exiting'
        sys.exit()

    if args.verbose: print '[+] Getting door session token'
    openmydoor = httplib.HTTPSConnection('huskycardcenter.neu.edu')
    openmydoor.request('GET', '/student/openmydoor.php', headers=headers)
    r3 = openmydoor.getresponse()
    soup = BeautifulSoup(r3.read())
    door_sesstok = soup.find('script').text.split()[-1][1:-2]
    if args.verbose: print '[i] Got sesstok: {}'.format(door_sesstok)

    room = 2 if args.room else 1
    open_body = urllib.urlencode({'__sesstok': door_sesstok,
                                  'doorType': room, 'answeredYes': 'yes'})

    if args.verbose: print '[+] Unlocking door! (it may take up to 10 seconds,\
 wait for it)'
    boom = httplib.HTTPSConnection('huskycardcenter.neu.edu')
    boom.request('POST', '/student/openmydoor.php', open_body, headers)

if __name__ == '__main__':
    main()
