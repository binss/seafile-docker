#!/usr/bin/env python
#coding: UTF-8

"""
This script calls the appropriate seafile init scripts (e.g.
setup-seafile.sh or setup-seafile-mysql.sh. It's supposed to run inside the
container.
"""

import argparse
import os
from os.path import abspath, basename, exists, dirname, join, isdir
import shutil
import sys
import uuid
import time

from utils import call, get_conf, get_install_dir, get_script, render_template, get_seafile_version

seafile_version = get_seafile_version()
installdir = get_install_dir()
topdir = dirname(installdir)
shared_seafiledir = '/shared/seafile'
ssl_dir = '/shared/ssl'
generated_dir = '/bootstrap/generated'

def init_letsencrypt():
    if not exists(ssl_dir):
        os.mkdir(ssl_dir)

    domain = get_conf('server.hostname')
    context = {
        'https': False,
        'domain': domain,
    }

    # Create a temporary nginx conf to start a server, which would accessed by letsencrypt
    render_template('/templates/seafile.nginx.conf.template',
                    '/etc/nginx/sites-enabled/seafile.nginx.conf', context)
    call('nginx -s reload')
    call('/scripts/ssl.sh {0} {1}'.format(ssl_dir, domain))

    # Now create the final nginx configuratin
    context = {
        'https': True,
        'domain': domain,
    }
    render_template(
        '/templates/seafile.nginx.conf.template',
        join(generated_dir, 'seafile.nginx.conf'),
        context
    )

    context = {
        'ssl_dir': ssl_dir,
        'domain': domain,
    }
    render_template(
        '/templates/letsencrypt.cron.template',
        join(generated_dir, 'letsencrypt.cron'),
        context
    )

def is_https():
    return get_conf('server.https', '').lower() == 'true'

def generate_local_dockerfile():
    context = {
        'seafile_version': seafile_version,
        'https': is_https(),
        'domain': get_conf('server.domain'),
    }
    render_template('/templates/Dockerfile.template', join(generated_dir, 'Dockerfile'), context)

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parse-ports', action='store_true')

    return ap.parse_args()

def do_parse_ports():
    """
    Parse the server.port_mappings option and print docker command line port
    mapping flags like "-p 80:80 -p 443:443"
    """
    # conf is like '80:80,443:443'
    conf = get_conf('server.port_mappings', '').strip()
    if conf:
        sys.stdout.write(' '.join(['-p {}'.format(part.strip()) for part in conf.split(',')]))
        sys.stdout.flush()

def main():
    args = parse_args()
    if args.parse_ports:
        do_parse_ports()
        return
    if not exists(shared_seafiledir):
        os.mkdir(shared_seafiledir)
    if not exists(generated_dir):
        os.mkdir(generated_dir)

    generate_local_dockerfile()

    if is_https():
        init_letsencrypt()

    init_seafile_server()

def init_seafile_server():
    if exists(join(shared_seafiledir, 'seafile-data')):
        print 'Skipping running setup-seafile-mysql.py because there is existing seafile-data folder.'
        return

    env = {
        'SERVER_NAME': 'seafile',
        'SERVER_IP': get_conf('server.hostname'),
        'MYSQL_USER': 'seafile',
        'MYSQL_USER_PASSWD': str(uuid.uuid4()),
        'MYSQL_USER_HOST': '127.0.0.1',
        # Default MariaDB root user has empty password and can only connect from localhost.
        'MYSQL_ROOT_PASSWD': '',
    }

    # Change the script to allow mysql root password to be empty
    call('''sed -i -e 's/if not mysql_root_passwd/if not mysql_root_passwd and "MYSQL_ROOT_PASSWD" not in os.environ/g' {}'''
         .format(get_script('setup-seafile-mysql.py')))

    setup_script = get_script('setup-seafile-mysql.sh')
    call('{} auto -n seafile'.format(setup_script), env=env)

    files_to_copy = ['conf', 'ccnet', 'seafile-data', 'seahub-data',]
    for fn in files_to_copy:
        src = join(topdir, fn)
        dst = join(shared_seafiledir, fn)
        if not exists(dst) and exists(src):
            shutil.move(src, shared_seafiledir)

if __name__ == '__main__':
    # TODO: validate the content of bootstrap.conf is valid
    main()