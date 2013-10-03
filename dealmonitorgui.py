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
        self.builder.connect_signals(self)

    def run(self):
        l = Gtk.ListStore(str, str, float)
        l.append(('Vinz',))
        l.append(('Jhen',))
        l.append(('Chris',))
        l.append(('Shynne',))

        treeview = Gtk.TreeView()
        treeview.set_model(l)

        column = Gtk.TreeViewColumn()
        cell = Gtk.CellRendererText()
        column.pack_start(cell)
        column.add_attribute(cell,'text',0)
        treeview.append_column(column)

        treeview.get_selection().set_mode(Gtk.SELECTION_MULTIPLE)

        def print_selected(treeselection):
            (model,pathlist)=treeselection.get_selected_rows()
            print pathlist

        treeview.get_selection().connect('changed',lambda s: print_selected(s))
        self.builder.get_object("window1").show_all()
        Gtk.main()

    def on_window1_destroy(self, *args):
        Gtk.main_quit()


DealMonitor().run()
