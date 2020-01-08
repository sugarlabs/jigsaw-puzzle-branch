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

import os
import sys

cwd = os.path.split(__file__)[0]

from gi.repository import Gtk 
theme = Gtk.IconTheme.get_default()

if os.path.exists(os.path.join(cwd, 'mmm_modules')):
    # We are self contained
    theme.append_search_path(os.path.join(cwd, 'mamamedia_icons'))
    pass
else:
    # Working with shared code on MaMaMediaMenu

    propfile = os.path.expanduser("~/.sugar/default/org.worldwideworkshop.olpc.MMMPath")
    if os.path.exists(propfile):
        mmmpath = file(propfile, 'rb').read()
    else:
        mmmpath=os.path.normpath(os.path.join(cwd, '..', 'MaMaMediaMenu.activity'))

    #print ("MMMPath", mmmpath)

    sys.path.append(mmmpath)
    theme.append_search_path(os.path.join(mmmpath, 'icons'))

from mmm_modules import *


if __name__ == '__main__':
    gather_other_translations()
    
