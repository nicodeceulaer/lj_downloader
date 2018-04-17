#! /usr/bin/python
"""
Copyright (c) 2012 Markus Kauppila <markus.kauppila@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
"""
TODO:
    - handle incorrect account number
    - put latest to home directory and make it hidden
"""

import os
import sys
import urllib2
import urllib
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

def generate_path( filename ):
    """ Generate a full file path for a file

    Args:
        filename: File name of the issue when written to disk
    """
    if options.directory:
        directory = options.directory
        if directory[-1:] != '/':
            directory  += '/'
        path = directory + filename
    else:
        path = filename
    return path

def write_issue(data, filename):
    """ Writes the given issue data to file

    Args:
        data: file-like object that represents the issue
        filename: File name of the issue when written to disk
    """
    path = generate_path( filename )

    with open(path, 'w') as file:
        file.write(data.read())


def mode_download_all(issue_information):
    """ Downloads all the avaible Linux Journals

    Args:
        issue_information: information about all the found issues
    """
    for issue in issue_information:
        file_format = issue[1]
        if options.file_format == file_format:
            filename = generate_name_for_issue(issue)
            path = generate_path( filename )
            if os.path.isfile(path):
                print "Skip download of %s" % path
            else:
                print "Download %s" % path
                file = download_issue(issue)
                write_issue(file, filename)


def mode_download_issue_number(issue_number, issue_information):
    """ Downloads a specific issue

    Args:
        issue_number: what issue to download
        issue_information: information about all the found issues
    """
    found_issue = False
    for issue in issue_information:
        number_of_this_issue = issue[0]
        file_format = issue[1]
        if number_of_this_issue == str(issue_number) and \
           options.file_format == file_format:
            file = download_issue(issue)
            filename = generate_name_for_issue(issue)
            write_issue(file, filename)
            found_issue = True
    return found_issue


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

        if options.email_address:
            to_address = options.email_address
            send_issue_as_mail_to(latest_issue, filename, to_address)
    else:
        print "No newer issue found"


def send_issue_as_mail_to(issue, filename, to_address):
    """ Send the file to the given address.
    """
    issue_number = issue[0]
    file_format = issue[1]

    message = MIMEMultipart('Heres the latest issue')
    message['Subject'] = 'Linux Journal - %s' % issue_number
    message['To'] = to_address

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
    server.sendmail(from_address, to_address, message.as_string())
    server.quit()


def was_previous_month_special_issue(issue_number):
    """ Checks if the issue was special edition
    We're assuming that issue numbers for special editions
    are not actually numbers, but strings
    """
    return issue_number.isdigit() == False


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

    if issue_number == latest_issue_number:
        return did_update

    if (issue_number > latest_issue_number or
       was_previous_month_special_issue(latest_issue_number)) :
        with open('latest', 'w') as memory:
            print "%s " % issue_number
            memory.write(issue_number)
        did_update = True

    return did_update


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('-a', '--account-number', type='string', action='store', dest='account_number')
    parser.add_option('--email', metavar='foo@bar.org', type='string', action='store', dest='email_address',
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

    options, arguments = parser.parse_args()
    script_name = sys.argv[0]
    if options.mode == None:
        print "Requires mode, see %s --help" % script_name
        exit(1)

    # users account number for linux journal subscription
    account_number = options.account_number
    if not account_number:
        print "Account number is missing, see %s --help" % script_name
        sys.exit(1)
    print "account number %s" % account_number

    # Retrieve download page
    download_url = 'https://secure2.linuxjournal.com/pdf/dljdownload.php'
    data = urllib.urlencode( { 'ucLJFooter_accountnumber' : account_number } )
    response = urllib2.urlopen(url=download_url, data=data)
    page = response.read()

    print "downloaded %s" % download_url
    print "result= %s" % page

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

        print "Found issue %s (%s)" % (issue_number, file_format)
        issue_information.append((issue_number, file_format, link))

    # fire off the right execution mode
    if options.mode == 'all':
        mode_download_all(issue_information)
    elif options.mode == 'latest':
        mode_download_and_email_latest(issue_information)
    else:
        issue_number = options.mode
        did_download_issue = mode_download_issue_number(issue_number, issue_information)
        if did_download_issue == False:
            print "Couldn't download issue number %s in %s format" % (issue_number, options.file_format)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
