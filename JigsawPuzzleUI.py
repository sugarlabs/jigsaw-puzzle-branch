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

from mamamedia_modules import BorderFrame, BORDER_ALL_BUT_BOTTOM, BORDER_ALL_BUT_LEFT
from mamamedia_modules import utils
from mamamedia_modules import CategorySelector
from mamamedia_modules import ImageSelectorWidget
from mamamedia_modules import LanguageComboBox
from mamamedia_modules import TimerWidget
from mamamedia_modules import BuddyPanel, BUDDYMODE_COLLABORATION

from mamamedia_modules import GAME_IDLE, GAME_STARTED, GAME_FINISHED

from JigsawPuzzleWidget import JigsawPuzzleWidget

import logging
from mamamedia_modules import json

#from gettext import gettext as _

# Colors from Rich's UI design

COLOR_FRAME_OUTER = "#B7B7B7"
COLOR_FRAME_GAME = "#FF0099"
COLOR_FRAME_THUMB = COLOR_FRAME_GAME
COLOR_FRAME_CONTROLS = "#FFFF00"
COLOR_BG_CONTROLS = "#66CC00"
COLOR_FG_BUTTONS = (
    (gtk.STATE_NORMAL,"#CCFF99"),
    (gtk.STATE_ACTIVE,"#CCFF99"),
    (gtk.STATE_PRELIGHT,"#CCFF99"),
    (gtk.STATE_SELECTED,"#CCFF99"),
    (gtk.STATE_INSENSITIVE,"#CCFF99"),
    )
COLOR_BG_BUTTONS = (
    (gtk.STATE_NORMAL,"#027F01"),
    (gtk.STATE_ACTIVE,"#014D01"),
    (gtk.STATE_PRELIGHT,"#016D01"),
    (gtk.STATE_SELECTED,"#027F01"),
    (gtk.STATE_INSENSITIVE,"#CCCCCC"),
    )

def prepare_btn(btn, w=-1, h=-1):
    for state, color in COLOR_BG_BUTTONS:
        btn.modify_bg(state, gtk.gdk.color_parse(color))
    c = btn.get_child()
    if c is not None:
        for state, color in COLOR_FG_BUTTONS:
            c.modify_fg(state, gtk.gdk.color_parse(color))
    else:
        for state, color in COLOR_FG_BUTTONS:
            btn.modify_fg(state, gtk.gdk.color_parse(color))
    if w>0 or h>0:
        btn.set_size_request(w, h)
    return btn


class JigsawPuzzleUI (BorderFrame):
    __gsignals__ = {'game-state-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,))}
    
    def __init__(self, parent):
        super(JigsawPuzzleUI, self).__init__(border_color=COLOR_FRAME_OUTER)

        self._shuffling = False

        self._parent = parent
        # We want the translatables to be detected but not yet translated
        global _
        _ = lambda x: x
        self.labels_to_translate = []

        self._state = GAME_IDLE
        self._readonly = False
        self._join_time = 0

        inner_table = gtk.Table(2,2,False)
        self.add(inner_table)

        self.game = JigsawPuzzleWidget()
        self.game.connect('picked', self.piece_pick_cb, False)
        self.game.connect('dropped', self.piece_drop_cb)
        self.game.connect('solved', self.do_solve)
        self.game.connect('cutter-changed', self.cutter_change_cb)
        self.game.show()

        # panel is a holder for everything on the left side down to (not inclusive) the language dropdown
        panel = gtk.VBox()

        # Logo image
        img_logo = gtk.Image()
        img_logo.set_from_file("icons/logo.png")
        img_logo.show()
        panel.pack_start(img_logo, expand=False, fill=False)


        # Control panel has the image controls
        control_panel = BorderFrame(border=BORDER_ALL_BUT_BOTTOM,
                                    border_color=COLOR_FRAME_CONTROLS,
                                    bg_color=COLOR_BG_CONTROLS)
        control_panel_box = gtk.VBox()

        scrolled = gtk.ScrolledWindow()
        scrolled.props.hscrollbar_policy = gtk.POLICY_NEVER
        scrolled.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        scrolled.show()
        scrolled.add_with_viewport(control_panel_box)
        scrolled.child.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(COLOR_BG_CONTROLS))
        control_panel.add(scrolled)

        spacer = gtk.Label()
        spacer.set_size_request(-1, 5)
        control_panel_box.pack_start(spacer, expand=False, fill=False)

        btn_box = gtk.Table(2,5,False)
        btn_box.set_col_spacings(5)
        btn_box.set_row_spacings(5)
        btn_box.attach(gtk.Label(), 0,1,0,2)
        # Cut type buttons
        self.btn_basic_cut = gtk.ToggleButton()
        i = gtk.Image()
        i.set_from_pixbuf(utils.load_image(os.path.join('icons', 'cut_basic.svg')))
        self.btn_basic_cut.set_image(i)
        btn_box.attach(prepare_btn(self.btn_basic_cut), 1,2,0,1,0,0)
        self.btn_simple_cut = gtk.ToggleButton()
        i = gtk.Image()
        i.set_from_pixbuf(utils.load_image(os.path.join('icons', 'cut_simple.svg')))
        self.btn_simple_cut.set_image(i)
        btn_box.attach(prepare_btn(self.btn_simple_cut), 2,3,0,1,0,0)
        self.btn_classic_cut = gtk.ToggleButton()
        i = gtk.Image()
        i.set_from_pixbuf(utils.load_image(os.path.join('icons', 'cut_classic.svg')))
        self.btn_classic_cut.set_image(i)
        # Link cutter buttons with cutter styles
        self.btn_cut_mapping = {
            'basic': self.btn_basic_cut,
            'simple': self.btn_simple_cut,
            'classic': self.btn_classic_cut,
            }
        for k,v in self.btn_cut_mapping.items():
            v.connect("released", self.set_piece_cut, k)

        btn_box.attach(prepare_btn(self.btn_classic_cut), 3,4,0,1,0,0)
        # Difficulty level buttons
        self.btn_easy_level = gtk.ToggleButton()
        i = gtk.Image()
        i.set_from_pixbuf(utils.load_image(os.path.join('icons', 'level_easy.svg')))
        self.btn_easy_level.set_active(True)
        self.btn_easy_level.set_image(i)
        btn_box.attach(prepare_btn(self.btn_easy_level), 1,2,1,2,0,0)
        self.btn_normal_level = gtk.ToggleButton()
        i = gtk.Image()
        i.set_from_pixbuf(utils.load_image(os.path.join('icons', 'level_normal.svg')))
        self.btn_normal_level.set_image(i)
        btn_box.attach(prepare_btn(self.btn_normal_level), 2,3,1,2,0,0)
        self.btn_hard_level = gtk.ToggleButton()
        i = gtk.Image()
        i.set_from_pixbuf(utils.load_image(os.path.join('icons', 'level_hard.svg')))
        self.btn_hard_level.set_image(i)
        # Link level buttons with levels
        self.btn_level_mapping = {
            3: self.btn_easy_level,
            5: self.btn_normal_level,
            8: self.btn_hard_level,
            }
        for k,v in self.btn_level_mapping.items():
            v.connect("released", self.set_level, k)

        btn_box.attach(prepare_btn(self.btn_hard_level), 3,4,1,2,0,0)
        
        btn_box.attach(gtk.Label(), 4,5,0,2)
        control_panel_box.pack_start(btn_box, expand=False)

        self.thumb = ImageSelectorWidget(frame_color=COLOR_FRAME_THUMB,
                                         prepare_btn_cb=prepare_btn,
                                         method=utils.RESIZE_PAD,
                                         image_dir="images",
                                         parent=self._parent)
        self.thumb.connect("category_press", self.do_select_category)
        self.thumb.connect("image_press", self.do_shuffle)
        control_panel_box.pack_start(self.thumb, expand=False)

        spacer = gtk.Label()
        spacer.set_size_request(-1, 5)
        control_panel_box.pack_start(spacer, expand=False, fill=False)
        
        # The game control buttons
        btn_box = gtk.Table(3,4,False)
        btn_box.set_row_spacings(2)
        btn_box.attach(gtk.Label(), 0,1,0,4)
        btn_box.attach(gtk.Label(), 2,3,0,4)
        self.btn_solve = prepare_btn(gtk.Button(" "), 200)
        self.labels_to_translate.append([self.btn_solve, _("Solve")])
        self.btn_solve.connect("clicked", self.do_solve)
        btn_box.attach(self.btn_solve, 1,2,0,1,0,0)
        self.btn_shuffle = prepare_btn(gtk.Button(" "), 200)
        self.labels_to_translate.append([self.btn_shuffle, _("Shuffle")])
        self.btn_shuffle.connect("clicked", self.do_shuffle)
        btn_box.attach(self.btn_shuffle, 1,2,1,2,0,0)
        self.btn_add = prepare_btn(gtk.Button(" "), 200)
        self.labels_to_translate.append([self.btn_add, _("My Picture")])
        self.btn_add.connect("clicked", self.do_add_image)
        btn_box.attach(self.btn_add, 1,2,2,3,0,0)
        self.btn_hint = prepare_btn(gtk.ToggleButton(" "), 200)
        self.labels_to_translate.append([self.btn_hint, _("Board Hint")])
        self.btn_hint.connect("clicked", self.do_show_hint)
        btn_box.attach(self.btn_hint, 1,2,3,4,0,0)
        control_panel_box.pack_start(btn_box, False)
        self.control_panel_box = control_panel_box

        # Control panel end
        panel.pack_start(control_panel, expand=True, fill=True)

        inner_table.attach(panel, 0,1,0,1,0)

        self.game_box = BorderFrame(border_color=COLOR_FRAME_GAME)
        self.game_box.add(self.game)

        self.notebook = gtk.Notebook()
        self.notebook.show()
        self.notebook.props.show_border = False
        self.notebook.props.show_tabs = False
        self.notebook.append_page(self.game_box)
        inner_table.attach(self.notebook, 1,2,0,1)

        lang_combo = prepare_btn(LanguageComboBox('org.worldwideworkshop.olpc.JigsawPuzzle'))
        lang_combo.connect('changed', self.do_select_language)
        # Push the gettext translator into the global namespace
        del _
        lang_combo.install()
        lang_box = BorderFrame(bg_color=COLOR_BG_CONTROLS,
                               border_color=COLOR_FRAME_CONTROLS)
        hbox = gtk.HBox(False)
        vbox = gtk.VBox(False)
        vbox.pack_start(lang_combo, padding=8)
        hbox.pack_start(vbox, padding=8)
        lang_box.add(hbox)
        inner_table.attach(lang_box, 0,1,1,2,gtk.FILL, gtk.FILL)

        timer_box = BorderFrame(border=BORDER_ALL_BUT_LEFT,
                                bg_color=COLOR_BG_CONTROLS,
                                border_color=COLOR_FRAME_CONTROLS)
        timer_hbox = gtk.HBox(False)
        self.timer = TimerWidget(bg_color=COLOR_BG_BUTTONS[0][1],
                                 fg_color=COLOR_FG_BUTTONS[0][1],
                                 lbl_color=COLOR_BG_BUTTONS[1][1])
        self.timer.set_sensitive(False)
        self.timer.set_border_width(3)
        self.labels_to_translate.append((self.timer, _("Time: ")))
        timer_hbox.pack_start(self.timer, False, padding=8)
        self.timer.connect('timer_toggle', self.timer_toggle_cb)

        self.msg_label = gtk.Label()
        self.msg_label.show()
        timer_hbox.pack_start(self.msg_label, True)
        
        self.do_select_language(lang_combo)
        
        self.buddy_panel = BuddyPanel(BUDDYMODE_COLLABORATION)
        self.buddy_panel.show()

        if not parent._shared_activity:
            self.do_select_category(self)

        self.set_contest_mode(False)

        # Assert consistent state
        self.cutter_change_cb(None, self.game.get_cutter(), self.game.get_target_pieces_per_line())

    def set_message (self, msg, frommesh=False):
        if frommesh and self.get_game_state() != GAME_STARTED:
            return
        self.msg_label.set_label(msg)

    def _set_control_area (self, *args):
        """ The controls area below the logo needs different actions when in contest mode,
        and also if we are the contest initiators or not. """
        if self._contest_mode:
            if self.get_game_state() > GAME_IDLE or not self.is_initiator():
                self.set_readonly()
            if self.get_game_state() <= GAME_IDLE:
                if self.is_initiator():
                    if self.timer.is_reset():
                        self.set_message(_("Select image and press Start Game..."))
                    else:
                        self.set_game_state(GAME_STARTED)
                else:
                    self.set_message(_("Waiting for Puzzle image to be chosen..."))
                    self.set_button_translation(self.btn_add, "Buddies")
                    self.btn_add.get_child().set_label(_("Buddies"))

    def set_readonly (self):
        """ In collaborative mode, after an image is selected and the game started you can not change much """
        self.thumb.set_readonly(True)
        self.set_button_translation(self.btn_shuffle, "Game Running")
        self.btn_shuffle.get_child().set_label(_("Game Running"))
        self.btn_shuffle.set_sensitive(False)
        for b in self.btn_cut_mapping.values() + self.btn_level_mapping.values():
            if not (b.get_active() and self.is_initiator()):
                b.set_sensitive(False)
        self._readonly = True

    def is_readonly (self):
        return self._readonly

    def is_initiator (self):
        return self._parent.initiating

    @utils.trace
    def timer_toggle_cb (self, evt, running):
        logging.debug("Timer running: %s" % str(running))
        if self._contest_mode and running:
            self.set_game_state(GAME_STARTED)
        self._send_status_update()

    def set_contest_mode (self, mode):
        if getattr(self, '_contest_mode', None) != mode:
            self.timer.set_can_stop(not bool(mode))
            self._contest_mode = bool(mode)
            self._set_control_area()
            if self._contest_mode:
                self.btn_solve.set_sensitive(False)
                #self.set_button_translation(self.btn_solve, "Give Up")
                #self.btn_solve.get_child().set_label(_("Give Up"))
                self.set_button_translation(self.btn_shuffle, "Start Game")
                self.btn_shuffle.get_child().set_label(_("Start Game"))

    @utils.trace
    def set_game_state (self, state, force=False):
        if state[0] > self._state[0] or force:
            self._state = state
            self.emit('game-state-changed', state[0])
            self._set_control_area()
            if state == GAME_STARTED:
                self.set_button_translation(self.btn_add, "Buddies")
                self.btn_add.get_child().set_label(_("Buddies"))
                if self._contest_mode:
                    if self.is_initiator():
                        self._send_game_update()
            self._send_status_update()
        elif state[0] <= GAME_STARTED[0] and self._contest_mode and not self.is_initiator():
            c = gtk.gdk.Cursor(gtk.gdk.WATCH)
            self.window.set_cursor(c)
            

    def get_game_state (self):
        return self._state

    def do_select_category (self, o, *args):
        if isinstance(o, CategorySelector):
            self.thumb.set_image_dir(args[0])
            #if not self.thumb.category.has_images():
            #    self.do_add_image(None)
        else:
            if self.game.get_parent():
                s = CategorySelector(_("Choose a Subject"), self.thumb.get_image_dir(), path="images")
                s.connect("selected", self.do_select_category)
                s.show()
                self.game_box.push(s)
                s.grab_focus()
            else:
                self.game_box.pop()


    @utils.trace
    def _show_game (self, pixbuf=None, reshuffle=True):
        if not self.game.get_parent():
            self.game_box.pop()
            while gtk.events_pending():
                gtk.main_iteration(False)
        c = gtk.gdk.Cursor(gtk.gdk.WATCH)
        self.window.set_cursor(c)
        if not self.game.prepare_image(pixbuf, reshuffle):
            self._shuffling = False
            return
        self._shuffling = False
        self.window.set_cursor(None)
        #self.game.randomize()

    def do_shuffle (self, o, *args):
        #if self.thumb.has_image():
        #    print ("FN", self.thumb.category.filename)
        if self._contest_mode and \
             self.get_game_state() == GAME_IDLE and \
             self.game.is_running() and \
             o == self.btn_shuffle and \
             self.timer.is_reset():
            # Start
            logging.debug('do_shuffle')
            self.timer.start()
        elif self.thumb.has_image():
            if not self._shuffling:
                logging.debug('do_shuffle start')
                self.timer.stop()
                self._shuffling = True
                self._show_game(self.thumb.get_image())
                self.timer.reset(False)
                self.do_show_hint(self.btn_hint)
        
    def do_solve (self, o, *args):
        if not self.game.is_running():
            return
        if not self.game.get_parent():
            self.game_box.pop()
        self.game.solve()
        self.timer.stop(True)
        if self._contest_mode:
            self.set_game_state(GAME_FINISHED)
            self.set_message(_("Puzzle Solved!"))
            self.control_panel_box.foreach(self.control_panel_box.remove)
            lbl = gtk.Label(_("Press Stop on the Toolbar to Exit Activity!"))
            lbl.modify_font(pango.FontDescription("bold 9"))
            lbl.set_line_wrap(True)
            lbl.set_justify(gtk.JUSTIFY_CENTER)
            lbl.set_size_request(200, -1)
            lbl.show()
            self.control_panel_box.pack_start(lbl, True)
            

    def do_add_image (self, o, *args):
        if self._contest_mode and self.get_game_state() >= GAME_STARTED:
            # Buddy Panel
            if not self.buddy_panel.get_parent():
                #self.timer.stop()
                self.game_box.push(self.buddy_panel)
            else:
                self.game_box.pop()
        else:
            self.thumb.add_image()

    @utils.trace
    def do_select_language (self, combo, *args):
        self.selected_lang_details = combo.translations[combo.get_active()]
        self.refresh_labels()

    def do_show_hint (self, o, *args):
        self.game.show_hint(o.get_active())

    def set_button_translation (self, btn, translation):
        for i in range(len(self.labels_to_translate)):
            if self.labels_to_translate[i][0] == btn:
                self.labels_to_translate[i][1] = translation
                break

    def refresh_labels (self, first_time=False):
        self._parent.set_title(_("Jigsaw Puzzle Activity"))
        for lbl in self.labels_to_translate:
            if isinstance(lbl[0], gtk.Button):
                lbl[0].get_child().set_label(_(lbl[1]))
            else:
                lbl[0].set_label(_(lbl[1]))
        if not self.game.get_parent() and not first_time:
            self.game_box.pop()
            if self.notebook.get_current_page() == 1:
                m = self.do_lesson_plan
            else:
                m = self.do_select_category
            m(self)

    def set_piece_cut (self, btn, cutter, *args):
        if self.is_readonly():
            return
        self.game.set_cutter(cutter)
        if self.game.is_running():
            self.do_shuffle(btn)

    def cutter_change_cb (self, o, cutter, tppl):
        # tppl = target pieces per line
        for c,b in self.btn_cut_mapping.items():
            if c == cutter:
                b.set_sensitive(True)
                b.set_active(True)
            else:
                b.set_active(False)
        for c,b in self.btn_level_mapping.items():
            if c == tppl:
                b.set_sensitive(True)
                b.set_active(True)
            else:
                b.set_active(False)

    def set_level (self, btn, level, *args):
        if self.is_readonly():
            return
        self.game.set_target_pieces_per_line(level)
        if self.game.is_running():
            self.do_shuffle(btn)

    def piece_pick_cb (self, o, piece, from_mesh=False):
        if not self.timer.is_running():
            self.timer.start()
        if not from_mesh:
            self._send_pick_notification (piece)

    def piece_drop_cb (self, o, piece, from_mesh=False):
        if self._parent._shared_activity and not from_mesh:
            self._send_drop_notification (piece)

    def _freeze (self, journal=True):
        if journal:
            return {'thumb': self.thumb._freeze(),
                    'timer': self.timer._freeze(),
                    'game': self.game._freeze(),
                    }
        else:
            return {'timer': self.timer._freeze(),
                    'game': self.game._freeze(img_cksum_only=True),}

    def _thaw (self, data):
        self.timer.reset()
        for k in ('thumb', 'timer', 'game'):
            if data.has_key(k):
                logging.debug('_thaw data for %s: %s' % (k, data))
                getattr(self, k)._thaw(data[k])
        if data.has_key('game'):# and not data.has_key('thumb'):
            self.thumb.load_pb(self.game.board.cutboard.pb)
        if data.has_key('timer'):
            self._join_time = self.timer.ellapsed()
        if data.has_key('game') and data['game']['piece_pos']:
            self._show_game(reshuffle=False)

    @utils.trace
    def _send_status_update (self):
        """ Send a status update signal """
        if self._parent._shared_activity:
            if self.get_game_state() == GAME_STARTED:
                if self.thumb.has_image():
                    self.set_message(_("Game Started!"))
                else:
                    self.set_message(_("Waiting for Puzzle image to be transferred..."))
            self._parent.game_tube.StatusUpdate(self._state[1], self._join_time)

    @utils.trace
    def _send_game_update (self):
        """ A puzzle was selected, share it """
        if self._parent._shared_activity:
            # TODO: Send image 
            self._parent.game_tube.GameUpdate(self._state[1])

    @utils.trace
    def _send_pick_notification (self, piece):
        """ """
        if self._parent._shared_activity:
            self._parent.game_tube.PiecePicked(piece.get_index())

    @utils.trace
    def _recv_pick_notification (self, index):
        for piece in self.game.get_floating_pieces():
            if piece.get_index() == index:
                logging.debug("Remote picked piece %s" % piece)
                piece.set_sensitive(False)
                
    @utils.trace
    def _send_drop_notification (self, piece):
        """ """
        if piece.placed:
            self._parent.game_tube.PiecePlaced(piece.get_index())
        else:
            self._parent.game_tube.PieceDropped(piece.get_index(), piece.get_position())
    
    @utils.trace
    def _recv_drop_notification (self, index, position=None):
        for piece in self.game.get_floating_pieces():
            if piece.get_index() == index:
                logging.debug("Moving piece %s" % piece)
                if position is None:
                    self.game.board.place_piece(piece)
                else:
                    self.game._move_cb(piece, position[0], position[1], absolute=True)
                    self.game._drop_cb(piece, from_mesh=True)
                piece.set_sensitive(True)
                break
