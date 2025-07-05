# Copyright 2007 World Wide Workshop Foundation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# If you find this activity useful or end up using parts of it in one of your
# own creations we would love to hear from you at info@WorldWideWorkshop.org !
#

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import logging

from .tube_helper import GAME_IDLE, GAME_STARTED, GAME_FINISHED, GAME_QUIT

#from sugar.graphics.icon import CanvasIcon

BUDDYMODE_CONTEST = 0
BUDDYMODE_COLLABORATION = 1

class BuddyPanel (Gtk.ScrolledWindow):
    def __init__ (self, mode=BUDDYMODE_CONTEST):
        super(BuddyPanel, self).__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.model = Gtk.ListStore(str, str, str, str)
        self.model.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.treeview = Gtk.TreeView()

        #col = gtk.TreeViewColumn(_("Icon"))
        #r = gtk.CellRendererText()
        #col.pack_start(r, True)
        #col.set_attributes(r, stock_id=0)
        #self.treeview.append_column(col)

        col = Gtk.TreeViewColumn("Buddy")
        r = Gtk.CellRendererText()
        col.pack_start(r, True)
        col.set_attributes(r, text=0)
        self.treeview.append_column(col)

        col = Gtk.TreeViewColumn("Status")
        r = Gtk.CellRendererText()
        col.pack_start(r, True)
        col.set_attributes(r, text=1)
        self.treeview.append_column(col)
        col.set_visible(mode == BUDDYMODE_CONTEST)

        col = Gtk.TreeViewColumn("Play Time")
        r = Gtk.CellRendererText()
        col.pack_start(r, True)
        col.set_attributes(r, text=2)
        self.treeview.append_column(col)
        col.set_visible(mode == BUDDYMODE_CONTEST)

        col = Gtk.TreeViewColumn("Joined at")
        r = Gtk.CellRendererText()
        col.pack_start(r, True)
        col.set_attributes(r, text=3)
        self.treeview.append_column(col)
        col.set_visible(mode == BUDDYMODE_COLLABORATION)
        
        self.treeview.set_model(self.model)

        self.add(self.treeview)
        self.show_all()

        self.players = {}

    def add_player (self, buddy, current_clock=0):
        """ Adds a player to the panel """
        op = buddy.object_path()
        if self.players.get(op) is not None:
            return

#        buddy_color = buddy.props.color
#        if not buddy_color:
#            buddy_color = "#000000,#ffffff"
#
#        icon = CanvasIcon(
#            icon_name='computer-xo',
#            xo_color=XoColor(buddy_color))
#
        nick = buddy.props.nick
        if not nick:
            nick = ""
        self.players[op] = (buddy, self.model.append([nick,
                                                      _('synchronizing'),
                                                      '',
                                                      '']))
        return nick

    def update_player (self, buddy, status, clock_running, time_ellapsed):
        """Since the current target build (432) does not fully support the contest mode, we are removing this for now. """
        #return
        op = buddy.object_path()
        if self.players.get(op, None) is None:
            logging.debug("Player %s not found" % op)
            return
        logging.debug(self.players[op])
        if status == GAME_STARTED[1]:
            stat = clock_running and _("Playing") or _("Paused")
        elif status == GAME_FINISHED[1]:
            stat = _("Finished")
        elif status == GAME_QUIT[1]:
            stat = _("Gave up")
        else:
            stat = _("Unknown")
        self.model.set_value(self.players[op][1], 1, stat)
        self.model.set_value(self.players[op][1], 2, _(
            "%i minutes") % (time_ellapsed / 60))
        self.model.set_value(self.players[op][1], 3, '%i:%0.2i' % (
            int(time_ellapsed / 60), int(time_ellapsed % 60)))
        return (self.model.get_value(self.players[op][1], 0), self.model.get_value(self.players[op][1], 1))
        
    def get_buddy_from_path (self, object_path):
        logging.debug("op = " + object_path)
        logging.debug(self.players)
        return self.players.get(object_path, None)
        
    def remove_player (self, buddy):
        op = buddy.object_path()
        if self.players.get(op) is None:
            return
        nick = buddy.props.nick
        if not nick:
            nick = ""
        self.model.remove(self.players[op][1])
        del self.players[op]
        return nick
