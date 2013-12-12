import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../")))
from common.config import DATA_PATH, LOCK_FILENAME
from time import sleep, time

DBG = False

def wait_for_file_disappearance(filename, timeout):
	started_at = time()
	while os.path.isfile(filename):
                if DBG:
                    print "Waiting for disappearance of", filename, ", already ", time() - started_at, "passed, timeout is", timeout
		if timeout and (time() - started_at) >= timeout:
			return False
		sleep(0.1) # Wait a bit for the lock to be released...
        return True

def lock_lockfile(fname, blocking=True, timeout=None):
        """
        Will try to lock the file before the given timeout
        
        It will return True if it was able to acquire the lock (or forced it).
        
        If blocking=True, it will suspend the current process until it can the file lock
        
        If no timeout is specified, will try forever until it manages to lock the file.
        If a timeout is specified, it will try until the given timeout is reached
        and return False if it times out before being able to acquire the lock.
        """
	res = True
	if blocking:
		res = wait_for_file_disappearance(fname, timeout)
        # Lock released! Acquire it:
	f = open(fname, "w+")
	f.close()
	return res

def unlock_job(jobname):
	return release_lockfile(DATA_PATH + jobname + "/" + LOCK_FILENAME)

def release_lockfile(fname):
	os.remove(fname)

def lock_job(jobname, blocking=True, timeout=None):
	return lock_lockfile(DATA_PATH + jobname + "/" + LOCK_FILENAME, blocking, timeout)

def load_file(fname):
	f = open(fname, 'r')
	res = f.read()
	f.close()
	return res

def write_file(fname, content):
	"""
	If the file already exists, it will be overwritten
	"""
	f = open(fname, "w+")
	res = f.write(content)
	f.close()
	return res

def printe(s):
	print >> sys.stderr, s
