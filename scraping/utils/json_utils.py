# Note; This module is named json_utils and not 'json' not to 
# conflict with default's 'json' module that we're importing here
from json import load, dump

def load_json(filename):
	f = open(filename, 'r')
	obj = load(f)
	f.close()
	return obj

def write_json(data, filename):
	f = open(filename, "w+")
	res = dump(data, f)
	f.close()
	return res