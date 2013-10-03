#!/usr/bin/python
 # -*- coding: utf-8 -*-

import gtk


class DealMonitor (object):

    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("dealmonitor.glade")
        self.builder.connect_signals(self)

    def run(self):
        self.builder.get_object("window1").show_all()
        gtk.main()

    def on_window1_destroy(self, *args):
        gtk.main_quit()


DealMonitor().run()
