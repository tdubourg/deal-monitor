#!/usr/bin/python
DBG = True

from utils.shell_utils import execute_shell_and_get_stdout
import json
import filter as f

# Launch scrapy job

# Analyze results, store the ones that fulfill the filters, send alerts for the ones that fulfill alert filters
# Load items
items_lbc_file = open("items_lbc.json")
items = json.load(items_lbc_file)

# Load filters
filters_file = open('filters.json')
filters_json_data = json.load(filters_file)
if DBG:
	print "Filters data:", filters_json_data

filters = [f.fromJSON(json_data) for json_data in filters_json_data]

if DBG:
	print "Filters!!", filters

for item in items:
	if DBG:
		print "Item=", item
	for f in filters:
		if DBG:
			print "Applying filter=", f
		if f.satisfies(item):
			if DBG:
				print "Item satisfies filter", f
			# Insert in db
			#TODO
		if f.satisfies_alert(item):
			if DBG:
				print "Item satisfies alert!"
			# Send alert
			#TODO
