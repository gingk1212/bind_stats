#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess
from paramiko import SSHClient, AutoAddPolicy

if len(sys.argv) != 5:
    print 'Error: Invalid argument'
    sys.exit(1)

HOST = sys.argv[1]
PORT = sys.argv[2]
USER = sys.argv[3]
PRIVATE_KEY = sys.argv[4]

REMOTE_FILE = '/var/tmp/named_stats.txt'
FILE = '/tmp/named_stats.txt'
SEND_FILE = '/tmp/named_sender.txt'
ZABBIX_SENDER = '/usr/bin/zabbix_sender'


def get_stats_file(remote, local):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(HOST, PORT, USER, key_filename=PRIVATE_KEY)

    sftp = ssh.open_sftp()
    sftp.get(remote, local)

    sftp.close()
    ssh.close()


if __name__ == '__main__':
    get_stats_file(REMOTE_FILE, FILE)

    if os.path.isfile(SEND_FILE) is True:
        os.remove(SEND_FILE)

    fi = open(FILE, 'r')
    fo = open(SEND_FILE, 'w')

    sub = ""
    subsub = ""

    for line in fi:
        if re.match('\+\+\+ ', line):
            match_time = re.search('[0-9]+', line)
            if match_time:
                time = match_time.group()
            else:
                time = 0
        elif re.match('--- ', line):
            pass
        elif re.match('\+\+ ', line):
            sub = re.sub(' ?\+\+ ?', '', line)
            sub = re.sub('[\(|\)|\<|/]', '-', sub)
            sub = sub.replace('\n', '').replace(' ', '-')
        elif re.match('\[', line):
            subsub = line.replace('\n', '').replace(' ', '-')
        else:
            match_value = re.search('[0-9]+', line)
            if match_value:
                value = match_value.group()
            else:
                value = 0
            category = re.sub(' +[0-9]+ ', '', line)
            category = re.sub('[\(|\)|\<|/]', '-', category)
            category = re.sub('\!', 'no-', category)
            category = category.replace('\n', '').replace(' ', '-')

            # <hostname> <key> <timestamp> <value>
            fo.write('%s %s_%s %s %s\n' % (HOST, sub, category, time, value))

    fi.close()
    fo.close()
    if os.path.isfile(FILE) is True:
        os.remove(FILE)

    if subprocess.call(
            [ZABBIX_SENDER, '-z', 'localhost', '-i', SEND_FILE, '-T']):
        sys.exit(0)
    else:
        print 'Error: zabbix sender error'
        sys.exit(1)
