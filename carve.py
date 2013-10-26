#!/usr/bin/env python

import csv
import datetime
import os
import shutil
import sqlite3 as sql
import subprocess
import sys
import plistlib as pl

# configs
root_dir = '/Users/mark/code/sec/forensics/ciphertech/iOS4_logical_acquisition/'
root_output_dir = '/Users/mark/code/sec/forensics/ciphertech/carvings/'
targets = ['AddressBook', 'Calendar', 'Cookies', 'Mail', 'Maps', 'Safari', 'SMS', 'Voicemail']

### functions ##########

def die(msg=''):
    sys.exit(msg)

def dir_scrape():
    """Traverses directories, searching for sqlite databases and plist files, as specified in targets list."""

    for root, dirs, files in os.walk('.'):
        # print dirs
        # if (root in targets) or (root in dirs)
        for d in dirs:
            if d in targets:

                # the Mail directory setup is weird, so special case
                if d == 'Mail':
                    output_dir = root_output_dir + d
                    os.mkdir(output_dir)
                    os.chdir(root + '/Mail')
                    mail_pre_carve(output_dir)
                    os.chdir(root_dir)
                    continue

                if d == 'Cookies':
                    output_dir = root_output_dir + d
                    try:
                        os.mkdir(output_dir)
                    except:
                        pass
                    for f in os.listdir(root + "/" + d):
                        shutil.copy(root + '/' + d + '/' + f, output_dir)
                    continue

                # print d
                # print dirs
                # print root
                # print files
                output_dir = root_output_dir + d
                try:
                    os.mkdir(output_dir)
                except OSError:
                    continue
                # os.chdir(root)
                # print os.listdir(root + "/" + d)
                # print os.listdir(root + "/" + d)
                for f in os.listdir(root + "/" + d):
                    cmd = "file '%s'" % (root + "/" + d + "/" + f)
                    # print cmd
                    cmd_obj = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
                    cmd_output = cmd_obj.communicate()[0]
                    # print cmd_output
                    if ('SQLite' in cmd_output) or ('Apple binary' in cmd_output) or ('XML' in cmd_output):
                        # print cmd_output
                        shutil.copy(root + "/" + d + "/" + f, output_dir) 
                        # print root + "/" + d + "/" + f + "   =>  " + output_dir
                        # print
                        # print

def mail_pre_carve(output_dir):
    # how fucking scary does this look
    # not actually that bad ;)

    for item in os.listdir('.'):
        if 'Protected' in item:
            shutil.copy(item, output_dir)
            continue
        if item[0:4] == 'IMAP':
            for root, dirs, files in os.walk(item):
                if 'Messages' in root:
                    for f in files:
                        shutil.copy(root + '/' + f, output_dir)
    pass

def cal_carve():
    """Asssumes it is currently in the output directory (carvings). Finds /Calendar and performs analysis of db."""
    
    os.chdir('Calendar')
    cal_content = []
    start_ts = ''
    end_ts = ''

    # indexes
    id = 0
    summary = 1
    location = 2
    description = 3
    start_date = 4
    loc = 5
    end_date = 6

    for file in os.listdir('.'):
        conn = sql.connect(file)
        c = conn.cursor()

        c.execute('SELECT * from Event')
        cal_content = c.fetchall()

        with open(file.split('.')[0] + "_summary.txt", 'w') as f:
            for row in cal_content:
                start_ts = str(datetime.datetime.fromtimestamp(row[4]))
                end_ts = str(datetime.datetime.fromtimestamp(row[6]))

                f.write('Event ' + str(row[id]) + ':\n\n')
                f.write('Summary: ' + row[summary] + '\n')
                f.write('Description: ' + str(row[description]) + '\n')
                f.write('Location: ' + row[loc] + '\n')
                f.write('Start: ' + start_ts + '\n')
                f.write('End: ' + end_ts + '\n')

        conn.close()

    os.chdir(root_output_dir)


def sms_carve():
    """Asssumes it is currently in the output directory (carvings). Finds /SMS and performs analysis of db."""

    os.chdir('SMS')
    sms_contents = []
    ts = ''
    destination = ''

    # indexes
    id = 0
    phone_number = 1
    date = 2
    text = 3
    recipient = 15

    for file in os.listdir('.'):
        conn = sql.connect(file)
        c = conn.cursor()

        c.execute('SELECT * from message')
        sms_contents = c.fetchall()

        with open(file.split('.')[0] + "_summary.txt", 'w') as f:
            for row in sms_contents:

                if row[phone_number] == None:
                    destination = str(row[recipient])
                    destination = destination[destination.find('<string>') + 8:destination.find('</string>')]
                else:
                    destination = row[phone_number]

                ts = str(datetime.datetime.fromtimestamp(row[date]))
                f.write('Message ' + str(row[id]) + ':\n\n')
                f.write('To: ' + destination + '\n')
                f.write('Date: ' + ts + '\n')
                f.write('Contents: ' + str(row[text]) + '\n\n')

        conn.close()

    os.chdir(root_output_dir)

def mail_carve():
    """Asssumes it is currently in the output directory (carvings). Finds /Mail and performs analysis of messages and db."""

    os.chdir('Mail')
    os.mkdir('Messages')

    # indexes
    sender = 1
    email = 3

    mail_summary = open('mail_summary.txt', 'w')
    mail_contents = ''
    recent_correspondents = []

    for file in os.listdir('.'):
        try:
            if file.split('.')[2] == 'emlxpart':
                shutil.move(file, 'Messages')
        except:
            pass # for the files without extensions

        if 'Protected' in file:
            conn = sql.connect(file)
            c = conn.cursor()
            c.execute('SELECT * from messages')
            mail_contents = c.fetchall()
            email_addr = mail_contents[0][email]
            mail_summary.write('Email Address: ' + email_addr + '\n\n')
            for row in mail_contents:
                if row[sender] in recent_correspondents:
                    continue
                else:
                    recent_correspondents.append(row[sender])
            mail_summary.write('Recent Correspondents:\n')
            for r in recent_correspondents:
                mail_summary.write(r + '\n')

            conn.close()

    mail_summary.close()
    os.chdir(root_output_dir)

def cookie_carve():
    """Asssumes it is currently in the output directory (carvings). Finds /Mail and performs analysis of messages and db."""

    os.chdir('Cookies')
    plist_contents = {}

    

    with open('cookies_summary.txt', 'w') as f:
        ind = 1
        plist_contents = pl.readPlist('Cookies.plist')
        for cookie in plist_contents:
            created_ts = str(datetime.datetime.fromtimestamp(cookie['Created']))
            f.write('Cookie ' + str(ind) + '\n\n')
            f.write('Domain: ' + cookie['Domain'] + '\n')
            f.write('Name: ' + cookie['Name'] + '\n')
            f.write('Created: ' + created_ts + '\n')
            f.write('Expires: ' + str(cookie['Expires']) + '\n')
            try:
                f.write('Value: ' + cookie['Value'] + '\n')
            except:
                pass
            f.write('\n')
            ind += 1

    with open('itunes_stored_cookies_summary.txt', 'w') as f:
        ind = 1
        plist_contents = pl.readPlist('com.apple.itunesstored.plist')
        for cookie in plist_contents:
            created_ts = str(datetime.datetime.fromtimestamp(cookie['Created']))
            f.write('Cookie ' + str(ind) + '\n\n')
            f.write('Domain: ' + cookie['Domain'] + '\n')
            f.write('Name: ' + cookie['Name'] + '\n')
            f.write('Created: ' + created_ts + '\n')
            f.write('Expires: ' + str(cookie['Expires']) + '\n')
            try:
                f.write('Value: ' + cookie['Value'] + '\n')
            except:
                pass
            f.write('\n')
            ind += 1

    os.chdir(root_output_dir)

### main ##########

def main():
    os.chdir(root_dir)
    os.mkdir(root_output_dir)

    dir_scrape();

    os.chdir(root_output_dir)

    cookie_carve()
    sms_carve()
    cal_carve()
    mail_carve()


if __name__ == '__main__':
    main()