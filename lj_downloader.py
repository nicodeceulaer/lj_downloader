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

TODO:
    - emailing
    - Add destination path
    - print warnings if issue is not found, try issue 200 for epub
"""

import os
import sys
import urllib2 
import HTMLParser
import urlparse
import optparse
import smtplib
import pdb

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders

options = None

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
    """ Generates file name for the issue

    Args:
        issue_info: given issue tuple
    """
    issue_number, file_format, link = issue_info
    base = options.base_filename
    return "%s-%s.%s" % (base, issue_number, file_format)


def write_issue(data, filename):
    """ Writes the given issue data to file

    Args:
        data: file-like object that represents the issue
        filename: File name of the issue when written to disk
    """
    with open(filename, 'w') as file:
        file.write(data.read())


def mode_download_all(issue_information):
    """ Downloads all the avaible Linux Journals

    Args:
        issue_information: information about all the found issues
    """
    for issue in issue_information:
        file_format = issue[1]
        if options.file_format == file_format:
            file = download_issue(issue)
            filename = generate_name_for_issue(issue)
            write_issue(file, filename)


def mode_download_issue_number(issue_number, issue_information):
    """ Downloads a specific issue
    
    Args:
        issue_number: what issue to download
        issue_information: information about all the found issues
    """
    for issue in issue_information:
        number_of_this_issue = issue[0]
        file_format = issue[1]
        if number_of_this_issue == str(issue_number) and \
           options.file_format == file_format:
            file = download_issue(issue)
            filename = generate_name_for_issue(issue)
            write_issue(file, filename)


def mode_download_and_email_latest(issue_information):
    """ Downloads and emails the latest issue 

    Args:
        issue_information: information about all the found issues
    """
    issue_number, file_format = '', ''
    latest_issue = None
    for issue in issue_information:
        file_format = issue[1]
        if file_format == options.file_format:
            print "found the issue: %s", issue
            latest_issue = issue
            break

    is_indeed_latest = try_to_update_latest_issue_number(latest_issue[0])
    if latest_issue and is_indeed_latest:
        print latest_issue
        file = download_issue(latest_issue)
        filename = generate_name_for_issue(latest_issue)
        write_issue(file, filename)

        to_address = 'markus.kauppila@gmail.com'
        send_issue_as_mail_to(latest_issue, filename, to_address)
    else:
        print "No newer issue found"

def send_issue_as_mail_to(issue, filename, to_address):
    """ Send the file to the given address.

    needs issue number <- issue tuple
    needs file type <- issue tuple
    """
    issue_number = issue[0]
    file_format = issue[1]

    message = MIMEMultipart('Heres the latest issue')
    message['Subject'] = 'Linux Journal - %s' % issue_number
    message['To'] = to

    # defaults to pdf
    mime_ending = 'pdf'
    if file_format == 'mobi':
        mime_ending = 'x-mobipocket-ebook'
    elif file_format == 'epub':
        mime_ending = 'epub+zib'

    part = MIMEBase('application', mime_ending)
    attachment_file = open(filename, 'rb').read()
    part.set_payload(attachment_file)
    Encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="%s"' 
            % os.path.basename(filename))
    message.attach(part)

    from_address = 'lj@mailer.org'
    server = smtplib.SMTP('localhost')
    server.sendmail(from_address, to_address, msg.as_string())
    server.quit()

def try_to_update_latest_issue_number(issue_number):
    """ Tries ot update the latest issue number 
    Number is stored in a file.
    """
    did_update = False
    latest_issue_number = None
    # Check if file exists before opening
    if os.path.exists('latest'):
        with open('latest') as memory:
            latest_issue_number = memory.readline()

    if issue_number > latest_issue_number:
        with open('latest', 'w') as memory:
            print "%s " % issue_number
            memory.write(issue_number)
        did_update = True

    return did_update


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('-a', '--account-number', type='string', action='store', dest='account_number')
    parser.add_option('--mail_to', metavar='foo@bar.org', type='string', action='store', 
            help='Where to mail the latest issue')
    parser.add_option('--base-filename', metavar='linux_journal', type='string', action='store', default='LinuxJournal', dest='base_filename',
            help='Base filename for the downloaded issue, will be appended by issue number and file format')
    parser.add_option('--format', metavar='FILE_FORMAT', type='string', action='store', dest='file_format',  default='pdf',
            help='The desired file format pdf, epub or mobi. Defaults to pdf')
    parser.add_option('--directory', metavar='PATH', type='string', action='store', 
            help='Download directory. Defaults to  current working directory')

    # group modes
    modes = optparse.OptionGroup(parser, 'Mode options', 'Choose one of these')
    modes.add_option('--download-all', action='store_const', const='all', dest='mode', help='help')
    modes.add_option('--download-issue', metavar='XXX', type='int', action='store', dest='mode',  help='help')
    modes.add_option('--download-latest', action='store_const', const='latest', dest='mode', help='help')
    parser.add_option_group(modes)

    global options
    options, arguments = parser.parse_args()
    if options.mode == None:
        print "Requires mode, see ./name --help"
        exit(1)

    # users account number for linux journal subscription
    account_number = options.account_number
    if not account_number:
        print "Account number is missing"
        sys.exit(1)
    print "account number %s" % account_number

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

    # fire off the right execution mode
    if options.mode == 'all':
        mode_download_all(issue_information)
    elif options.mode == 'latest':
        mode_download_and_email_latest(issue_information)
    else:
        issue_number = options.mode
        mode_download_issue_number(issue_number, issue_information)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
