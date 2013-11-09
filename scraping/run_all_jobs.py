#!/usr/bin/python

import json
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../")))
from utils.shell_utils import execute_shell_and_get_stdout_and_err as execsh

DATA_PATH = "data/"
JOBS_FILEPATH = DATA_PATH + "jobs.json"
DBG = True

if __name__ == '__main__':
    f_jobs = open(JOBS_FILEPATH, "r")
    jobs = json.load(f_jobs)
    f_jobs.close()
    if DBG:
        print "Loaded %s jobs" % len(jobs)
        print jobs

    for j in jobs.values():
        if DBG:
            print "Job %s..." % j["job_name"]
        # Scrap the data...
        items_file_path = DATA_PATH + j["job_name"] + "/items.json"
        os.remove(DATA_PATH + j["job_name"] + "/items.json")
        res = execsh(
            "./scrap",
            [
                  "-o", "../" + items_file_path
                , "-a", 'region=%s' % j["region"]
                , "-a", 'keywords=%s' % j["keywords"]
                , "-a", 'category=%s' % j["category"]
            ]
        )
        if DBG:
            print "Result of scrapy execution:"
            print res
        # Process the data...
        res = execsh("./process_data_for_job.py", [j["job_name"]])
        if DBG:
            print "Result of job processing execution:"
            print res