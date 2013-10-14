#!/usr/bin/python
DBG = True

from utils.shell_utils import execute_shell_and_get_stdout
import json
import filter as f
from bisect import bisect_left as bisect_search
import smtplib

def send_alert(item, filter):
	to = 'trolldu26@gmail.com'
	gmail_user = 'notimportant2014@gmail.com'
	gmail_pwd = 'thisaccountdoesnotmatter'
	# Opening SMTP connection...
	sc = smtplib.SMTP("smtp.gmail.com", 587)
	sc.ehlo()
	sc.starttls()
	sc.ehlo
	sc.login(gmail_user, gmail_pwd)
	header = 'To: %s\nFrom: %s \nSubject: Bot Alert for Item %s [%s]\n' % (
		to
		, gmail_user
		, item["title"]
		, filter.name
	)
	print header
	msg = header + '\n this is test msg from mkyong.com \n\n'
	sc.sendmail(gmail_user, to, msg)
	print 'done!'
	sc.close()

passed_alerts = dict([(int(id), o) for id,o in json.load(open("passed_alerts.json")).items()]) #TODO: Sort prices lists so that we can use bisect_search()?

def already_alerted(self, item):
	"""
	Tells whether we already sent an alert for this item, with its current price.
	We consider we have the right to send an alert again is the price changed compared to the previous alert sent for this item.
	"""
	global passed_alerts
	try:
		item_passed_alerts = passed_alerts[item["id"]]
		if item["price"] in item_passed_alerts:
			return True
		else:
			return False
	except KeyError:
		return False

# Launch scrapy job

# Analyze results, store the ones that fulfill the filters, send alerts for the ones that fulfill alert filters
# Load items
items_lbc_file = open("items_lbc.json")
items = json.load(items_lbc_file)

already_existing_items = dict([(int(o["id"], o) for o in json.load(open("filtered_items.json"))])

# Load filters
filters_file = open('filters.json')
filters_json_data = json.load(filters_file)
if DBG:
	print "Filters data:", filters_json_data

filters = [f.fromJSON(json_data) for json_data in filters_json_data]

if DBG:
	print "Filters!!", filters

output_items = {}
for f in filters:
	output_items[f.name] = []


for item in items:
	item["id"] = item_id = int(item["id"])
	
	try:
		existing_item = already_existing_items[item_id]
	except KeyError:
		existing_item = None

	if DBG:
		print "Item=", item
	for f in filters:
		if DBG:
			print "Applying filter=", f
		if f.satisfies(item):
			if DBG:
				print "Item satisfies filter", f
			if existing_item is not None: # This item was already inserted
				 # Did it change?
				 if existing_item != item:
				 	# Then update it
				 	already_existing_items[item["id"]] = item
			else:
				# New satisfying item, insert in db
				output_items[f.name].append(item)

			if f.satisfies_alert(item) and not already_alerted(item):
				if DBG:
					print "Item satisfies alert for filter", f
				# Send alert
				send_alert(item, f)
