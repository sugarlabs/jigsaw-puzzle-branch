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

# init gthreads before using abiword
import gi
gi.require_version('Pango', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GObject

from sugar3.activity.activity import Activity, get_bundle_path
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityButton
from sugar3.activity.widgets import TitleEntry
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ShareButton
from sugar3.activity.widgets import DescriptionItem

from gettext import gettext as _
import logging, os, sys
import time
import zlib
from io import StringIO
from mamamedia_modules import json

from JigsawPuzzleUI import JigsawPuzzleUI
# from mamamedia_modules import TubeHelper
from mamamedia_modules import GAME_IDLE, GAME_STARTED, GAME_FINISHED, GAME_QUIT

logger = logging.getLogger('jigsawpuzzle-activity')

# from dbus.service import method, signal
# from dbus.gi_service import ExportedGObject

SERVICE = "org.worldwideworkshop.olpc.JigsawPuzzle.Tube"
IFACE = SERVICE
PATH = "/org/worldwideworkshop/olpc/JigsawPuzzle/Tube"
'''
class GameTube (ExportedGObject):
    """ Manage the communication between cooperating activities """
    def __init__(self, tube, is_initiator, activity):
        super(GameTube, self).__init__(tube, PATH)
        self.tube = tube
        self.activity = activity
        self.add_status_update_handler()
        self.get_buddy = activity._get_buddy
        self.syncd_once = False
        if is_initiator:
            self.add_hello_handler()
            self.add_request_image_handler()
            #self.add_need_image_handler()
            #self.activity.ui.connect('game-state-changed', self.game_state_cb)
        else:
            self.add_game_update_handler()
            #self.add_re_sync_handler()
            self.Hello()
        self.add_piece_picked_handler()
        self.add_piece_placed_handler()
        self.add_piece_dropped_handler()
        self.tube.watch_participants(self.participant_change_cb)

    def participant_change_cb(self, added, removed):
        logger.debug('Adding participants: %r', added)
        logger.debug('Removing participants: %r', removed)


    ###############
    # Signals
    
    @signal(dbus_interface=IFACE, signature='')
    def Hello(self):
        """Request that this player's Welcome method is called to bring it
        up to date with the game state.
        """
        pass

    @signal(dbus_interface=IFACE, signature='s')
    def GameUpdate(self, game_state):
        """ When an image is chosen by the initiator, this method gets called."""
        pass

    @signal(dbus_interface=IFACE, signature='su')
    def StatusUpdate (self, status, ellapsed_time):
        """ signal a reshufle, possibly with a new image """
        pass
    
    @signal(dbus_interface=IFACE, signature='')
    def RequestImage (self):
        """ Request that the game image be sent to us. """
        pass

    @signal(dbus_interface=IFACE, signature='i')
    def PiecePicked (self, index):
        """ Signals a piece picked in the correct board position """
        pass
        
    @signal(dbus_interface=IFACE, signature='i')
    def PiecePlaced (self, index):
        """ Signals a piece placed in the correct board position """
        pass
        
    @signal(dbus_interface=IFACE, signature='i(dd)')
    def PieceDropped (self, index, position):
        """ Signals a piece that has been moved around and dropped """
        pass

    ###############
    # Callbacks

    def add_hello_handler(self):
        self.tube.add_signal_receiver(self.hello_cb, 'Hello', IFACE,
                                                                    path=PATH, sender_keyword='sender')

    def hello_cb(self, obj=None, sender=None):
        """Tell the newcomer what's going on."""
        logger.debug('Newcomer %s has joined', sender)
#       if self.activity.ui.get_game_state() < GAME_STARTED:
#           f = {}
#       else:
#           f = self.activity.ui._freeze(journal=False)
        self.tube.get_object(sender, PATH).Welcome(self.activity.ui.get_game_state()[1], dbus_interface=IFACE)

    def add_game_update_handler (self):
        self.tube.add_signal_receiver(self.game_update_cb, 'GameUpdate', IFACE,
                                                                    path=PATH, sender_keyword='sender')

    def game_update_cb (self, game_state, sender=None):
        logger.debug('GameUpdate: %s' % game_state)
        if game_state == GAME_STARTED[1]:
            self.activity.ui.set_game_state(GAME_STARTED)
            self.RequestImage()
        #self.activity.ui.set_game_state(str(game_state))
        #self.activity.ui._thaw(json.read(str(state)))

    def add_request_image_handler (self):
        self.tube.add_signal_receiver(self.request_image_cb, 'RequestImage', IFACE,
                                                                    path=PATH, sender_keyword='sender')

    def request_image_cb (self, sender=None):
        logger.debug('Sending image to %s', sender)
        img = self.activity.ui.game.board.cutboard.get_image_as_png()
        t = time.time()
        compressed = zlib.compress(img, 9)
        # We will be sending the image, 24K at a time (my tests put the high water at 48K)
        logger.debug("was %d, is %d. compressed to %d%% in %0.4f seconds" % (len(img), len(compressed), len(compressed)*100/len(img), time.time() - t))
        part_size = 24*1024
        parts = len(compressed) / part_size
        for i in range(parts+1):
            self.tube.get_object(sender, PATH).ImageSync(compressed[i*part_size:(i+1)*part_size], i+1,
                                                         dbus_interface=IFACE)
        self.tube.get_object(sender, PATH).ImageDetailsSync(json.write(self.activity.ui._freeze(journal=False)), dbus_interface=IFACE)


    def add_piece_picked_handler (self):
        self.tube.add_signal_receiver(self.piece_picked_cb, 'PiecePicked', IFACE,
                                                                    path=PATH, sender_keyword='sender')

    def piece_picked_cb (self, index, sender=None):
        if sender != self.activity.get_bus_name():
            self.activity.ui._recv_pick_notification(index)

    def add_piece_placed_handler (self):
        self.tube.add_signal_receiver(self.piece_placed_cb, 'PiecePlaced', IFACE,
                                                                    path=PATH, sender_keyword='sender')

    def piece_placed_cb (self, index, sender=None):
        if sender != self.activity.get_bus_name():
            self.activity.ui._recv_drop_notification(index)
    
    def add_piece_dropped_handler (self):
        self.tube.add_signal_receiver(self.piece_dropped_cb, 'PieceDropped', IFACE,
                                                                    path=PATH, sender_keyword='sender')

    def piece_dropped_cb (self, index, position, sender=None):
        if sender != self.activity.get_bus_name():
            self.activity.ui._recv_drop_notification(index, position)

    def add_status_update_handler(self):
        self.tube.add_signal_receiver(self.status_update_cb, 'StatusUpdate', IFACE,
                                                                    path=PATH, sender_keyword='sender')

    def status_update_cb (self, status, join_time, sender=None):
        buddy = self.get_buddy(self.tube.bus_name_to_handle[sender])
        logger.debug("status_update: %s %s" % (str(sender), str(join_time)))
        nick, stat = self.activity.ui.buddy_panel.update_player(buddy, status, True, int(join_time))
        if buddy != self.activity.owner:
            self.activity.ui.set_message(
                    _("Buddy '%(buddy)s' changed status: %(status)s") % \
                        {'buddy': nick, 'status': stat},
                    frommesh=True)
    
    ##############
    # Methods

    @method(dbus_interface=IFACE, in_signature='s', out_signature='')
    def Welcome(self, game_state):
        """ """
        logger.debug("state: '%s' (%s)" % (game_state, type(game_state)))
        if game_state == GAME_STARTED[1]:
            self.activity.ui.set_game_state(GAME_STARTED)
            self.RequestImage()
        else:
            self.activity.ui.set_game_state(GAME_IDLE)

    @method(dbus_interface=IFACE, in_signature='ayi', out_signature='', byte_arrays=True)
    def ImageSync (self, image_part, part_nr):
        """ """
        logger.debug("Received image part #%d, length %d" % (part_nr, len(image_part)))
        if part_nr == 1:
            self.image = StringIO()
            self.image.write(image_part)
        else:
            self.image.write(image_part)

    @method(dbus_interface=IFACE, in_signature='s', out_signature='', byte_arrays=True)
    def ImageDetailsSync (self, state):
        """ Signals end of image and shares the rest of the needed data to create the image remotely."""
        state = json.read(str(state))
        state['game']['board']['cutboard']['pb'] = zlib.decompress(self.image.getvalue())
        self.activity.ui._thaw(state)
        self.activity.ui._send_status_update()
        
'''

class JigsawPuzzleActivity(Activity):
    def __init__(self, handle):
        Activity.__init__(self, handle)
        logger.debug('Starting Jigsaw Puzzle activity... %s' % str(get_bundle_path()))
        os.chdir(get_bundle_path())

        self.connect('destroy', self._destroy_cb)
        
        self.ui = JigsawPuzzleUI(self)
        self.set_canvas(self.ui)
        self.build_toolbar()
        self.show_all()
        
        # TubeHelper.__init__(self, tube_class=GameTube, service=SERVICE)
    
    def build_toolbar(self):
        # toolbar with the new toolbar redesign
        toolbar_box = ToolbarBox()

        activity_button = ActivityButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        title_entry = TitleEntry(self)
        toolbar_box.toolbar.insert(title_entry, -1)
        title_entry.show()

        description_item = DescriptionItem(self)
        toolbar_box.toolbar.insert(description_item, -1)
        description_item.show()

        share_button = ShareButton(self)
        toolbar_box.toolbar.insert(share_button, -1)
        share_button.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()
        
    def _destroy_cb(self, data=None):
        return True
    '''
    def new_tube_cb (self):
        self.ui.set_contest_mode(True)

    def shared_cb (self):
        self.ui.buddy_panel.add_player(self.owner)

    def joined_cb (self):
        self.ui.set_readonly()

    def buddy_joined_cb (self, buddy):
        nick = self.ui.buddy_panel.add_player(buddy)
        self.ui.set_message(_("Buddy '%s' joined the game!") % (nick), frommesh=True)

    def buddy_left_cb (self, buddy):
        nick = self.ui.buddy_panel.remove_player(buddy)
        self.ui.set_message(_("Buddy '%s' left the game!") % (nick), frommesh=True)
    '''
    
    def read_file(self, file_path):
        f = open(file_path, 'r')
        try:
            session_data = f.read()
        finally:
            f.close()
        self.ui._thaw(json.read(session_data))
        #import urllib
        #logging.debug('Read session: %s.' % urllib.quote(session_data))
        
    def write_file(self, file_path):
        # First make sure the game is showing, as we need that to get the piece positions
        
        session_data = json.write(self.ui._freeze())
        f = open(file_path, 'w')
        try:
            f.write(session_data)
        finally:
            f.close()
        #import urllib
        #logging.debug('Write session data: %s.' % urllib.quote(session_data))
