"use strict"
// This module is a server for sending native notifications to connected Android devices.
// It can have a dynamic number of connected devices and will broadcast notifications to all of them

var DATA_PATH = "./data/"
var net = require("net");
var utils = require('./utils.js')
var p = utils.p
// var streamId = 0
var streams = {}
var server = null
var NOTIF_PREFIX = "@@notif@@\n"
var MESSAGE_TO_SEND_PREFIX = "@@msg@@"
var PHONE_NUM_PREFIX = "@@phone@@"
var END_OF_NOTIF_FRAME = "\n@@end@@\n\n"
var END_OF_IDENTIFICATION_FRAME = "@@end@@"

function start (port, ip) {
	console.log("ANDRONOTIF: Starting Android Service server")
	var server = net.createServer(function(stream) {
		console.log("ANDRONOTIF: New ANDROID server connection established.")
		var stop = false
		var device_name = false
		// var myStreamId = streamId++
		// streams[myStreamId] = stream
		stream.setTimeout(0);
		stream.setEncoding("utf8");

		function shutdown () {
			var stop = true
			if (device_name) { // If the device identified itself and was thus registered in the active streams, remove it on shutdown
				console.log("ANDRONOTIF: Closing connection to Android device", device_name)
				delete streams[device_name]
			} else {
				console.log("ANDRONOTIF: Closing connection to an unidentified Android device")
			}
		}

		stream.on("error", shutdown)
		stream.on("close", shutdown)
		stream.on("end", shutdown)

		var buffer = ""
		stream.addListener("data", function (data) {
			console.log("ANDRONOTIF: " + new Date().toString() + "New data packet came in:", data)
			buffer += data
			// If this is not a complete frame (the END_OF_IDENTIFICATION_FRAME is not present), then, just add to the buffer and
			// return from this callback
			if(-1 == data.indexOf(END_OF_IDENTIFICATION_FRAME)) {
				return
			}
			var frame = buffer
			buffer = "" // Emptying the buffer, so that it's ready to get the next start of a frame
			device_name = extract_device_name(frame)
			p("Device identified itself as", device_name, ". Registering it.")
			streams[device_name] = stream // Register the newly identified device as an active stream
			stream.write("ANDRONOTIF: " + new Date().toString() + ": ACK\n")
		});
	})
	server.listen(port, ip);
}

function extract_device_name (frame) {
	return frame.match(/^([.\s\S]+)@@end@@$/m)[1]
}
function write_to_device (device_name, message, recipient_phone_number) {
	var msgTxt = MESSAGE_TO_SEND_PREFIX + message
	var phoneTxt = PHONE_NUM_PREFIX + recipient_phone_number
	if (streams[device_name]) {
		var content = NOTIF_PREFIX + msgTxt + phoneTxt + END_OF_NOTIF_FRAME
		streams[device_name].write(content, function () {
			p("Content", content, "has been sent")
		})
		return true
	} else {
		p("No currently active streams for this device name.")
	}
	return false
}

function push_android_notif (alert) {
	var device_name = alert["device"]
	var txt_to_send_to_recipient = alert["message"]
	var recipient_phone_number = alert["recipient"]
	p("Pushing a new android notif to (", device_name, ", ", recipient_phone_number,")")
	if (device_name) {
		return write_to_device(device_name, txt_to_send_to_recipient, recipient_phone_number)
	}
	return false
}

exports.start = start
exports.push_android_notif = push_android_notif
