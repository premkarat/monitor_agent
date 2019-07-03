monitor
=======

Basic local monitoring tool.

monitor daemon runs on local host at every interval and collects the following information

* Total number of processes running in the system and the increase/decrease of the process count since the last monitoring.
* Top 5 processes by memory usage (list pid of the process, memory consumed and complete command line for the process).
* Percentage disk space usage in /var partition and the change since last monitoring round.
* Check the new contents of syslog for the keyword "ERROR" (case insensitive) since the last monitoring round.

Requirements
============

* Ensure passwordless SSH login is setup before executing the tool. A couple of references to setup it up.

    [thegeekstuff](http://www.thegeekstuff.com/2008/11/3-steps-to-perform-ssh-login-without-password-using-ssh-keygen-ssh-copy-id)

    [techmint](https://www.tecmint.com/ssh-passwordless-login-using-ssh-keygen-in-5-easy-steps/)

* Ensure passwordless sudo can be executed on the local host.

* python-pip should be availble on the target machine.


Deploy
======

Basic steps::

    1. git clone https://github.com/premkarat/monitor_agent.git
    2. cd monitor_agent

Running monitor
===============

    sudo monitor start <host-ip> <interval>
    sudo monitor stop

    host-ip: Valid IPv4 address
    interval: in seconds (greater than 0)
    start: as a daemon
    stop: the daemon

Example::

    To start as daemon

    sudo monitor.py start 127.0.0.1 10

    To stop the running daemon

    sudo monitor.py stop

Monitor result log
==================

monitor log is available under::

    /var/log/monitor.log

License
=======

This project is licensed under the MIT License

Authors
=======

* Prem Karat [prem(dot)karat(at)gmail(dot)com]
