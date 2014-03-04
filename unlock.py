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
        print '[!] You need a ~/.unlock.json config file. ' + \
              'Create one now (y/n)?',
        input = raw_input()
        if input.lower() == 'y':
            config = create_config()
        print '[-] Exiting'
        sys.exit(1)
    return config


def create_config():
    """ Generate ~/.unlock.json config file. """

    print '[+] This will generate a ~/.unlock.json file for you, which is ' + \
          'necessary\n    for the script to authenticate you into ' + \
          'huskycardcenter.neu.edu'
    u = raw_input('myNEU username: ')
    p = getpass.getpass('myNEU password: ')
    config_path = os.path.expanduser('~/.unlock.json')
    with open(config_path, 'w') as f:
        json.dump({'USER': u, 'PASS': p}, f, indent=4)
    print '[+] Config file created'


def scrape(path, cookie, getCookie):
    """ Scrape sesstoken and optionally cookie from given page. """

    url = 'https://{}{}'.format(BASE_URL, path)
    if cookie:
        page_request = urllib2.Request(url, headers=generate_headers(cookie))
        page = urllib2.urlopen(page_request)
    else:
        page = urllib2.urlopen(url)
    if getCookie:
        cookie = page.headers.get('set-cookie').split(';')[0]
        if args.verbose:
            print '[i] Got cookie: {}'.format(cookie)
    soup = BeautifulSoup(page.read())
    sesstok = soup.find('script').text.split()[-1][1:-2]
    if args.verbose:
        print '[i] Got session token: {}'.format(sesstok)
    if getCookie:
        return sesstok, cookie
    else:
        return sesstok


def login(config):
    """ Logins in to huskycardcenter.neu.edu, returns user cookie """
    
    if args.verbose: print '[+] Logging in'
    sesstok, login_cookie = scrape('/login/ldap.php', None, True)
    post_body = urllib.urlencode({'__sesstok': sesstok, 'user': config['USER'],
                                  'pass': config['PASS']})
    login = httplib.HTTPSConnection(BASE_URL)
    login.request('POST', '/login/ldap.php', post_body,
                  generate_headers(login_cookie))
    login_response = login.getresponse()
    cookie = login_response.getheader('set-cookie').split(';')[0]

    if args.verbose: print '[i] Got user cookie: {}'.format(cookie)

    if test_login(cookie):
        if args.verbose: print '[+] Login Successful!'
    else:
        print '[-] Login Failed!'
        print '[-] Exiting'
        sys.exit()
    
    return cookie


def test_login(cookie):
    """ Test whether login to huskycardcenter.neu.edu worked. """
    
    headers = generate_headers(cookie)
    test = httplib.HTTPSConnection(BASE_URL)
    test.request('GET', '/student/welcome.php', headers=headers)
    test_response = test.getresponse()

    if 'Welcome to CS Gold WebCard Center' in test_response.read():
        return True
    else:
        return False
    

def unlock_door(cookie):
    """ Provided the user's cookie, sends the request to unlock the door. """

    if args.verbose: print '[+] Getting door unlock session token'
    door_sesstok = scrape('/student/openmydoor.php', cookie, False)
    if args.verbose: print '[i] Got session token: {}'.format(door_sesstok)

    room = 2 if args.room else 1
    open_body = urllib.urlencode({'__sesstok': door_sesstok,
                                 'doorType': room, 'answeredYes': 'yes'})
    if args.verbose: print '[+] Unlocking door! (it may take up to 10 seconds,\
 wait for it)'
    unlock = httplib.HTTPSConnection('huskycardcenter.neu.edu')
    unlock.request('POST', '/student/openmydoor.php', open_body, 
                 generate_headers(cookie))
    

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


def main():
    global args, BASE_URL
    args = get_args()
    BASE_URL = 'huskycardcenter.neu.edu'
    config = get_config()

    if args.verbose: print '[+] Starting'

    cookie = login(config)
    unlock_door(cookie)


if __name__ == '__main__':
    main()
