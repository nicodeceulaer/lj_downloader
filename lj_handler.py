#! /usr/bin/python

"""
Handles downloading and emailing the latest issue of Linux Journal.

Put this script as cron task.

Usage:
	AN=XXXXXX MAIL_TO=markus.kauppila@gmail.com ./lj_handler.py
		AN= Linux Journal account number
		MAIL_TO= your.email@address.com

	./lj_handler --an XXXXXX --download_all --mail_to markus.kauppila@gmail.com
				 --filename "Linux Journal" --format=[pdf,epub,mobi]

	- Two modes:	
		- download all
		- mail the latest issue

TODO:
	- emailing
	- Add proper support for different file formats
"""

import os
import urllib2 
import HTMLParser
import urlparse

class LinkParser(HTMLParser.HTMLParser):
	def __init__(self):
		HTMLParser.HTMLParser.__init__(self)
		self.verified_links = []

	def verify_link(self, link):
		is_download_link = link.startswith('http://download.linuxjournal.com/pdf/get-doc.php?code=')
		if is_download_link:
			self.verified_links.append(link)

	def handle_starttag(self, tag, attrs):
		if tag == 'a':
			link = attrs[0][1]
			self.verify_link(link)


def download_issue(issue_info):
	""" Download the issue 
	"""
	issue_number, file_format, link = issue_info
	filename = "LinuxJournal-" + issue_number + ".pdf"
	with open(filename, 'w') as file:
		pdf_data = pdf.read()
		file.write(pdf_data)
	return filename
	

if __name__ == "__main__":
	# users account number for linux journal subscription
	# TODO(mk): print usage and exit if AN is missing
	account_number = os.environ['AN']

	download_url = 'https://secure2.linuxjournal.com/pdf/dljdownload.php?ucLJFooter_accountnumber='

	# Retrieve download page
	full_url = '%s%s' % (download_url, account_number)
	response = urllib2.urlopen(full_url)
	page = response.read()

	# parse the download links
	parser = LinkParser()
	parser.feed(page)

	latest_issue_number = None
	# remember the test without the file
	with open('latest') as memory:
		latest_issue_number = memory.readline()
		print "latest issue: %s" % latest_issue_number


	issue_information = []

	for link in parser.verified_links:
		# parse issue number
		parsed_url = urlparse.urlparse(link)
		query = urlparse.parse_qs(parsed_url.query)

		tcode = query['tcode']
		codes = tcode[0].split('-')

		file_format = codes[0]
		issue_number = codes[1]
		link += '&action=spit'

		issue_information.append((issue_number, file_format, link))

		#print "Linux Journal - %s as %s" % (issue_number, file_format)


	if True:
		if issue_number > latest_issue_number and False:
			print "downloading magazine"

			# modify the link for direct download
			link += '&action=spit'
			pdf = urllib2.urlopen(link)
			filename = "LinuxJournal-" + issue_number + ".pdf"
			with open(filename, 'w') as file:
				pdf_data = pdf.read()
				file.write(pdf_data)

			# update the latest issue
			with open('latest', 'w') as memory:
				memory.write(issue_number)
		else:
			pass
			#print "No new issue available"
	else:
		# download all mode, download and safe
		for issue in issue_information:
			print issue


