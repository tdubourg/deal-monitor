#!/usr/bin/python
DBG = True

from utils.shell_utils import execute_shell_and_get_stdout
from utils.json_utils import load_json, write_json
from utils import lock_lockfile, release_lockfile, printe
import json
import filter as f
from bisect import bisect_left as bisect_search
import smtplib
import os, time, sys
import urllib2
from urllib import urlencode
from common.config import *

# Retrieving parameters from CLI
from optparse import OptionParser
parser = OptionParser()
parser.usage = "%prog [options] job_name\n/!\\WARNING/!\\ DO NOT EXECUTE MULTIPLE INSTANCES IN PARALLEL OF THIS SCRIPT IN THE SAME WORKING DIRECTORY"
(options, args) = parser.parse_args()

if len(args) != 1:
    parser.print_help()
    exit(0)

JOB_NAME = args[0]

job_infos = load_json(JOBS_INFO_FILEPATH)[args[0]]
ALERT_RECIPIENT = job_infos["email_recipient"]

DATA_JOB_PATH = DATA_PATH + JOB_NAME + "/"

# Customize job's specific paths
ITEMS_FILEPATH = ITEMS_FILEPATH % job_infos["job_name"]
FILTERS_FILEPATH = FILTERS_FILEPATH % job_infos["job_name"]
PASSED_ALERTS_FILEPATH = PASSED_ALERTS_FILEPATH % job_infos["job_name"]
PASSED_SMS_FILEPATH = PASSED_SMS_FILEPATH % job_infos["job_name"]
PASSED_MAILS_FILEPATH = PASSED_MAILS_FILEPATH % job_infos["job_name"]
FILTERED_ITEMS_FILEPATH = FILTERED_ITEMS_FILEPATH % job_infos["job_name"]

def send_alert(item, filter):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    to = ALERT_RECIPIENT
    gmail_user = open(ALERT_SMTP_USERNAME_FILEPATH).read().strip()
    gmail_pwd = open(ALERT_SMTP_PASSWD_FILEPATH).read().strip()
    # Opening SMTP connection...
    sc = smtplib.SMTP("smtp.gmail.com", 587)
    sc.ehlo()
    sc.starttls()
    sc.ehlo
    sc.login(gmail_user, gmail_pwd)
    # header = 'To: %s\nFrom: %s \nSubject: Bot Alert for Item %s [%s]\n' % (
    #     to
    #     , gmail_user
    #     , item["title"]
    #     , filter.name.encode("utf-8")
    # )
    #TODO: Improve this message...
    msg_plain = '\n BOT ALERT FOR %s \n %s \n %s \n\n' % (
          item["url"]
        , item["title"]
        , item["desc"]
    )
    msg = MIMEMultipart('alternative')
    msg['To'] = to
    msg['From'] = gmail_user
    msg['Subject'] = "Bot Alert for Item %s [%s]" % (item['title'], filter.name.encode('utf-8'))
    plaintext = MIMEText(msg_plain.encode('utf-8'),'plain','utf-8')
    msg.attach(plaintext)
    sc.sendmail(gmail_user, to, msg.as_string().encode('ascii'))
    sc.close()

    # Now, register this sent alert in the passed alerts:
    register_alerted(item)

def push_new_sms_contact(device_name, message, recipient):
    lock_lockfile(SMS_SERVER_LOCK_FILE)
    # We acquired the lock, we can now write to the json db file:
    sms_alerts = load_json(SMS_SERVER_ALERTS_FILE)
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
    release_lockfile(SMS_SERVER_LOCK_FILE)

def push_new_mail_contact(from_email, from_name, from_phone, message, item):
    headers = {
        # Mimeting Firefox's POST headers
          "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0"
        , "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        , "Accept-Language": "en-US,en;q=0.5"
        , "DNT": "1"
    }

    # First, grab the cookie form's, this is necessary to pass website's server-side validation:
    # And this will also allow us to check against website's specific encoding charset
    try:
        form_resp = urllib2.urlopen(urllib2.Request(
              "http://www2.leboncoin.fr/ar/form/0?ca=22_s&id=%s" % item["id"]
            , None
            , headers
        ))
        if form_resp.getcode() != 200:
            return False
    except:
        return False

    cookie = ""
    charset = ""
    for i in form_resp.info().items():
        name = i[0].lower()
        if name == "content-type":
            pos = i[1].find("charset")
            if pos is not -1:
                for i in i[1].split(";"):
                    i = i.strip()
                    if i.find("charset") == 0:
                        charset = i[8:] # for some bizarre reason, slicing notation beings at 1,not 0
        if name == "set-cookie":
            cookie = i[1]
    if DBG:
        print form_resp.info().items()
        print "Coooooookie", cookie
        print 'Encoooooooooooding', charset

    # Add the referer to the headers:
    headers["Referer"] = "http://www2.leboncoin.fr/ar/form/0?ca=22_s&id=%s" % item["id"]
    # And the cookie:
    headers["Cookie"] = cookie
    # And the content-type of a POST form
    headers["Content-Type"] = "application/x-www-form-urlencoded" + ("; " + charset if charset else "")
    # Now you can make the request
    if not charset:
        data = {
            "name": from_name,
            "email": from_email,
            "phone": from_phone,
            "body": message,
            "cc": 1
        }
    else:
        data = {
        "name": from_name.encode(charset),
        "email": from_email.encode(charset),
        "phone": from_phone.encode(charset),
        "body": message.encode(charset),
        "cc": 1
    }

    try:
        r = urllib2.urlopen(urllib2.Request(
              'http://www2.leboncoin.fr/ar/send/0?ca=22_s&id=%s' % item["id"]
            , urlencode(data)
            , headers
        ))
    except:
        return False

    if r.getcode() == 200:
        return True
    else:
        return False

def auto_contact_sms(item, f):
    sms_message = f.get_auto_contact_sms_message(item)
    push_new_sms_contact(
        f.data["sms_device_name"],
        sms_message,
        item["phone"]
    )
    register_sms_contacted(item)

def auto_contact_email(item, f):
    ret = push_new_mail_contact(
        f.data["mail_auto_contact_from_email"],
        f.data["mail_auto_contact_from_name"],
        f.data["mail_auto_contact_from_phone"],
        f.get_auto_contact_mail_message(item),
        item
    )

    # Now, register this sent alert in the passed alerts:
    if ret:
        return register_mail_contacted(item)
    else:
        return False

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
    return True

passed_alerts = dict([(int(id), o) for id,o in load_json(PASSED_ALERTS_FILEPATH).items()]) #TODO: Sort prices lists so that we can use bisect_search()?

passed_sms_contacts = dict([(int(id), o) for id,o in load_json(PASSED_SMS_FILEPATH).items()]) #TODO: Sort prices lists so that we can use bisect_search()?

passed_mail_contacts = dict([(int(id), o) for id,o in load_json(PASSED_MAILS_FILEPATH).items()]) #TODO: Sort prices lists so that we can use bisect_search()?

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
        if int(item["price"]) in item_passed_alerts:
            return True
        else:
            return False
    except KeyError:
        return False

def already_auto_contacted_sms(item):
    """
    Tells whether we already sent an auto contact for this item.
    """
    global passed_sms_contacts
    if not has_valid_price(item):
        return True # In case the price is not valid, the following comparisons won't work, just don't send an alert to something without a valid price
    try:
        item_passed_sms = passed_sms_contacts[item["id"]]
        if int(item["price"]) in item_passed_sms:
            return True
        else:
            return False
    except KeyError:
        return False

def already_auto_contacted_email(item):
    """
    Tells whether we already sent an auto contact for this item.
    """
    global passed_mail_contacts
    if not has_valid_price(item):
        return True # In case the price is not valid, the following comparisons won't work, just don't send an alert to something without a valid price
    try:
        item_passed_mail = passed_mail_contacts[item["id"]]
        if int(item["price"]) in item_passed_mail:
            return True
        else:
            return False
    except KeyError:
        return False

# Launch scrapy job

# Analyze results, store the ones that fulfill the filters, send alerts for the ones that fulfill alert filters
# Load items
items = load_json(ITEMS_FILEPATH)

already_existing_items = dict([(int(o["id"]), o) for o in load_json(FILTERED_ITEMS_FILEPATH)])

# Load filters
filters_json_data = load_json(FILTERS_FILEPATH)
if DBG:
    print "Filters data:", filters_json_data

filters = [f.fromJSON(json_data) for json_data in filters_json_data]

if DBG:
    print "Filters!!", filters

output_items = {}
for f in filters:
    output_items[f.name] = []

new_items = []

for item in items.values():
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

            if f.satisfies_auto_contact_sms(item):
                if DBG:
                    print "Item satisfies auto_contact_sms for filter", f
                if not already_auto_contacted_sms(item):
                    # Auto contact
                    auto_contact_sms(item, f)
                else:
                    if DBG:
                        print "Item satisfies auto_contact_sms for filter but already contacted", f
            if f.satisfies_auto_contact_email(item):
                if DBG:
                    print "Item satisfies auto_contact_email for filter", f
                if not already_auto_contacted_email(item):
                    # Auto contact
                    if not auto_contact_email(item, f):
                        printe("ERROR, something went wrong while trying to auto_contact_email")
                else:
                    if DBG:
                        print "Item satisfies auto_contact_email for filter but already contacted", f


f_existing_items = open(FILTERED_ITEMS_FILEPATH, 'w+')
total_items = already_existing_items.values() + new_items

# While debugging, use pretty-printed JSON, when not debugging anymore, use compact notation for space efficiency
if DBG:
    json_repr = json.dumps(total_items, indent=4, separators=(',', ': '))
else:
    json_repr = json.dumps(total_items)
f_existing_items.write(json_repr)
f_existing_items.close()
                
write_json(passed_alerts, PASSED_ALERTS_FILEPATH)
                
write_json(passed_mail_contacts, PASSED_MAILS_FILEPATH)
                
write_json(passed_sms_contacts, PASSED_SMS_FILEPATH)
