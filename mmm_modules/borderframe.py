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

from gi.repository import Gtk, GObject, Pango, Gdk

BORDER_LEFT = 1
BORDER_RIGHT = 2
BORDER_TOP = 4
BORDER_BOTTOM = 8
BORDER_VERTICAL = BORDER_TOP | BORDER_BOTTOM
BORDER_HORIZONTAL = BORDER_LEFT | BORDER_RIGHT
BORDER_ALL = BORDER_VERTICAL | BORDER_HORIZONTAL
BORDER_ALL_BUT_BOTTOM = BORDER_HORIZONTAL | BORDER_TOP
BORDER_ALL_BUT_TOP = BORDER_HORIZONTAL | BORDER_BOTTOM
BORDER_ALL_BUT_LEFT = BORDER_VERTICAL | BORDER_RIGHT

class BorderFrame (Gtk.EventBox):
    def __init__ (self, border=BORDER_ALL, size=5, bg_color=None, border_color=None):
        Gtk.EventBox.__init__(self)
        if border_color is not None:
            self.set_border_color(Gdk.color_parse(border_color))
        self.inner = Gtk.EventBox()
        if bg_color is not None:
            self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse(bg_color))
        align = Gtk.Alignment.new(1.0,1.0,1.0,1.0)
        self.padding = [0,0,0,0]
        if (border & BORDER_TOP) != 0:
            self.padding[0] = size
        if (border & BORDER_BOTTOM) != 0:
            self.padding[1] = size
        if (border & BORDER_LEFT) != 0:
            self.padding[2] = size
        if (border & BORDER_RIGHT) != 0:
            self.padding[3] = size
        align.set_padding(*self.padding)
        align.add(self.inner)
        align.show()
        self.inner.show()
        Gtk.EventBox.add(self, align)
        self.stack = []

    def set_border_color (self, color):
        Gtk.EventBox.modify_bg(self, Gtk.StateType.NORMAL, color)

    def modify_bg (self, state, color):
        self.inner.modify_bg(state, color)

    def add (self, widget):
        self.stack.append(widget)
        self.inner.add(widget)
        # FIXME REVIEW NOTE : RECHECK
        
        self.inner.show_now()

    def push (self, widget):
        widget.set_size_request(*self.inner.child.get_size_request())
        self.inner.remove(self.inner.child)
        self.add(widget)

    def pop (self):
        if len(self.stack) > 1:
            self.inner.remove(self.inner.child)
            del self.stack[-1]
            self.inner.add(self.stack[-1])

    def get_child (self):
        return self.inner.child

    def set_size_request (self, w, h):
        self.inner.set_size_request(w,h)
        super(BorderFrame, self).set_size_request(w+self.padding[0]+self.padding[2], h+self.padding[1]+self.padding[3])

    def show (self):
        self.show_all()

#    def get_allocation (self):
#        return self.inner.get_allocation()

