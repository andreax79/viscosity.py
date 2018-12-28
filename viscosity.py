#!/usr/bin/env python
#
# MIT License
#
# Copyright (c) 2017, Andrea Bonomi <andrea.bonomi@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#     The above copyright notice and this permission notice shall be included in all
#     copies or substantial portions of the Software.
#
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#     IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#     AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#     LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#     OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#     SOFTWARE.

import subprocess
import re
import sys
import argparse
import time
import itertools

__all__ = [
    'get_connections',
    'show_connections',
    'show_ongoing_connections',
    'get_connections',
    'connect',
    'disconnect'
]

def display_usage(name=None):
    return """%s [-q] <command> [arg]

Options:
-q                                Suppress headers

Commands:
connect <connection name|#>       Open the given connection
disconnect <connection name|#>    Close the given connection
status <connection name|#>        Show connection status
ls                                List all the configured connections
connections                       Display ongoing connections


""" % name

GET_CONNECTIONS = """tell application "Viscosity"
  set result to {}
  repeat with con in connections
    set result to result & ((get name of con) & "|" & (get state of con))
  end repeat
  return result
end tell
"""

CONNECT = "tell application \"Viscosity\" to connect \"%s\""

DISCONNECT = "tell application \"Viscosity\" to disconnect \"%s\""

SPINNER = itertools.cycle(['-', '\\', '|', '/'])

def get_connections(args):
    output = subprocess.check_output([ 'osascript', '-e', GET_CONNECTIONS ]).decode('utf-8')
    return [(y[0], y[1][0], y[1][1]) for y in enumerate(sorted([x.split('|') for x in re.split(',\s*', output.strip('\n'))]), start=1)]

def show_connections(args):
    if not args.quiet:
        print ("%3s %-40s %s" % ('#', 'Connection name', 'Status'))
        print ('-' * 60)
    for item in get_connections(args):
        print ("%3d %-40s %s" % (item[0], item[1], item[2]))
    return 0

def show_ongoing_connections(args):
    if not args.quiet:
        print ("%3s %-40s" % ('#', 'Connection name'))
        print ('-' * 50)
    for item in get_connections(args):
        if item[2] == 'Connected':
            print ("%3d %-40s" % (item[0], item[1]))

def get_connection(args):
    if not args.connection:
        return None
    connections = get_connections(args)
    try:
        connection = connections[int(args.connection) - 1]
    except:
        connection = None
        for c in connections:
            if args.connection == c[1]:
                connection = c
                break
    return connection

def show_status(args):
    if not args.connection:
        print('%s: missing argument connection' % (sys.argv[0]))
        return 2
    connection = get_connection(args)
    if not connection:
        print('%s: connection %s not found' % (sys.argv[0], args.connection or ''))
        return 1
    print(connection[2])
    if connection[2] == 'Connected':
        return 10
    elif connection[2] == 'Disconnected':
        return 11
    elif connection[2] == 'Connecting':
        return 12
    else:
        return 13

def connect(args):
    if not args.connection:
        print('%s: missing argument connection' % (sys.argv[0]))
        return 2
    connection = get_connection(args)
    if not connection:
        print('%s: connection %s not found' % (sys.argv[0], args.connection or ''))
        return 1
    if connection[2] == 'Connected':
        print('%s: already connected to %s' % (sys.argv[0], connection[1]))
        return 1
    subprocess.check_output([ 'osascript', '-e', CONNECT % connection[1] ])
    sys.stdout.write('Connecting to %s...  ' % connection[1])
    sys.stdout.flush()
    while True:
        sys.stdout.write('\b')
        sys.stdout.write(next(SPINNER))
        sys.stdout.flush()

        time.sleep(0.1)
        connection = get_connection(args)
        if connection[2] != 'Connecting':
            sys.stdout.write('\b \n')
            sys.stdout.flush()
            print(connection[2])
            return 0

def disconnect(args):
    if not args.connection:
        print('%s: missing argument connection' % (sys.argv[0]))
        return 2
    connection = get_connection(args)
    if not connection:
        print('%s: connection %s not found' % (sys.argv[0], args.connection or ''))
        return 1
    if connection[2] == 'Disconnected':
        print('%s: already disconnected from %s' % (sys.argv[0], connection[1]))
        return 1
    subprocess.check_output([ 'osascript', '-e', DISCONNECT % connection[1] ])
    print('Disconnecting from %s...' % connection[1])
    return 0

CMDS = {
    'ls': show_connections,
    'list': show_connections,
    'connections': show_ongoing_connections,
    'status': show_status,
    'connect': connect,
    'disconnect': disconnect,
}

def main():
    parser = argparse.ArgumentParser(usage=display_usage(sys.argv[0]))
    parser.add_argument('--quiet', '-q', action='store_true')
    parser.add_argument('cmd', metavar='cmd', type=str, help='command', choices=CMDS.keys())
    parser.add_argument('connection', metavar='connection', type=str, nargs='?', help='command')
    args = parser.parse_args()
    cmd = CMDS.get(args.cmd)
    if cmd is not None:
        sys.exit(cmd(args))

if __name__ == "__main__":
    main()
