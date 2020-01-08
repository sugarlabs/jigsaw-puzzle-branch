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
# FIXME Port to Collabwrapper
from gi.repository import TelepathyGLib as telepathy
#import telepathy.client
from sugar3.presence.tubeconn import TubeConnection
from sugar3.presence import presenceservice
#import dbus
import logging
logger = logging.getLogger('tube_helper')

GAME_IDLE = (10, 'idle')
GAME_SELECTED = (20, 'selected')
GAME_STARTED = (30, 'started')
GAME_FINISHED = (40, 'finished')
GAME_QUIT = (50, 'quit')

class TubeHelper (object):
    """ Tube handling mixin for activities """
    def __init__(self, tube_class, service):
        """Set up the tubes for this activity."""
        self.tube_class = tube_class
        self.service = service
        self.pservice = presenceservice.get_instance()

        #bus = dbus.Bus()


        name, path = self.pservice.get_preferred_connection()
        self.tp_conn_name = name
        self.tp_conn_path = path
        #self.conn = telepathy.client.Connection(name, path)
        self.game_tube = False
        self.initiating = None
        

        # Buddy object for you
        owner = self.pservice.get_owner()
        self.owner = owner

        self.connect('shared', self._shared_cb)
        self.connect('joined', self._joined_cb)

        #if self._shared_activity:
        #    # we are joining the activity
        #    self.conn = self._shared_activity.telepathy_conn
        #    self.tubes_chan = self._shared_activity.telepathy_tubes_chan
        #    self.text_chan = self._shared_activity.telepathy_text_chan
        #    self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES].connect_to_signal('NewTube',
        #                                                                    self._new_tube_cb)
        #    self.connect('joined', self._joined_cb)
        #    self._shared_activity.connect('buddy-joined',
        #                                  self._buddy_joined_cb)
        #    self._shared_activity.connect('buddy-left',
        #                                  self._buddy_left_cb)
        #    if self.get_shared():
        #        # we've already joined
        #        self._joined_cb()


    def _sharing_setup(self):
        if self._shared_activity is None:
            logger.error('Failed to share or join activity')
            return

        self.conn = self._shared_activity.telepathy_conn
        self.tubes_chan = self._shared_activity.telepathy_tubes_chan
        self.text_chan = self._shared_activity.telepathy_text_chan

        self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES].connect_to_signal('NewTube',
            self._new_tube_cb)

        self._shared_activity.connect('buddy-joined', self._buddy_joined_cb)
        self._shared_activity.connect('buddy-left', self._buddy_left_cb)

    def _shared_cb(self, activity):
        logger.debug('My activity was shared')
        self.initiating = True
        self._sharing_setup()

        logger.debug('This is my activity: making a tube...')
        id = self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES].OfferDBusTube(
            self.service, {})
        self.shared_cb()

    #def _shared_cb(self, activity):
    #    logger.debug('My activity was shared')
    #    self.initiating = True
    #    #self._setup()
    #
    #    self.conn = self._shared_activity.telepathy_conn
    #    self.tubes_chan = self._shared_activity.telepathy_tubes_chan
    #    self.text_chan = self._shared_activity.telepathy_text_chan
    #    self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES].connect_to_signal('NewTube',
    #                                                                    self._new_tube_cb)
    #
    #    for buddy in self._shared_activity.get_joined_buddies():
    #        pass  # Can do stuff with newly acquired buddies here
    #
    #    self._shared_activity.connect('buddy-joined', self._buddy_joined_cb)
    #    self._shared_activity.connect('buddy-left', self._buddy_left_cb)
    #
    #    logger.debug('This is my activity: making a tube...')
#   #     id = self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES].OfferTube(
#   #         telepathy.TUBE_TYPE_DBUS, self.service, {})
    #
    #    self.shared_cb()

    def shared_cb (self):
        """ override this """
        pass

#    # FIXME: presence service should be tubes-aware and give us more help
#    # with this
#    def _setup(self):
#        if self._shared_activity is None:
#            logger.error('Failed to share or join activity')
#            return
#
#        bus_name, conn_path, channel_paths =\
#            self._shared_activity.get_channels()
#
#        # Work out what our room is called and whether we have Tubes already
#        room = None
#        tubes_chan = None
#        text_chan = None
#        for channel_path in channel_paths:
#            channel = telepathy.client.Channel(bus_name, channel_path)
#            htype, handle = channel.GetHandle()
#            if htype == telepathy.HANDLE_TYPE_ROOM:
#                logger.debug('Found our room: it has handle#%d "%s"',
#                    handle, self.conn.InspectHandles(htype, [handle])[0])
#                room = handle
#                ctype = channel.GetChannelType()
#                if ctype == telepathy.CHANNEL_TYPE_TUBES:
#                    logger.debug('Found our Tubes channel at %s', channel_path)
#                    tubes_chan = channel
#                elif ctype == telepathy.CHANNEL_TYPE_TEXT:
#                    logger.debug('Found our Text channel at %s', channel_path)
#                    text_chan = channel
#
#        if room is None:
#            logger.error("Presence service didn't create a room")
#            return
#        if text_chan is None:
#            logger.error("Presence service didn't create a text channel")
#            return
#
#        # Make sure we have a Tubes channel - PS doesn't yet provide one
#        if tubes_chan is None:
#            logger.debug("Didn't find our Tubes channel, requesting one...")
#            tubes_chan = self.conn.request_channel(telepathy.CHANNEL_TYPE_TUBES,
#                telepathy.HANDLE_TYPE_ROOM, room, True)
#
#        self.tubes_chan = tubes_chan
#        self.text_chan = text_chan
#
#        tubes_chan[telepathy.CHANNEL_TYPE_TUBES].connect_to_signal('NewTube',
#            self._new_tube_cb)

    def _list_tubes_reply_cb(self, tubes):
        for tube_info in tubes:
            self._new_tube_cb(*tube_info)

    def _list_tubes_error_cb(self, e):
        logger.error('ListTubes() failed: %s', e)

    def _joined_cb(self, activity):
        if not self._shared_activity:
            return

        for buddy in self._shared_activity.get_joined_buddies():
            self._buddy_joined_cb(self, buddy)

        logger.debug('Joined an existing shared activity')
        self.initiating = False
        self._sharing_setup()

        logger.debug('This is not my activity: waiting for a tube...')
        self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES].ListTubes(
            reply_handler=self._list_tubes_reply_cb,
            error_handler=self._list_tubes_error_cb)

    def joined_cb (self):
        """ override this """
        pass

    def _new_tube_cb(self, id, initiator, type, service, params, state):
        logger.debug('New tube: ID=%d initator=%d type=%d service=%s '
                     'params=%r state=%d', id, initiator, type, service,
                     params, state)

        if (type == telepathy.TUBE_TYPE_DBUS and
            service == self.service):
            if state == telepathy.TUBE_STATE_LOCAL_PENDING:
                self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES].AcceptDBusTube(id)

            self.tube_conn = TubeConnection(self.conn,
                self.tubes_chan[telepathy.CHANNEL_TYPE_TUBES],
                id, group_iface=self.text_chan[telepathy.CHANNEL_INTERFACE_GROUP])

            
            logger.debug("creating game tube")
            self.game_tube = self.tube_class(self.tube_conn, self.initiating, self)

        self.new_tube_cb()

    def get_bus_name (self):
        return self.tube_conn.participants.get(self.tubes_chan[telepathy.CHANNEL_INTERFACE_GROUP].GetSelfHandle(), None)
        
    def new_tube_cb (self):
        """ override this """
        pass

    def _get_buddy(self, cs_handle):
        """Get a Buddy from a channel specific handle."""
        logger.debug('Trying to find owner of handle %u...', cs_handle)
        group = self.text_chan[telepathy.CHANNEL_INTERFACE_GROUP]
        my_csh = group.GetSelfHandle()
        logger.debug('My handle in that group is %u', my_csh)
        if my_csh == cs_handle:
            handle = self.conn.GetSelfHandle()
            logger.debug('CS handle %u belongs to me, %u', cs_handle, handle)
        elif group.GetGroupFlags() & telepathy.CHANNEL_GROUP_FLAG_CHANNEL_SPECIFIC_HANDLES:
            handle = group.GetHandleOwners([cs_handle])[0]
            logger.debug('CS handle %u belongs to %u', cs_handle, handle)
        else:
            handle = cs_handle
            logger.debug('non-CS handle %u belongs to itself', handle)
            # XXX: deal with failure to get the handle owner
            assert handle != 0
        return self.pservice.get_buddy_by_telepathy_handle(self.tp_conn_name,
                self.tp_conn_path, handle)

    def _buddy_joined_cb (self, activity, buddy):
        logger.debug('Buddy %s joined' % buddy.props.nick)
        self.buddy_joined_cb(buddy)

    def buddy_joined_cb (self, buddy):
        """ override this """
        pass

    def _buddy_left_cb (self, activity, buddy):
        logger.debug('Buddy %s left' % buddy.props.nick)
        self.buddy_left_cb(buddy)

    def buddy_left_cb (self, buddy):
        """ override this """
        pass

