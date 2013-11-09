#!/usr/bin/python
DBG = True

from utils.shell_utils import execute_shell_and_get_stdout
import json
import filter as f
from bisect import bisect_left as bisect_search
import smtplib
import os, time, sys
import urllib2
from urllib import urlencode

# Retrieving parameters from CLI
from optparse import OptionParser
parser = OptionParser()
parser.usage = "%prog [options] job_name\n/!\\WARNING/!\\ DO NOT EXECUTE MULTIPLE INSTANCES IN PARALLEL OF THIS SCRIPT IN THE SAME WORKING DIRECTORY"
(options, args) = parser.parse_args()

if len(args) != 1:
    parser.print_help()
    exit(0)

JOB_NAME = args[0]

f_jobs_data = open(DATA_PATH + "jobs.json", 'r')
job_infos = json.load(f_jobs_data)[JOB_NAME]
f_jobs_data.close()

DATA_PATH = "data/"
DATA_JOB_PATH = DATA_PATH + JOB_NAME + "/"

# JOB-only data files
ITEMS_FILEPATH = DATA_JOB_PATH + "items.json"
FILTERED_ITEMS_FILEPATH = DATA_JOB_PATH + "filtered_items.json"
ALERT_RECIPIENT_FILEPATH = job_infos["email_recipient"]
FILTERS_FILEPATH = DATA_JOB_PATH + 'filters.json'

# Global ones
PASSED_ALERTS_FILEPATH = DATA_PATH + "passed_alerts.json"
PASSED_SMS_FILEPATH = DATA_PATH + "sms_alerts_py.json"
PASSED_MAILS_FILEPATH = DATA_PATH + "passed_mails_autocontacts.json"
SMS_SERVER_LOCK_FILE = DATA_PATH + "sms_alerts.lock"
SMS_SERVER_ALERTS_FILE = DATA_PATH + "sms_alerts.json"
ALERT_SMTP_USERNAME_FILEPATH = DATA_PATH + "alert_smtp_username.txt"
ALERT_SMTP_PASSWD_FILEPATH = DATA_PATH + "alert_smtp_password.txt"

def send_alert(item, filter):
    to = open(ALERT_RECIPIENT_FILEPATH).read().strip()
    gmail_user = open(ALERT_SMTP_USERNAME_FILEPATH).read().strip()
    gmail_pwd = open(ALERT_SMTP_PASSWD_FILEPATH).read().strip()
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
    #TODO: Improve this message...
    msg = header + '\n BOT ALERT FOR %s \n %s \n %s \n\n' % (item["url"].encode("utf-8"), item["title"].encode("utf-8"), item["desc"].encode("utf-8"))
    sc.sendmail(gmail_user, to, msg)
    sc.close()

    # Now, register this sent alert in the passed alerts:
    register_alerted(item)

def push_new_sms_contact(device_name, message, recipient):
    while os.path.isfile(SMS_SERVER_LOCK_FILE):
        print "Sms alerts file locked, waiting for lock to be released..."
        time.sleep(0.1) # Wait a bit for the lock to be released...
    # Lock released! Acquire it:
    flock = open(SMS_SERVER_LOCK_FILE, 'w')
    flock.close()
    # We acquired the lock, we can now write to the json db file:
    f_sms_alerts = open(SMS_SERVER_ALERTS_FILE, "r")
    sms_alerts = json.load(f_sms_alerts)
    f_sms_alerts.close()
    sms_alerts.append(
        {
            "device": device_name,
            "message": message,
            "recipient": recipient,
            "sent": False
        }
    )
    f_sms_alerts = open(SMS_SERVER_ALERTS_FILE, "w+")
    json.dump(sms_alerts, f_sms_alerts)
    f_sms_alerts.close()
    # Alerts updated, release the lock:
    os.remove(SMS_SERVER_LOCK_FILE)

def push_new_mail_contact(from_email, from_name, from_phone, message, item):
    data = {
        "name": from_name,
        "email": from_email,
        "phone": from_phone,
        "body": message,
        "cc": 1
    }

    urllib2.urlopen(urllib2.Request(
        'http://leboncoin//ar/send/0?ca=22_s&id=%s' % item["id"],
        urlencode(data),
        {
            # Mimeting Firefox's POST headers
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0", 
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Referer": "http://www2.leboncoin.fr/ar/form/0?ca=22_s&id=%s" % item["id"],
            "Content-Type": "application/x-www-form-urlencoded"
        }
    ))

def auto_contact(item, filter):
    push_new_sms_contact(
        filter.data["sms_device_name"],
        filter.get_auto_contact_sms_message(item),
        item["phone"]
    )
    register_sms_contacted(item)
    
    push_new_mail_contact(
        filter.data["mail_auto_contact_from_email"],
        filter.data["mail_auto_contact_from_name"],
        filter.data["mail_auto_contact_from_phone"],
        filter.get_auto_contact_mail_message(item),
        item
    )

    # Now, register this sent alert in the passed alerts:
    register_mail_contacted(item)

def register_alerted(item):
    global passed_alerts
    try:
        item_passed_alerts = passed_alerts[item["id"]]
    except KeyError:
        item_passed_alerts = []
        passed_alerts[item["id"]] = item_passed_alerts

    item_passed_alerts.append(item["price"])

def register_sms_contacted(item):
    global passed_sms_contacts
    try:
        item_passed_contacts = passed_sms_contacts[item["id"]]
    except KeyError:
        item_passed_contacts = []
        passed_sms_contacts[item["id"]] = item_passed_contacts

    item_passed_contacts.append(item["price"])

def register_mail_contacted(item):
    global passed_mail_contacts
    try:
        item_passed_contacts = passed_mail_contacts[item["id"]]
    except KeyError:
        item_passed_contacts = []
        passed_mail_contacts[item["id"]] = item_passed_contacts

    item_passed_contacts.append(item["price"])

f_passed_alerts = open(PASSED_ALERTS_FILEPATH, 'r')
passed_alerts = dict([(int(id), o) for id,o in json.load(f_passed_alerts).items()]) #TODO: Sort prices lists so that we can use bisect_search()?
f_passed_alerts.close()

f_passed_sms = open(PASSED_SMS_FILEPATH, 'r')
passed_sms_contacts = dict([(int(id), o) for id,o in json.load(f_passed_sms).items()]) #TODO: Sort prices lists so that we can use bisect_search()?
f_passed_sms.close()

f_passed_mails = open(PASSED_MAILS_FILEPATH, 'r')
passed_mail_contacts = dict([(int(id), o) for id,o in json.load(f_passed_mails).items()]) #TODO: Sort prices lists so that we can use bisect_search()?
f_passed_mails.close()

def has_valid_price(item):
    if item["price"] is None:
        return False
    price = int(item["price"])
    if price >= 0:
        return True


def already_alerted(item):
    """
    Tells whether we already sent an alert for this item, with its current price.
    We consider we have the right to send an alert again is the price changed compared to the previous alert sent for this item.
    """
    global passed_alerts
    if not has_valid_price(item):
        return True # In case the price is not valid, the following comparisons won't work, just don't send an alert to something without a valid price
    try:
        item_passed_alerts = passed_alerts[item["id"]]
        if item["price"] in item_passed_alerts:
            return True
        else:
            return False
    except KeyError:
        return False

def already_auto_contacted(item):
    """
    Tells whether we already sent an auto contact for this item.
    """
    global passed_sms_contacts, passed_mail_contacts
    if not has_valid_price(item):
        return True # In case the price is not valid, the following comparisons won't work, just don't send an alert to something without a valid price
    try:
        item_passed_sms = passed_sms_contacts[item["id"]]
        if item["price"] in item_passed_sms:
            return True
        else:
            return False
    except KeyError:
        return False

    try:
        item_passed_mail = passed_mail_contacts[item["id"]]
        if item["price"] in item_passed_mail:
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
filters_file = open(FILTERS_FILEPATH)
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

            if f.satisfies_auto_contact(item):
                if DBG:
                    print "Item satisfies auto_contact for filter", f
                if not already_auto_contacted(item):
                    # Auto contact
                    auto_contact(item, f)
                else:
                    if DBG:
                        print "Item satisfies auto_contact for filter but already contacted", f


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
                
f_passed_mails = open(PASSED_MAILS_FILEPATH, 'w+')
json.dump(passed_mail_contacts, f_passed_mails)
f_passed_mails.close()
                
f_passed_sms = open(PASSED_SMS_FILEPATH, 'w+')
json.dump(passed_sms_contacts, f_passed_sms)
f_passed_sms.close()