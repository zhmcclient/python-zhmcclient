#!/usr/bin/env python
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Copyright Red Hat
#
#   SPDX-License-Identifier: GPL-2.0
#
#   Author: Sebastian Mitterle <smitterl@redhat.com>

"""
Example that triggers load from ftp from a specified generic.ins
and displays the console output.
This is useful when the .prm file has a kickstart reference for
a fully automated installation.
"""
import sys
import time
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
import yaml
import zhmcclient


PRINT_METADATA = False

def receive_until_KeyboardInterrupt(receiver):
    try:
        for headers, message in receiver.notifications():
            os_msg_list = message['os-messages']
            for os_msg in os_msg_list:
                if PRINT_METADATA:
                    msg_id = os_msg['message-id']
                    held = os_msg['is-held']
                    priority = os_msg['is-priority']
                    prompt = os_msg.get('prompt-text', None)
                    print("# OS message {} (held: {}, priority: {}, "
                          "prompt: {}):".
                          format(msg_id, held, priority, prompt))
                msg_txt = os_msg['message-text'].strip('\n')
                print(msg_txt)
    except KeyboardInterrupt:
        print("Keyboard interrupt - leaving receiver loop")
    finally:
        print("Closing receiver ...")
        receiver.close()

def get_password(host, userid):
    return input("password for user %s on host %s:" % (userid, host))

def load_config(config_filepath):
    """
    config = {
        'host': "<host_url>",
        'userid': "<userid>",
        'ftp_config': {
            'host' : '<ftp_server_url>',
            'username' : '<ftp_user>',
            'password' : '<ftp_password>',
            'file_path' : '<ftp_file_path>'
        },
        'lpar': "<lpar-name>"
    }
    """
    with open(config_filepath) as f:
        return yaml.safe_load(f)

def main(config_filepath):
    config = load_config(config_filepath)
    session = zhmcclient.Session(config['host'], config['userid'], get_password=get_password, verify_cert=False)
    client = zhmcclient.Client(session)
    console = client.consoles.console
    lpars = console.list_permitted_lpars()
    lpar = [x for x in lpars if x.properties.get("name") == config['lpar']][0]
    print(lpar)
    ftp_config = config['ftp_config']
    lpar.load_from_ftp(host=ftp_config['host'], username=ftp_config['username'],
                       password=ftp_config['password'], load_file=ftp_config['file_path'],
                       wait_for_completion=False)
    print("Load from FTP issued. Will connect to OS messages in 10 sec.")
    time.sleep(10)
    topic = lpar.open_os_message_channel()
    receiver = zhmcclient.NotificationReceiver(topic, config['host'], session.session_id, session.session_credential)
    receive_until_KeyboardInterrupt(receiver)


if __name__ == '__main__':
    main(sys.argv[1])
