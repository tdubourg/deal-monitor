"use strict"
// This module is a server for sending native notifications to connected Android devices.
// It can have a dynamic number of connected devices and will broadcast notifications to all of them

var DATA_PATH = "./data/"
var net = require("net");
var alerts = require(DATA_PATH + "sms_alerts.json")
var streamId = 0
var streams = {}
var server = null
var NOTIF_PREFIX = "@@notif@@\n"
var PHONE_NUM_PREFIX = "url: "

function start (port, ip) {
	console.log("ANDRONOTIF: Starting Android Service server")
	var server = net.createServer(function(stream) {
		var stop = false
		var myStreamId = streamId++
		streams[myStreamId] = stream
		stream.setTimeout(0);
		stream.setEncoding("utf8");

		stream.addListener("connect", function(){
			console.log("ANDRONOTIF: New ANDROID server connection established (device number", myStreamId, ").")
		// Debug purpose : If you want to debug the notifications, uncomment that code
		// 	var i = 0
		// 	a = setInterval(function () {
		// 		console.log("Sending a new notif", i++, "to Android device number", myStreamId)
		// 		try {
		// 			stream.write(NOTIF_PREFIX + "Hi Android device "+ myStreamId + "!\r\n")
		// 		} catch(e) {
		// 			shutdown()
		// 		}
		// 	}, 3000)
		});

		function shutdown () {
			console.log("ANDRONOTIF: Closing connection to Android device number", myStreamId)
			var stop = true
			// clearInterval(a)
			delete streams[myStreamId]
		}

		stream.on("error", shutdown)
		stream.on("close", shutdown)
		stream.on("end", shutdown)

		var buffer = ""
		stream.addListener("data", function (data) {
			console.log("ANDRONOTIF: " + new Date().toString() + "New data packet came in:", data)
			stream.write("ANDRONOTIF: " + new Date().toString() + ": ACK\r\n")
		});
	})
	server.listen(port, ip);
}

function write_to_device (streamId, message, recipient_phone_number) {
	var msgTxt = MESSAGE_TO_SEND_PREFIX + message
	var phoneTxt = "\n" + PHONE_NUM_PREFIX + recipient_phone_number
	streams[streamId].write(NOTIF_PREFIX + msgTxt + phoneTxt)
}

function push_android_notif (txt_to_send_to_recipient, recipient_phone_number) {
	for(var streamId in streams) {
		write_to_device(streamId, txtToSendToRecipient, recipient_phone_number)
	}
}

exports.start = start
exports.push_android_notif = push_android_notif
