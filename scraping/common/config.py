# Global data files paths
DATA_PATH = "data/"
# Paths that have to be customized to a given job
PASSED_ALERTS_FILEPATH = DATA_PATH + "%s/passed_alerts.json"
PASSED_SMS_FILEPATH = DATA_PATH + "%s/sms_alerts_py.json"
PASSED_MAILS_FILEPATH = DATA_PATH + "%s/passed_mails_autocontacts.json"
FILTERED_ITEMS_FILEPATH = DATA_PATH + "%s/filtered_items.json"
FILTERS_FILEPATH = DATA_PATH + "%s/filters.json"
ITEMS_FILEPATH = DATA_PATH + "%s/items.json"

SMS_SERVER_LOCK_FILE = DATA_PATH + "sms_alerts.lock"
SMS_SERVER_ALERTS_FILE = DATA_PATH + "sms_alerts.json"
ALERT_SMTP_USERNAME_FILEPATH = DATA_PATH + "alert_smtp_username.txt"
ALERT_SMTP_PASSWD_FILEPATH = DATA_PATH + "alert_smtp_password.txt"

JOBS_INFO_FILENAME = "jobs.json"

JOBS_INFO_FILEPATH = DATA_PATH + JOBS_INFO_FILENAME
LAST_RUN_FILEPATH = DATA_PATH + "%s/lastrun.txt"
LOCK_FILENAME = "locked"