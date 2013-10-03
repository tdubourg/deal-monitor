#!/usr/bin/python
 # -*- coding: utf-8 -*-

import sys

DBG = False

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.usage = "%prog [options] job_name"
    parser.add_option("-i", "--interval", dest="interval", default="60",
                      help="Monitoring interval, in seconds, for this job.",
                      metavar="interval")
    (options, args) = parser.parse_args()

    if DBG:
        print options
        print args

    if len(args) != 1:
        parser.print_help()
        exit()

    args2 = [args[0]]

    args2.append(options.interval)

