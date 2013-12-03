#!/usr/bin/python

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../")))
from utils.shell_utils import execute_shell_and_get_stdout_and_err as execsh
from common.config import *
from utils.json_utils import load_json
from utils import lock_job, unlock_job, load_file, write_file
from time import time
DBG = False
INFO = True

if __name__ == '__main__':
    jobs = load_json(JOBS_INFO_FILEPATH)
    if INFO:
        print "Loaded %s jobs" % len(jobs)
    if DBG:
        print jobs

    for j in jobs.values():
        # Note: We re-compute 'now' variable for each job, 
        # as running a job might take some time (or there might be a lot of them)!!
        now = int(time())
        jname = j["job_name"] # is going to be used a lot, will avoid dict' lookups
        JOB_DATA_PATH = DATA_PATH + jname + "/"
        if INFO:
            print "Job %s..." % jname
        
        lastrun_f_str = load_file(LAST_FULL_RUN_FILEPATH % jname)
        lastrun_p_str = load_file(LAST_PARTIAL_RUN_FILEPATH % jname)
        run = False
        # Note: If the lastrun strings are empty ("not lastrun_xxx") => has not ever been run
        # It's been enough time to run a full run of this job
        if not lastrun_f_str or (now - int(lastrun_f_str)) >= int(j["interval_full"]):
            run = True
            run_type = "full"
            lastrun_to_be_updated_fpath = LAST_FULL_RUN_FILEPATH % jname
        # It's only been enough time to run a partial run of this job
        elif not lastrun_p_str or (now - int(lastrun_p_str)) >= int(j["interval_partial"]):
            run = True
            run_type = "partial"
            lastrun_to_be_updated_fpath = LAST_PARTIAL_RUN_FILEPATH % jname
        if run is True:
            # In order not to delay runs of consecutives jobs because of
            # one long job, we fork their execution
            if DBG:
                print "Forking job %s... with run_type %s " % (jname, run_type)
            pid = os.fork()
            if pid == 0:
                # Wait for this job to be unlocked (in order not to corrupt data files)
                # and acquire the lock on this job
                if DBG:
                    print "Locking job from child process..."
                
                lock_job(jname)
                
                # This is happening! This job is kicking off, store this data in the appropriate file
                # Note: This is then used by the partial spider, to know where to stop crawling
                # for new items
                lastrun_start = None
                if run_type == RUN_TYPE_FULL:
                    f = open(LAST_FULL_RUN_START_FILEPATH % jname, "w+")
                elif run_type == RUN_TYPE_PARTIAL:
                    # Before overwriting this file, we're going to grab the value of the last run
                    # Indeed, in partial runs, we have to pass it to the scrapy spider as an argument
                    lastrun_f = load_file(LAST_FULL_RUN_START_FILEPATH % jname)
                    lastrun_p = load_file(LAST_PARTIAL_RUN_START_FILEPATH % jname)
                    lastrun_start = lastrun_f if lastrun_p and int(lastrun_f) > int(lastrun_p) else lastrun_p
                    
                    # Now you can overwrite it, bro
                    f = open(LAST_PARTIAL_RUN_START_FILEPATH % jname, "w+")
                else:
                    print "ERROR run_type is equal to", run_type, "which is an invalid value"
                    exit(1)
                f.write(str(int(time())))
                f.close()

                # Scrap the data...
                items_file_path = ITEMS_FILEPATH % jname
                # try:
                #     os.remove(items_file_path)
                # except OSError:
                #     pass # If the file did not exist, we do not care
                args = [
                      "-a", "export_path=../" + items_file_path
                    , "-a", 'region=%s' % j["region"]
                    , "-a", 'keywords=%s' % j["keywords"]
                    , "-a", 'category=%s' % j["category"]
                    , "-a", 'run=%s' % run_type
                ]
                if lastrun_start is not None:
                    args.extend(("-a", 'upto=%s' % lastrun_start))

                res = execsh("./scrap", args)
                if INFO:
                    print "\n\n ------------------- Result of scrapy execution: -------------- \n\n"
                    print "------------ STDOUT... ---------- "
                    print res[0]
                    print "============ STDERR... ========== "
                    print res[1]
                # Process the data...
                res = execsh("./process_data_for_job.py", [jname])
                if res[1]:
                    # stderr was not empty, something went wrong
                    print "\n\n ------------------------- Something went wrong during job data processing, here's the stderr: ------------------- \n\n"
                    print res[1]
                    print "\n\n------------- And here is stdout: ----------------------\n\n"
                    unlock_job(jname)
                    exit(1)
                if INFO:
                    print "\n\n------------- -Result of job processing execution: ----------------\n\n"
                    print res[0]
                # Update the lastrun's value
                write_file(lastrun_to_be_updated_fpath, str(int(time()))) # Using the job's end time
                # Release job's lockfile
                try:
                    unlock_job(jname)
                except OSError:
                    pass
        else:
            if DBG:
                print "Job's interval has not passed yet."
