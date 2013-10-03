#!/usr/bin/python
 # -*- coding: utf-8 -*-

import gi
gi.require_version("Gtk", "3.0")
# from gi.repository import Gtk,GdkPixbuf,GObject,Pango,Gdk
from gi.repository import Gtk

# import gtk -- this doesn't work
class DealMonitor (object):

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("dealmonitor.glade")
        self.box_categ = self.builder.get_object("box_categ")
        self.builder.connect_signals(self)

    def on_window1_destroy(self, widget, data=None):
        Gtk.main_quit()

    def run(self):
        l = Gtk.ListStore(str, int)
        l.append(('Vinz',0))
        l.append(('Jhen',1))
        l.append(('Chris',2))
        l.append(('Shynne',3))

        treeview = Gtk.TreeView()
        treeview.set_model(l)

        self.box_categ.add(treeview)

        column = Gtk.TreeViewColumn()
        cell = Gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell,'text',0)
        treeview.append_column(column)

        treeview.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        def print_selected(treeselection):
            (model,pathlist)=treeselection.get_selected_rows()
            print pathlist

        treeview.get_selection().connect('changed',lambda s: print_selected(s))
        self.builder.get_object("window1").show_all()
        Gtk.main()




DealMonitor().run()
