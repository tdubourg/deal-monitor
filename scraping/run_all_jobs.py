#!/usr/bin/python

import json
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../")))
from utils.shell_utils import execute_shell_and_get_stdout as execsh

DATA_PATH = "data/"
JOBS_FILEPATH = DATA_PATH + "jobs.json"

if __name__ == '__main__':
    f_jobs = open(JOBS_FILEPATH, "r")
    jobs = json.load(f_jobs)
    f_jobs.close()
    for j in jobs:
        # Scrap the data...
        execsh(
            "./scrap",
            [
                  "-o", DATA_PATH + j.name + "/items.json"
                , "-a", 'region="%s"' % j.region
                , "-a", 'keywords="%s"' % j.keywords
            ]
        )
        # Process the data...
        execsh("./process_data_for_job.py", [j.name])