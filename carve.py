#!/usr/bin/env python

import csv
import datetime
import os
import shutil
import sqlite3 as sql
import subprocess
import sys

root_dir = '/Users/mark/code/sec/forensics/ciphertech/iOS4_logical_acquisition/'
root_output_dir = '/Users/mark/code/sec/forensics/ciphertech/carvings/'
targets = ['Library', 'Address Book', 'Calendar', 'Cookies', 'Mail', 'Maps', 'Safari', 'SMS', 'Voicemail']
# targets = ['./mobile/Library/AddressBook', './mobile/Library/Calendar']
# targets = ['AddressBook', 'Calendar', 'Notes', 'Safari', 'SMS', 'Cookies']

def die(msg=''):
    sys.exit(msg)

def dir_scrape():
    """Traverses directories, searching for sqlite databases and plist files, as specified in targets list."""

    for root, dirs, files in os.walk('.'):
        # print dirs
        # if (root in targets) or (root in dirs)
        for d in dirs:
            if d in targets:
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
                    cmd = "file %s" % (root + "/" + d + "/" + f)
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

        print file
        c.execute('SELECT * from message')
        sms_contents = c.fetchall()

        with open(file.split('.')[0] + "_summary.txt", 'w') as f:
            for row in sms_contents:
                print row[recipient]

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

### main ##########

def main():
    os.chdir(root_dir)
    os.mkdir(root_output_dir)

    dir_scrape();

    os.chdir(root_output_dir)

    sms_carve()

if __name__ == '__main__':
    main()