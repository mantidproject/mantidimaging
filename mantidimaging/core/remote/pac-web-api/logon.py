#!/usr/bin/python
import urllib
import urllib2
import os
from os.path import expanduser
import getpass
from argparse import ArgumentParser

parser = ArgumentParser()

parser.add_argument("-u",  dest="federalid", help="Your federal id", metavar="Federal ID",required=True)

args = parser.parse_args()

username=(args.federalid)
password = getpass.getpass()
url = 'https://portal.scarf.rl.ac.uk/cgi-bin/token.py'
params = urllib.urlencode({
  'username': username,
  'password': password
})
response = urllib2.urlopen(url, params).read()
if "https://portal.scarf.rl.ac.uk" in response:
       	fpath=expanduser("~")
       	file = fpath + '/' + ".pacpass"
       	f = open(file,'w')
       	f.write(response) 
	print "You have now successfully logged onto PAC"
       	f.close() 
else:
	print response	
