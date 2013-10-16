#!/bin/sh

~/Downloads/adt-bundle-linux-x86/sdk/tools/android create project \
    --target 1 \
    --name dealmonitor_smssender \
    --path ~/Dropbox/code/deal-monitor/android/ \
    --activity MainActivity \
    --package com.dealmonitor.smssender
