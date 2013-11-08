#!/usr/bin/python
 # -*- coding: utf-8 -*-

import sys, json

DBG = False
DATA_PATH = "data/"
JOBS_FILEPATH = DATA_PATH + "jobs.json"

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.usage = "%prog [options] job_name"
    parser.add_option("-i", "--interval", dest="interval", default="60",
                      help="Monitoring interval, in seconds, for this job.",
                      metavar="interval")
    parser.add_option("-r", "--region", dest="region", default="",
                      help="Region.",
                      metavar="rhone_alpes")
     # TODO: Allow multiple queries to be specified for a given job?
    parser.add_option("-q", "--query", dest="query",
                      help="The query / keywords to scrap products about",
                      metavar="my über object I want")
    (options, args) = parser.parse_args()

    if DBG:
        print options
        print args

    if len(args) != 1:
        parser.print_help()
        exit()

    args2 = [args[0]]

    f_jobs = open(JOBS_FILEPATH, "r")
    jobs = json.load(f_jobs)
    f_jobs.close()

    jobs.append(
        {
              "job_name": args[0]
            , "interval": options.interval
            , "keywords": options.query # TODO: Allow multiple sets of keywords to be specified?
            , "region": options.region
        }
    )

    f_jobs = open(JOBS_FILEPATH, "w+")
    json.dump(jobs, f_jobs)
    f_jobs.close()

    print "Sucessfully saved the new job."
