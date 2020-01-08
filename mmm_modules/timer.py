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

import pygtk
pygtk.require('2.0')
import gtk, gobject, pango

import os
from time import time

cwd = os.path.normpath(os.path.join(os.path.split(__file__)[0], '..'))

if os.path.exists(os.path.join(cwd, 'mamamedia_icons')):
    # Local, no shared code, version
    mmmpath = cwd
    iconpath = os.path.join(mmmpath, 'mamamedia_icons')
else:
    propfile = os.path.expanduser("~/.sugar/default/org.worldwideworkshop.olpc.MMMPath")

    if os.path.exists(propfile):
        mmmpath = file(propfile, 'rb').read()
    else:
        mmmpath = cwd
    iconpath = os.path.join(mmmpath, 'icons')

from .utils import load_image

class TimerWidget (gtk.HBox):
    __gsignals__ = {'timer_toggle' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (bool,)),}
    def __init__ (self, bg_color="#DD4040", fg_color="#4444FF", lbl_color="#DD4040", can_stop=True):
        gtk.HBox.__init__(self)
        self.counter = gtk.EventBox()
        self.counter.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(bg_color))
        self.counter.set_size_request(120, -1)
        hb = gtk.HBox()
        self.counter.add(hb)
        self.lbl_time = gtk.Label()
        self.lbl_time.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(lbl_color))
        self.pack_start(self.lbl_time, False)
        self.time_label = gtk.Label("--:--")
        self.time_label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(fg_color))
        hb.pack_start(self.time_label, False, False, 5)
        self.prepare_icons()
        self.icon = gtk.Image()
        self.icon.set_from_pixbuf(self.icons[1])
        hb.pack_end(self.icon, False, False, 5)
        self.pack_start(self.counter, False)
        self.connect("button-press-event", self.process_click)
        self.start_time = 0
        self.timer_id = None
        self.finished = False
        self.can_stop = can_stop

    def set_label (self, label):
        self.lbl_time.set_label(label)

    def prepare_icons (self):
        self.icons = []
        self.icons.append(load_image(os.path.join(iconpath,"circle-x.svg")))
        self.icons.append(load_image(os.path.join(iconpath,"circle-check.svg")))


    def set_can_stop (self, can_stop):
        self.can_stop = can_stop
    
    def modify_bg(self, state, color):
        self.foreach(lambda x: x is not self.counter and x.modify_bg(state, color))

    def reset (self, auto_start=True):
        self.set_sensitive(True)
        self.finished = False
        self.stop()
        self.start_time = 0
        if auto_start:
            self.start()

    def start (self):
        if self.finished:
            return
        self.set_sensitive(True)
        self.icon.set_from_pixbuf(self.icons[0])
        if self.start_time is None:
            self.start_time = time()
        else:
            self.start_time = time() - self.start_time
        self.do_tick()
        if self.timer_id is None:
            self.timer_id = gobject.timeout_add(1000, self.do_tick)
        self.emit('timer_toggle', True)

    def stop (self, finished=False):
        if not self.can_stop and not finished:
            return
        self.icon.set_from_pixbuf(self.icons[1])
        if self.timer_id is not None:
            gobject.source_remove(self.timer_id)
            self.timer_id = None
            self.start_time = time() - self.start_time
        if not finished:
            self.time_label.set_text("--:--")
        else:
            self.finished = True
        self.emit('timer_toggle', False)
        
    def process_click (self, btn, event):
        if self.timer_id is None:
            self.start()
        else:
            self.stop()

    def is_running (self):
        return self.timer_id is not None

    def ellapsed (self):
        if self.is_running():
            return time() - self.start_time
        else:
            return self.start_time

    def is_reset (self):
        return not self.is_running() and self.start_time == 0

    def do_tick (self):
        t = time() - self.start_time
        if t > 5999:
            # wrap timer
            t = 0
            self.start_time = time()
        self.time_label.set_text("%0.2i:%0.2i" % (t/60, t%60))
        return True

    def _freeze (self):
        return (self.start_time, time(), self.finished, self.timer_id is None)

    def _thaw (self, obj):
        self.start_time, t, finished, stopped = obj
        if self.start_time is not None:
            if not stopped:
                self.start_time = t - self.start_time
                self.start()
                return
            self.start_time = time() - self.start_time
            self.do_tick()
        self.stop(finished)
