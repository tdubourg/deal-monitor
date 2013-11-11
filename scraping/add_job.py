#!/usr/bin/python
 # -*- coding: utf-8 -*-

import sys, json
from utils.shell_utils import execute_shell_and_get_stdout

DBG = False
DATA_PATH = "data/"
JOBS_FILEPATH = DATA_PATH + "jobs.json"

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.usage = "%prog [options] job_name"
    parser.add_option("-I", "--interval-full", dest="interval_full", default="60",
                      help="Interval, in seconds, between two full runs of this job (from end to next start).",
                      metavar="interval_in_seconds")
    parser.add_option("-i", "--interval-partial", dest="interval_partial", default="60",
                      help="Interval, in seconds, between two runs of a partial scraping of the job (from end of job to next job's start).",
                      metavar="interval_in_seconds")
    parser.add_option("-e", "--email_recipient", dest="email_recipient", default="",
                      help="The email recipient for bot alerts (email address that will receive emails if alerts are activated and filters are matched).",
                      metavar="you@youremail.tld")
     # TODO: Allow multiple regions to be specified for a given job?
    parser.add_option("-r", "--region", dest="region", default="",
                      help="Region.",
                      metavar="rhone_alpes")
     # TODO: Allow multiple categories to be specified for a given job?
    parser.add_option("-c", "--category", dest="category",
                      help="The category",
                      metavar="consoles_consoles_jeux_video")
     # TODO: Allow multiple queries to be specified for a given job?
    parser.add_option("-q", "--query", dest="query",
                      help="The query / keywords to scrap products about",
                      metavar="my uber object I want")
    (options, args) = parser.parse_args()

    if DBG:
        print options
        print args

    if len(args) != 1:
        parser.print_help()
        exit()

    args2 = [args[0]]

    options.interval_full = int(options.interval_full)
    options.interval_partial = int(options.interval_partial)

    if options.interval_full <= options.interval_partial:
        print "Error, --intervall-full must be lower than --interval-partial as a partial run will be run BETWEEN full runs"
        exit(1)
    
    f_jobs = open(JOBS_FILEPATH, "r")
    jobs = json.load(f_jobs)
    f_jobs.close()

    if args[0] in jobs:
      print "Error, a job with this exact name already exists. Please choose a different name."

    jobs[args[0]] = {
              "job_name": args[0]
            , "interval_full": options.interval_full
            , "interval_partial": options.interval_partial
            , "keywords": options.query # TODO: Allow multiple sets of keywords to be specified?
            , "region": options.region
            , "category": options.category
            , "email_recipient": options.email_recipient
        }

    execute_shell_and_get_stdout("cp", ["data/empty_job_base", "data/%s" %  args[0], "-R"])

    f_jobs = open(JOBS_FILEPATH, "w+")
    json.dump(jobs, f_jobs)
    f_jobs.close()

    print "Sucessfully saved the new job."
