#! /usr/bin/python

"""
"""

import os
import urllib2 
import HTMLParser

download_links = []

class LinkParser(HTMLParser.HTMLParser):
	def handle_starttag(self, tag, attrs):
		if tag == 'a':
			 link = attrs[0][1]
			 print link
			 is_download_link = link.startswith('http://download.linuxjournal.com/pdf/get-doc.php?code=')
			 if is_download_link:
				 download_links.append(link)

# users account number for linux journal subscription
# TODO(mk): print usage and exit if AN is missing
account_number = os.environ['AN']

# download url
download_url = 'https://secure2.linuxjournal.com/pdf/dljdownload.php?ucLJFooter_accountnumber='

full_url = '%s%s' % (download_url, account_number)
response = urllib2.urlopen(full_url)
page = response.read()

parser = LinkParser()
parser.feed(page)

for link in download_links:
	print link

# parse issue number

print "downloading magazine'

download_link = "%s&action=spit" % download_links[0]
pdf = urllib2.urlopen(download_link)
with open('filename.pdf', 'w') as file:
	file.write(pdf.read())

