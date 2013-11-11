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
# File storing the last time we've ended a full run of a given job...
LAST_FULL_RUN_FILEPATH = DATA_PATH + "%s/lastrun_full.txt"
# File storing the last time we've started a full run of a given job...
LAST_FULL_RUN_START_FILEPATH = DATA_PATH + "%s/lastrun_full_start.txt"
# File storing the last time we've started a partial run of a given job...
LAST_PARTIAL_RUN_START_FILEPATH = DATA_PATH + "%s/lastrun_partial_start.txt"
# File storing the last time we've ended a partial run of a given job...
LAST_PARTIAL_RUN_FILEPATH = DATA_PATH + "%s/lastrun_partial.txt"
# Filename of the lock file used for a job's data lock
LOCK_FILENAME = "locked"

RUN_TYPE_FULL = "full"
RUN_TYPE_PARTIAL = "partial"
