#!/usr/bin/python
DBG = True

from utils.shell_utils import execute_shell_and_get_stdout
import json
import filter as f
from bisect import bisect_left as bisect_search
import smtplib

DATA_PATH = "data/"
ITEMS_FILEPATH = DATA_PATH + "items_lbc.json"
FILTERED_ITEMS_FILEPATH = DATA_PATH + "filtered_items.json"
PASSED_ALERTS_FILEPATH = DATA_PATH + "passed_alerts.json"

def send_alert(item, filter):
	to = open(DATA_PATH + "alert_recipient.txt").read().strip()
	gmail_user = open(DATA_PATH + "alert_smtp_username.txt").read().strip()
	gmail_pwd = open(DATA_PATH + "alert_smtp_password.txt").read().strip()
	# Opening SMTP connection...
	sc = smtplib.SMTP("smtp.gmail.com", 587)
	sc.ehlo()
	sc.starttls()
	sc.ehlo
	sc.login(gmail_user, gmail_pwd)
	header = 'To: %s\nFrom: %s \nSubject: Bot Alert for Item %s [%s]\n' % (
		to
		, gmail_user
		, item["title"].encode("utf-8")
		, filter.name.encode("utf-8")
	)
	msg = header + '\n BOT ALERT FOR %s \n %s \n %s \n\n' % (item["url"].encode("utf-8"), item["title"].encode("utf-8"), item["desc"].encode("utf-8"))
	sc.sendmail(gmail_user, to, msg)
	sc.close()

	# Now, register this sent alert in the passed alerts:
	register_alerted(item)

def register_alerted(item):
	global passed_alerts
	try:
		item_passed_alerts = passed_alerts[item["id"]]
	except KeyError:
		item_passed_alerts = []
		passed_alerts[item["id"]] = item_passed_alerts

	item_passed_alerts.append(item["price"])

f_passed_alerts = open(PASSED_ALERTS_FILEPATH, 'r')
passed_alerts = dict([(int(id), o) for id,o in json.load(f_passed_alerts).items()]) #TODO: Sort prices lists so that we can use bisect_search()?
f_passed_alerts.close()

def already_alerted(item):
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
items_lbc_file = open(ITEMS_FILEPATH)
items = json.load(items_lbc_file)
items_lbc_file.close()

already_existing_items = dict([(int(o["id"]), o) for o in json.load(open(FILTERED_ITEMS_FILEPATH))])

# Load filters
filters_file = open(DATA_PATH + 'filters.json')
filters_json_data = json.load(filters_file)
filters_file.close()
if DBG:
	print "Filters data:", filters_json_data

filters = [f.fromJSON(json_data) for json_data in filters_json_data]

if DBG:
	print "Filters!!", filters

output_items = {}
for f in filters:
	output_items[f.name] = []

new_items = []

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
				# output_items[f.name].append(item)
				new_items.append(item) # TODO improve that to insert by filter, as the commented line above

			if f.satisfies_alert(item):
				if DBG:
					print "Item satisfies alert for filter", f
				if not already_alerted(item):
					# Send alert
					send_alert(item, f)
				else:
					if DBG:
						print "Item satisfies alert for filter but already alerted", f

f_existing_items = open(FILTERED_ITEMS_FILEPATH, 'w+')
total_items = already_existing_items.values() + new_items

# While debugging, use pretty-printed JSON, when not debugging anymore, use compact notation for space efficiency
if DBG:
	json_repr = json.dumps(total_items, indent=4, separators=(',', ': '))
else:
	json_repr = json.dumps(total_items)
f_existing_items.write(json_repr)
f_existing_items.close()
				
f_passed_alerts = open(PASSED_ALERTS_FILEPATH, 'w+')
json.dump(passed_alerts, f_passed_alerts)
f_passed_alerts.close()
