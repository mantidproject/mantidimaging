#!/home/dtasev/anaconda2/bin/python
import urllib
import urllib2
import os
import getpass
import pac_api
from argparse import ArgumentParser
PACPASSFILE = '.pacpass'

parser = ArgumentParser()

parser.add_argument("-u",  dest="federalid",
                    help="Your federal id", metavar="Federal ID", required=True)

args = parser.parse_args()

username = (args.federalid)
password = getpass.getpass()
url = 'https://portal.scarf.rl.ac.uk/cgi-bin/token.py'
params = urllib.urlencode({
    'username': username,
    'password': password
})
response = urllib2.urlopen(url, params).read()
if "https://portal.scarf.rl.ac.uk" in response:
    url_token = response.splitlines()
    pac_api.saveToken(url_token[0], url_token[1])
    print "You have now successfully logged onto PAC"
else:
    print response
