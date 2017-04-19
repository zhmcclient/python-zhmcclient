#!/usr/bin/env python

# Copyright 2016 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# zhmcsh.py: command line tool for HMC web API

import argparse
import getpass
import importlib
import os
import readline
import string
import sys
import zhmcclient

# workaround https verification noise
import requests
requests.packages.urllib3.disable_warnings()


## Command line parsing
# The name by which the script is invoked
script_filename = os.path.basename(sys.argv[0])

# arguments and options
host = [['host'], {'help': 'HMC hostname or IP address'}]
cpc = [['cpc'], {'help': 'CPC name'}]
lpar = [['lpar'], {'help': 'LPAR name'}]
user = [['-u', '--user'], {'help': 'HMC userid to use'}]
nokeyring = [['-K', '--nokeyring'], {'action': 'store_true',
                                     'help': 'don\'t use system keyring for credentials'}]
passwd = [['-p', '--password'], {'action': 'store_true',
                                 'help': 'always ask for password'}]
loadaddr = [['loadaddr'], {'help': 'load device address'}]
partition = [['partition'], {'help': 'partition name'}]

# argument lists for objects and operations
# HMC level
args_exit = []
args_version = [host]

# CPC level
# we are specifying the common options for both
# the object and the operations to allow the
# options to appear everywhere
# this is true for all object types
args_cpc = [user, nokeyring, passwd]
args_cpc_op  = args_cpc + [host]
args_cpc_single_op  = args_cpc_op + [cpc]

# LPAR level
args_lpar = args_cpc
args_lpar_op = args_lpar + [host, cpc]
args_lpar_single_op = args_lpar_op + [lpar]

# partition level
args_partition = args_cpc
args_partition_op = args_partition + [host, cpc]
args_partition_single_op = args_partition_op + [partition]

# operations and their arguments
op_exit = {'name': 'exit',
           'desc': 'exit the interactive HMC processor',
           'args': args_exit}

op_version = {'name': 'version',
              'desc': 'display HMC version',
              'args': args_version}

op_cpc_list = {'name': 'list',
               'desc': 'list CPCs',
               'args': args_cpc_op}

op_cpc_show = {'name': 'show',
               'desc': 'show CPC details',
               'args': args_cpc_single_op}

op_lpar_list = {'name': 'list',
                'desc': 'list LPARs',
                'args': args_lpar_op}

op_lpar_show = {'name': 'show',
                'desc': 'show LPAR details',
                'args': args_lpar_single_op}

op_lpar_activate = {'name': 'activate',
                    'desc': 'activate LPAR',
                    'args': args_lpar_single_op}

op_lpar_deactivate = {'name': 'deactivate',
                      'desc': 'deactivate LPAR',
                      'args': args_lpar_single_op}

op_lpar_load = {'name': 'load',
                'desc': 'load LPAR',
                'args': args_lpar_single_op + [loadaddr]}

op_partition_list = {'name': 'list',
                     'desc': 'list partitions',
                     'args': args_partition_op}

op_partition_show = {'name': 'show',
                     'desc': 'show partition details',
                     'args': args_partition_single_op}

op_partition_start = {'name': 'start',
                      'desc': 'start partition',
                      'args': args_partition_single_op}

op_partition_stop = {'name': 'stop',
                     'desc': 'stop partition',
                     'args': args_partition_single_op}

# objects and their operations
obj_cpc = {'name': 'cpc',
           'desc': 'execute CPC command',
           'args': args_cpc,
           'ops': [op_cpc_list, op_cpc_show]}

obj_lpar = {'name': 'lpar',
            'desc': 'execute LPAR command',
            'args': args_lpar,
            'ops': [op_lpar_list,
                    op_lpar_show,
                    op_lpar_activate,
                    op_lpar_deactivate,
                    op_lpar_load]}

obj_partition = {'name': 'partition',
                 'desc': 'execute partition command',
                 'args': args_partition,
                 'ops': [op_partition_list,
                         op_partition_show,
                         op_partition_start,
                         op_partition_stop]}

obj_script = {'name': script_filename,
              'desc': 'execute HMC command',
              'ops': [op_version, op_exit],
              'children': [obj_cpc,
                           obj_lpar,
                           obj_partition]}

# allowed object names and aliases in obj_table
obj_alias = {'zhmccpc': obj_cpc,
             'zhmclpar': obj_lpar,
             'zhmcpart': obj_partition}

obj_table = {obj_script['name']: obj_script}
for o in obj_script['children']:
    obj_table[o['name']] = o

obj_table.update(obj_alias)

# allowed top level script operations in op_table
op_table = {}
for o in obj_script['ops']:
    op_table[o['name']] = o

# command line argument functions
def addargs(parser, id, args, isop=False):
    """
    Add subcommand specific arguments
    """
    if isop:
        parser.set_defaults(op=id)
    else:
        parser.set_defaults(obj=id)
    for a in args:
        parser.add_argument(*a[0], **a[1])

def mkobjargs(objname):
    """
    build an argument parser for the given object or command
    name
    """
    if objname in obj_table:
        # obj_table contains the list of all objects and aliases, so
        # we can directly use the object
        obj = obj_table[objname]
        isop = False
    elif objname in op_table:
        # op_table contains the list of root script operations
        # we can directly use the object
        obj = op_table[objname]
        isop = True
    else:
        # we didn't recognize the object or command but
        # it still may be valid, we will let the argument
        # parser decide
        obj = obj_script
        isop = False
    ap = argparse.ArgumentParser(prog=objname, description=obj['desc'])
    if 'args' in obj:
        addargs(ap, obj['name'], obj['args'], isop);
    if 'ops' in obj or 'children' in obj:
        subap = ap.add_subparsers()
        if 'ops' in obj:
            for o in obj['ops']:
                sb = subap.add_parser(o['name'], description=o['desc'])
                addargs(sb, o['name'], o['args'], True);
        if 'children' in obj:
            # we have at most one level of child objects
            # so we abstain from using recursion
            for c in obj['children']:
                sb = subap.add_parser(c['name'], description=c['desc'])
                if 'args' in c:
                    addargs(sb, c['name'], c['args'])
                    if 'ops' in c:
                        subsubap = sb.add_subparsers()
                        for o in c['ops']:
                            ssb = subsubap.add_parser(o['name'],
                                                      description=o['desc'])
                            addargs(ssb, o['name'], o['args'], True);
    return ap

## Helpers
# Keyring module loaded dynamically if present
kr_mod = None
kr_setpass = None
kr_getpass = None
kr_token = 'zhmcsh'
def initkeyring():
    """
    Dynamically import keyring module if present.
    """
    global kr_mod
    global kr_setpass
    global kr_getpass
    if kr_mod == None:
        try:
            kr_mod = importlib.import_module('keyring')
            kr_setpass = getattr(kr_mod, 'set_password')
            kr_getpass = getattr(kr_mod, 'get_password')
        except:
            pass

# Credentials
def getcreds(args):
    """
    Prompt for userid if not provided and password.
    Optionally use a system keyring to retrieve password
    for a given user.
    """
    if not args.nokeyring and kr_mod == None:
        initkeyring()
    password = None
    if args.user:
        userid = args.user
    else:
        userid = raw_input('Userid: ')
    if kr_mod:
        password = kr_getpass(kr_token, userid)
    if password == None or args.password:
        password = getpass.getpass('Password: ')
    if kr_mod:
        kr_setpass(kr_token, userid, password)
    return {'userid': userid, 'password': password}

# Error handling
def error(err):
    if isinstance(err, zhmcclient.ConnectionError):
        sys.exit('Connection to HMC could not be established')
    elif isinstance(err, zhmcclient.AuthError):
        sys.exit('Authentication with HMC failed')
    else:
        sys.exit('Unknown error occurred')

# property printer
def dictprint(d, level=0):
    for k in d:
        propprint(k, d, level + 1)

def listprint(l, level=0):
    for i in l:
        valprint(i, level + 1, True)

def valprint(v, level=0, listval=False):
    if isinstance(v, list):
        sys.stdout.write('\n')
        listprint(v, level)
    elif isinstance(v, dict):
        if not listval:
            sys.stdout.write('\n')
        dictprint(v, level)
    else:
        if listval:
            sys.stdout.write(string.ljust('', level))
        sys.stdout.write(str(v))
        sys.stdout.write('\n')

def propprint(n, p, level=0):
    sys.stdout.write(string.ljust('', level) + n + ': ')
    valprint(p[n], level, False)

## Core processing
# API functions
def version(client,args):
    """
    Retrieve and display HMC API Version
    """
    try:
        version = client.version_info()
        print('API Version = %s.%s' % version)
    except zhmcclient.Error as err:
        error(err)

# Exit handling quirks needed since we intercept the
# regular sys.exit in shell mode but want to quit
# if op=exit was selected (duh)
class UserExit(Exception):
    pass

def exit(client, args):
    raise UserExit()

# Object handlers and helpers
def findcpc(client, args):
    cpc = client.cpcs.find(name=args.cpc)
    if cpc == None:
        sys.exit('CPC %s not found' % args.cpc)
    else:
        return cpc

def cpc(client,args):
    """
    Perform CPC operation
    """
    try:
        if args.op == 'list':
            cpcs = client.cpcs.list()
            if cpcs:
                print('CPC%s\tStatus\n%s\t%s' % (string.ljust('', 8),
                                                 string.ljust('', 8, '-'),
                                                 string.ljust('', 16, '-')))
                for c in cpcs:
                    print('%s\t%s' % (string.ljust(c.properties['name'], 8),
                                      c.properties['status']))
        elif args.op == 'show':
            cpc = findcpc(client, args)
            if cpc:
                cpc.pull_full_properties()
                print('CPC: ' + args.cpc)
                dictprint(cpc.properties)
        else:
            sys.exit('unknown CPC operation %s requested' % args.op)
    except zhmcclient.Error as err:
        error(err)

def findlpar(cpc, args):
    lpar = cpc.lpars.find(name=args.lpar)
    if lpar == None:
        sys.exit('LPAR %s not found' % args.lpar)
    else:
        return lpar

def lpar(client, args):
    """
    Perform lpar operation
    """
    try:
        cpc = findcpc(client, args)

        if cpc.dpm_enabled:
            sys.exit('CPC operates in DPM mode: LPAR operations not supported')

        if args.op == 'list':
            lpars = cpc.lpars.list()
            if lpars:
                print('LPAR%s\tStatus\n%s\t%s' % (string.ljust('', 10),
                                                string.ljust('', 8, '-'),
                                                string.ljust('', 16, '-')))
                for p in lpars:
                    print('%s\t%s' % (string.ljust(p.properties['name'], 10),
                                      p.properties['status']))
        elif args.op == 'show':
            lpar = findlpar(cpc, args)
            if lpar:
                lpar.pull_full_properties()
                print('LPAR: ' + args.lpar)
                dictprint(lpar.properties)
        elif args.op == 'activate':
            lpar = findlpar(cpc, args)
            if lpar:
                lpar.activate()
        elif args.op == 'deactivate':
            lpar = findlpar(cpc, args)
            if lpar:
                lpar.deactivate()
        elif args.op == 'load':
            lpar = findlpar(cpc, args)
            print args.loadaddr
            if lpar:
                lpar.load(args.loadaddr)
        else:
            sys.exit('unknown lpar operation %s requested' % args.op)
    except zhmcclient.Error as err:
        error(err)

def findpartition(cpc, args):
    partition = cpc.partitions.find(name=args.partition)
    if partition == None:
        sys.exit('parition %s not found' % args.partition)
    else:
        return partition

def partition(client, args):
    """
    Perform partition operation
    """
    try:
        cpc = findcpc(client, args)

        if not cpc.dpm_enabled:
            sys.exit('CPC does not operate in DPM mode: partition operations not supported')

        if args.op == 'list':
            partitions = cpc.partitions.list()
            if partitions:
                print('Partition%s\tStatus\n%s\t%s' % (string.ljust('', 10),
                                                       string.ljust('', 8, '-'),
                                                       string.ljust('', 16, '-')))
                for p in partitions:
                    print('%s\t%s' % (string.ljust(p.properties['name'], 10),
                                      p.properties['status']))
        elif args.op == 'show':
            partition = findpartition(cpc, args)
            if partition:
                partition.pull_full_properties()
                print('Partition: ' + args.partition)
                dictprint(partition.properties)
        elif args.op == 'start':
            partition = findpartition(cpc, args)
            if partition:
                partition.start()
        elif args.op == 'stop':
            partition = findpartition(cpc, args)
            if partition:
                partition.stop()
        else:
            sys.exit('unknown partition operation %s requested' % args.op)
    except zhmcclient.Error as err:
        error(err)

# dispatch operations
hosts = {}
def dispatch(args):
    """
    prepare execution environment and dispatch
    to the responsible operation handler
    """
    global hosts
    if 'host' in args:
        # we need a host
        if args.host not in hosts:
            hosts[args.host] = {'credentials': None,
                                'authreq': False,
                                'client': None}
        if 'user' in args:
            # we need credentials
            if hosts[args.host]['credentials'] == None or \
               args.user and \
               hosts[args.host]['credentials']['userid'] != args.user or \
               args.password:
                hosts[args.host]['credentials'] = getcreds(args)
                hosts[args.host]['authreq'] = True

        # setup the connection
        # a bit ugly, we have cases not requiring authentication
        if hosts[args.host]['authreq'] == True:
            session = zhmcclient.Session(host=args.host, **hosts[args.host]['credentials'])
            hosts[args.host]['client'] = zhmcclient.Client(session)
            hosts[args.host]['authreq'] = False
        elif hosts[args.host]['client'] == None:
            session = zhmcclient.Session(host=args.host)
            hosts[args.host]['client'] = zhmcclient.Client(session)
        client = hosts[args.host]['client']
    else:
        client = None

    if 'obj' in args:
        handler = args.obj
    else:
        handler = args.op

    globals()[handler](client, args)

# interactive 'shell'
def zhmcshell():
    """
    Run the interactive HMC shell
    """
    while True:
        try:
            cmdargs = raw_input(script_filename + ': ').split()
        except EOFError:
            break
        if len(cmdargs) == 0 or \
           cmdargs[0] not in obj_table.keys() and \
           cmdargs[0] not in op_table.keys():
            print('Supported objects and operations:')
            for o in obj_script['children']:
                print('\t%-15s[-h] %s' % (o['name'], o['desc']))
            for o in obj_script['ops']:
                print('\t%-15s[-h] %s' % (o['name'], o['desc']))
        else:
            try:
                ap = mkobjargs(cmdargs[0])
                args = ap.parse_args(cmdargs[1:])
                dispatch(args)
            except SystemExit as se:
                if isinstance(se.code, basestring):
                    print se.code

# main
try:
    if len(sys.argv) == 1 and script_filename not in obj_alias:
        zhmcshell()
    else:
        argparser = mkobjargs(script_filename)
        args = argparser.parse_args()
        dispatch(args)
except UserExit:
    pass
