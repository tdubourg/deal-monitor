"use strict"

// var events = require('events');
var DATA_PATH = "./data/"
var net = require("net");
var alerts = require(DATA_PATH + "sms_alerts.json")
// var eventEmitter = new events.EventEmitter();
function start (port) {
	console.log(new Date(), "JSSERV: Starting server")
	var server = net.createServer(function(stream) {

		stream.setTimeout(0);
		stream.setEncoding("utf8");

		stream.addListener("connect", function(){
			console.log("JSSERV: ", new Date(), "New connection to server.")
		});

		var buffer = ""
		stream.addListener("data", function (data) {
			console.log("JSSERV: Data received")
		});

		stream.addListener("end", function(){
			console.log("JSSERV: ", "Connection closed.")
			stream.end();
		});
	});

	server.listen(port);
}

exports.start = start
