#!/usr/bin/python
# Author: Prem Karat [prem.karat@gmail.com]
# MIT License
#


import atexit
import subprocess
import datetime
import os
import re
import sys
import signal
import socket
import time


def usage():
    print("usage:")
    print("\t sudo montior.py start <host-ip> <interval>")
    print("\t sudo montior.py stop\n")
    print("\t <host-ip>: Valid IPv4 address")
    print("\t <interval>: in seconds. Minimum 1 sec")
    print("\t start: Run as daemon")
    print("\t stop: Stop daemon")


def check_usage():
    if len(sys.argv) != 4 and len(sys.argv) != 2:
        usage()
        raise SystemExit("invalid Usage")

    if sys.argv[1] != 'start' and sys.argv[1] != 'stop':
        usage()
        raise SystemExit('unknown argument %s' % sys.argv[1])


def getargs():
    ipaddr = sys.argv[2]
    interval = sys.argv[3]

    try:
        socket.inet_pton(socket.AF_INET, ipaddr)
    except socket.error:
        usage()
        raise SystemExit('invalid IP address')

    try:
        interval = int(interval)
    except ValueError:
        usage()
        raise SystemExit('invalid interval')

    if not interval:
        usage()
        raise SystemExit('interval should be miminum 1 second')

    return (ipaddr, interval)


def run_as_daemon(pidfile, stdout, stderr, stdin='/dev/null'):
    if os.path.exists(pidfile):
        raise RuntimeError('already Running')
    try:
        if os.fork() > 0:
            raise SystemExit(0)
    except OSError:
        raise RuntimeError('fork 1 failed')

    os.umask(0)
    os.setsid()

    try:
        if os.fork() > 0:
            raise SystemExit(0)
    except OSError:
        raise RuntimeError('fork 2 failed')

    # Replace file descriptors for stdin, stdout, and stderr
    with open(stdin, 'rb', 0) as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(stdout, 'ab', 0) as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    with open(stderr, 'ab', 0) as f:
        os.dup2(f.fileno(), sys.stderr.fileno())

    # Write the PID file
    with open(pidfile, 'w') as f:
        f.write(str(os.getpid()))

    # Arrange to have the PID file removed on exit/signal
    atexit.register(lambda: os.remove(pidfile))

    # Signal handler for termination (required)
    def sigterm_handler(signo, frame):
        raise SystemExit(1)

    signal.signal(signal.SIGTERM, sigterm_handler)


def get_process_diff(prev_nprocs):
    PROCCMD = "sudo ps --no-headers -ef | wc -l"
    output = subprocess.check_output(PROCCMD, shell=True)
    cur_nprocs = int(output)
    diff = cur_nprocs - prev_nprocs
    sys.stdout.write(
        'current number of process: %s and increase/decrease: %d\n' % (
            cur_nprocs, diff
        )
    )

    return cur_nprocs


def get_top5_process_by_mem_use():
    MEMCMD = "sudo ps --no-headers -eo pid,pmem,comm | sort -rk2 | head -n5"
    output = subprocess.check_output(MEMCMD, shell=True)
    sys.stdout.write('top 5 process by memory usage:\t\n')
    for line in output.splitlines():
        sys.stdout.write('\t%s\n' % line.strip())


def get_var_partition_disk_usage_diff(prev_dusage):
    DISKCMD = "sudo df -h /var | tail -n1"
    output = subprocess.check_output(DISKCMD, shell=True)
    match = re.findall(r'.*(\d+)%.*', output)
    if match:
        cur_dusage = int(match[0])
        diff = cur_dusage - prev_dusage
        sys.stdout.write(
            'disk space usage in /var: %s%% and increase/decrease: %d%%\n' % (
                match[0], diff
            )
        )

        return cur_dusage


def check_new_errors_in_syslog(filepos):
    SYSLOG = '/var/log/syslog'
    with open(SYSLOG, 'r') as f:
        f.seek(filepos)
        for line in f:
            if 'error' in line.lower():
                sys.stdout.write('%s\n' % line.strip())
        filepos = f.tell()
        sys.stdout.write('\n')

    return filepos


def main(host, interval):
    nprocs = 0
    dusage = 0
    filepos = 0

    while True:
        ts = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        sys.stdout.write('%s\n' % ts)
        sys.stdout.write('-------------------\n')

        # Get the total increase/decrease in process
        nprocs = get_process_diff(nprocs)

        # Get top 5 pmem process
        get_top5_process_by_mem_use()

        # Get /var disk usage informatoin
        dusage = get_var_partition_disk_usage_diff(dusage)

        # Incremental check for ERROR (case insensitive) in syslog
        filepos = check_new_errors_in_syslog(filepos)

        # Flush I/O buffers
        sys.stdout.flush()
        sys.stderr.flush()

        time.sleep(interval)


if __name__ == '__main__':
    check_usage()

    PIDFILE = 'monitor.pid'
    LOGFILE = '/var/log/monitor.log'

    if sys.argv[1] == 'start':
        ipaddr, interval = getargs()
        try:
            run_as_daemon(PIDFILE, stdout=LOGFILE, stderr=LOGFILE)
        except RuntimeError:
            raise SystemExit('Failed to run as daemon')

        main(ipaddr, interval)

    elif sys.argv[1] == 'stop':
        if os.path.exists(PIDFILE):
            with open(PIDFILE) as f:
                os.kill(int(f.read()), signal.SIGTERM)
        else:
            raise SystemExit('monitor daemon not running')
