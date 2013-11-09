#!/usr/bin/python

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../")))
from utils.shell_utils import execute_shell_and_get_stdout_and_err as execsh
from common.config import *
from utils.json_utils import load_json
from utils import lock_job, unlock_job
from time import time
DBG = True

if __name__ == '__main__':
    jobs = load_json(JOBS_INFO_FILEPATH)
    if DBG:
        print "Loaded %s jobs" % len(jobs)
        print jobs

    for j in jobs.values():
        # Note: We re-compute 'now' variable for each job, 
        # as running a job might take some time!!
        now = int(time())
        jname = j["job_name"] # is going to be used a lot, will avoid dict' lookups
        JOB_DATA_PATH = DATA_PATH + jname + "/"
        if DBG:
            print "Job %s..." % jname
        
        lastrun_f = LAST_RUN_FILEPATH % jname
        f = open(lastrun_f)
        lastrun_str = f.read()
        f.close()
        # If the string is empty (not lastrun_str) => has not ever been run
        if not lastrun_str or (now - int(lastrun_str)) >= int(j["interval"]):
            # In order not to delay runs of consecutives jobs because of
            # one long job, we fork their execution
            pid = os.fork()
            if pid == 0:
                # Wait for this job to be unlocked (in order not to corrupt data files)
                # and acquire the lock on this job
                if DBG:
                    print "Locking job from child process..."
                lock_job(jname)
                # Scrap the data...
                items_file_path = ITEMS_FILEPATH % jname
                os.remove(items_file_path)
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
                res = execsh("./process_data_for_job.py", [jname])
                if res[1]:
                    # stderr was not empty, something went wrong
                    print "Something went wrong during job data processing, here's the stderr:"
                    print res[1]
                    unlock_job(jname)
                    exit(1)
                if DBG:
                    print "Result of job processing execution:"
                    print res
                # Update the lastrun's value
                f = open(lastrun_f, "w+")
                f.write(str(int(time()))) # Using the job's end time
                f.close()
                # Release job's lockfile
                unlock_job(jname)
        else:
            if DBG:
                print "Job's interval has not passed yet."