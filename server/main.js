"use strict"

var server = require('./server.js')
var utils = require('./utils.js')
server.start(8080, utils.getLocalPublicIpAddress(["eth0", "wlan0"]))