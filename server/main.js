"use strict"

var DATA_PATH = "data/"
var server = require('./server.js')
var utils = require('./utils.js')
var p = utils.p
var fs = require('fs')
var alerts

var writing_to_alerts_file = false

var check_alerts = function () {

}

var ALERTS_FILE_PATH = DATA_PATH + "sms_alerts.json"


var ALERTS_LOCK_FILE = DATA_PATH + "sms_alerts.lock"

var	lock_alerts = function () {
	fs.writeFileSync(ALERTS_LOCK_FILE, "pouet")
}

var unlock_alerts = function (argument) {
	fs.unlinkSync(ALERTS_LOCK_FILE)
}

var load_alerts = function () {
	p("Loading alerts...")
	return JSON.parse(fs.readFileSync(DATA_PATH + "sms_alerts.json").toString())
}

var wait_for_alerts_lock = function (callback) {
	if (fs.existsSync(ALERTS_LOCK_FILE)) {
		p("Alerts file is locked, waiting for lock to be released...")
		setTimeout(function () {
			wait_for_alerts_lock(callback)
		}, 100) // Try again in 100 ms
	} else {
		callback()
	}
}

var update_alerts = function () {
	p("Updating alerts...")
	fs.writeFileSync(ALERTS_FILE_PATH, JSON.stringify(alerts))
}

var send_alert = function (event, filename) {
	p("Received event alert", event, " for file", filename)
	if (writing_to_alerts_file) {
		p("We're just currently updating it...")
		return
	};
	if (event == 'change') {
		p("Waiting for alerts lock...")
		wait_for_alerts_lock(function () {
			p("Locking alerts...")
			lock_alerts()
			alerts = load_alerts()
			var to_be_updated = false
			for (var i = alerts.length - 1; i >= 0; i--) {
				if (!alerts[i].sent) {
					if(server.push_android_notif(alerts[i])) {
						// If things went well, update the alert, else, do not, so that we try again next time
						to_be_updated = true
						alerts[i].sent = true
					}
				};
			};
			writing_to_alerts_file = true
			if (to_be_updated) {
				update_alerts()
			};
			writing_to_alerts_file = false
			unlock_alerts()
			p("Unlocking alerts...")
		});
		
	};
}

fs.watch(ALERTS_FILE_PATH, send_alert);
var ipaddr = utils.getLocalPublicIpAddress(["eth0", "p2p1", "wlan0"])
p("Starting server on local ip=", ipaddr)
server.start(8080, ipaddr)
// a = setInterval(check_alerts, 10000) // Check for new alerts to be sent every 10 seconds