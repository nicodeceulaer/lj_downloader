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
				 --dst-directory 'l'

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

	Args:
		issue_info: Tuple of three containing information
			about the issue. Tuple is in the form of
			(issue number, file format, download link)
	Returns:
		The downloaded data as file-like object
	"""
	link = issue_info[2]
	return urllib2.urlopen(link)


def generate_name_for_issue(issue_info):
	issue_number, file_format, link = issue_info
	return "LJ-%s.%s" % (issue_number, file_format)


def write_issue(data, filename):
	with open(filename, 'w') as file:
		file.write(data.read())


def mode_download_all(issue_information):
	""" Downloads all the avaible Linux Journals

	Args:
		issue_information:
	"""
	for issue in issue_information:
		file = download_issue(issue)
		filename = generate_name_for_issue(issue)
		write_issue(file, filename)


def mode_download_and_email_latest(issue_information):
	""" Downloads and emails the latest issue 
	"""
	issue = issue_information[0]
	file = download_issue(issue)
	filename = generate_name_for_issue(issue)
	write_issue(file, filename)


def try_to_update_latest_issue_number(issue_number):
	""" Tries ot update the latest issue number 
	Number is stored in a file.
	"""
	did_update = False
	latest_issue_number = None
	# remember the test without the file
	with open('latest') as memory:
		latest_issue_number = memory.readline()
		print "latest issue: %s" % latest_issue_number

	if issue_number > latest_issue_number:
		with open('latest', 'w') as memory:
			memory.write(issue_number)
		did_update = True

	return did_update


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

	issue_information = []
	for link in parser.verified_links:
		parsed_url = urlparse.urlparse(link)
		query = urlparse.parse_qs(parsed_url.query)

		tcode = query['tcode']
		codes = tcode[0].split('-')

		file_format = codes[0]
		issue_number = codes[1]
		link += '&action=spit'

		issue_information.append((issue_number, file_format, link))

	mode = 'all'

	did_update = try_to_update_latest_issue_number(issue_information[0][0])

	if mode == 'all':
		mode_download_all(issue_information)
	elif mode == 'latest':
		mode_download_and_email_latest(issue_information)
	elif mode == 'issue_no':
		pass
