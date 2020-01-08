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
import gtk, gobject

import os
from glob import glob
import logging
import md5

from sugar import mime
from sugar.graphics.objectchooser import ObjectChooser

from .borderframe import BorderFrame
from .utils import load_image, resize_image, RESIZE_CUT

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


from gettext import gettext as _

THUMB_SIZE = 48
IMAGE_SIZE = 200
#MYOWNPIC_FOLDER = os.path.expanduser("~/.sugar/default/org.worldwideworkshop.olpc.MyOwnPictures")

def prepare_btn (btn):
    return btn

def register_category (pixbuf_class, path):
    pass

class CategoryDirectory (object):
    def __init__ (self, path, width=-1, height=-1, method=RESIZE_CUT):
        self.path = path
        self.method = method
        self.pb = None
        if os.path.isdir(path):
            self.gather_images()
        else:
            self.images = [path]
        self.set_thumb_size(THUMB_SIZE, THUMB_SIZE)
        self.set_image_size(width, height)
        self.filename = None
        self.name = os.path.basename(path)

    def gather_images (self):
        """ Lists all images in the selected path as per the wildcard expansion of 'image_*'.
        Adds all linked images from files (*.lnk) """
        self.images = []
        links = glob(os.path.join(self.path, "*.lnk"))
        for link in links:
            fpath = file(link).readlines()[0].strip()
            if os.path.isfile(fpath) and not (fpath in self.images):
                self.images.append(fpath)
            else:
                os.remove(link)
        self.images.extend(glob(os.path.join(self.path, "image_*")))
        self.images.sort()

    def set_image_size (self, w, h):
        self.width = w
        self.height = h

    def set_thumb_size (self, w, h):
        self.twidth = w
        self.theight = h
        self.thumb = self._get_category_thumb()

    def get_image (self, name):
        if not len(self.images) or name is None or name not in self.images:
            return None
        self.pb = load_image(name)
        if self.pb is not None:
            rv = resize_image(self.pb, self.width, self.height, method=self.method)
            self.filename = name
            return rv
        return None
            
    def get_next_image (self):
        if not len(self.images):
            return None
        if self.filename is None or self.filename not in self.images:
            pos = -1
        else:
            pos = self.images.index(self.filename)
        pos += 1
        if pos >= len(self.images):
            pos = 0
        return self.get_image(self.images[pos])

    def get_previous_image (self):
        if not len(self.images):
            return None
        if self.filename is None or self.filename not in self.images:
            pos = len(self.images)
        else:
            pos = self.images.index(self.filename)
        pos -= 1
        if pos < 0:
            pos = len(self.images) - 1
        return self.get_image(self.images[pos])

    def has_images (self):
        logging.debug("IMG %s" % self.images)
        return len(self.images) > 0

    def count_images (self):
        return len(self.images)

    def has_image (self):
        return self.pb is not None

    def _get_category_thumb (self):
        if os.path.isdir(self.path):
            thumbs = glob(os.path.join(self.path, "thumb.*"))
            thumbs.extend(glob(os.path.join(self.path, "default_thumb.*")))
            thumbs.extend(glob(os.path.join(mmmpath, "mmm_images","default_thumb.*")))
            logging.debug(thumbs)
            thumbs = [x for x in thumbs if os.path.exists(x)]
            thumbs.append(None)
        else:
            thumbs = [self.path]
        logging.debug("%s %s" % (self.path, thumbs))
        return load_image(thumbs[0], self.twidth, self.theight)
    

class ImageSelectorWidget (gtk.Table):
    __gsignals__ = {'category_press' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
                    'image_press' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),}

    def __init__ (self,
                  width=IMAGE_SIZE,
                  height=IMAGE_SIZE,
                  frame_color=None,
                  prepare_btn_cb=prepare_btn,
                  method=RESIZE_CUT,
                  image_dir=None,
                  parent=None):
        gtk.Table.__init__(self, 2,5,False)
        self._parent = parent
        self._signals = []
        self.width = width
        self.height = height
        self.image = gtk.Image()
        self.method = method
        #self.set_myownpath(MYOWNPIC_FOLDER)
        img_box = BorderFrame(border_color=frame_color)
        img_box.add(self.image)
        img_box.set_border_width(5)
        self._signals.append((img_box, img_box.connect('button_press_event', self.emit_image_pressed)))
        self.attach(img_box, 0,5,0,1,0,0)
        self.attach(gtk.Label(), 0,1,1,2)
        self.bl = gtk.Button()

        il = gtk.Image()
        il.set_from_pixbuf(load_image(os.path.join(iconpath, 'arrow_left.png')))
        self.bl.set_image(il)

        self.bl.connect('clicked', self.previous)
        self.attach(prepare_btn_cb(self.bl), 1,2,1,2,0,0)

        cteb = gtk.EventBox()
        self.cat_thumb = gtk.Image()
        self.cat_thumb.set_size_request(THUMB_SIZE, THUMB_SIZE)
        cteb.add(self.cat_thumb)
        self._signals.append((cteb, cteb.connect('button_press_event', self.emit_cat_pressed)))
        self.attach(cteb, 2,3,1,2,0,0,xpadding=10)
        
        self.br = gtk.Button()
        ir = gtk.Image()
        ir.set_from_pixbuf(load_image(os.path.join(iconpath,'arrow_right.png')))
        self.br.set_image(ir)
        self.br.connect('clicked', self.__next__)
        self.attach(prepare_btn_cb(self.br), 3,4,1,2,0,0)
        self.attach(gtk.Label(),4,5,1,2)
        self.filename = None
        self.show_all()
        self.image.set_size_request(width, height)
        if image_dir is None:
            image_dir = os.path.join(mmmpath, "mmm_images")
        self.set_image_dir(image_dir)

    def add_image (self, *args):#widget=None, response=None, *args):
        """ Use to trigger and process the My Own Image selector. """

        if hasattr(mime, 'GENERIC_TYPE_IMAGE'):
            chooser = ObjectChooser(_('Choose image'), self._parent,
                                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                    what_filter=mime.GENERIC_TYPE_IMAGE)
        else:
            chooser = ObjectChooser(_('Choose image'), self._parent,
                                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        try:
            result = chooser.run()
            if result == gtk.RESPONSE_ACCEPT:
                jobject = chooser.get_selected_object()
                if jobject and jobject.file_path:
                    if self.load_image(str(jobject.file_path), True):
                        pass
                    else:
                        err = gtk.MessageDialog(self._parent, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                                _("Not a valid image file"))
                        err.run()
                        err.destroy()
                        return
        finally:
            chooser.destroy()
            del chooser


        #print (widget,response,args)
        #if response is None:
        #    # My Own Image selector
        #    imgfilter = gtk.FileFilter()
        #    imgfilter.set_name(_("Image Files"))
        #    imgfilter.add_mime_type('image/*')
        #    fd = gtk.FileChooserDialog(title=_("Select Image File"), parent=None,
        #                               action=gtk.FILE_CHOOSER_ACTION_OPEN,
        #                               buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        #
        #    fd.set_current_folder(os.path.expanduser("~/"))
        #    fd.set_modal(True)
        #    fd.add_filter(imgfilter)
        #    fd.connect("response", self.add_image)
        #    fd.resize(800,600)
        #    fd.show()
        #else:
        #    if response == gtk.RESPONSE_ACCEPT:
        #        if self.load_image(widget.get_filename()):
        #            pass
        #            #self.do_shuffle()
        #        else:
        #            err = gtk.MessageDialog(self._parent, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
        #                                    _("Not a valid image file"))
        #            err.run()
        #            err.destroy()
        #            return
        #    widget.destroy()

    def set_readonly (self, ro=True):
        if ro:
            self.bl.hide()
            self.br.hide()
            for w, s in self._signals:
                w.handler_block(s)

    #def set_myownpath (self, path):
    #    """ Sets the path to My Own Pictures storage, so we know where to add links to new pictures """
    #    if path is None:
    #        self.myownpath = None
    #    else:
    #        if not os.path.exists(path):
    #            os.mkdir(path)
    #        self.myownpath = path

    #def is_myownpath (self):
    #    """ Checks current path against the set custom image path """
    #    return self.myownpath == self.category.path
    #
    #def gather_myownpath_images(self):
    #    """ """
    #    rv = []
    #    self.images = []
    #    links = glob(os.path.join(self.myownpath, "*.lnk"))
    #    for link in links:
    #        linfo = filter(None, map(lambda x: x.strip(), file(link).readlines()))
    #        fpath = linfo[0]
    #        if os.path.isfile(fpath) and not (fpath in self.images):
    #            self.images.append(fpath)
    #            if len(linfo) > 1:
    #                digest = linfo[1]
    #            else:
    #                digest = md5.new(file(fpath, 'rb').read()).hexdigest()
    #            rv.append((link, fpath, digest))
    #    for fpath in glob(os.path.join(self.myownpath, "image_*")):
    #        digest = md5.new(file(fpath, 'rb').read()).hexdigest()
    #        rv.append((fpath, fpath, digest))
    #    return rv

    def emit_cat_pressed (self, *args):
        self.emit('category_press')
        return True

    def emit_image_pressed (self, *args):
        self.emit('image_press')
        return True

    def has_image (self):
        return self.category.has_image()

    def get_category_name (self):
        return self.category.name

    def get_filename (self):
        return self.category.filename

    def get_image (self):
        return self.category.pb

    def next (self, *args, **kwargs):
        pb = self.category.get_next_image()
        if pb is not None:
            self.image.set_from_pixbuf(pb)

    def previous (self, *args, **kwargs):
        pb = self.category.get_previous_image()
        if pb is not None:
            self.image.set_from_pixbuf(pb)

    def get_image_dir (self):
        return self.category.path

    def set_image_dir (self, directory):
        if os.path.exists(directory) and not os.path.isdir(directory):
            filename = directory
            directory = os.path.dirname(directory)
            logging.debug("dir=%s, filename=%s" % (directory, filename))
        else:
            logging.debug("dir=%s" % (directory))
            filename = None
        self.category = CategoryDirectory(directory, self.width, self.height, self.method)
        self.cat_thumb.set_from_pixbuf(self.category.thumb)
        if filename:
            self.image.set_from_pixbuf(self.category.get_image(filename))
        else:
            if self.category.has_images():
                next(self)

    def load_image(self, filename, fromJournal=False):
        """ Loads an image from the file """
        #if self.myownpath is not None and os.path.isdir(self.myownpath) and not fromJournal:
        #    name = os.path.splitext(os.path.basename(filename))[0]
        #    while os.path.exists(os.path.join(self.myownpath, '%s.lnk' % name)):
        #        name = name + '_'
        #    f = file(os.path.join(self.myownpath, '%s.lnk' % name), 'w')
        #    f.write(filename)
        #    image_digest = md5.new(file(filename, 'rb').read()).hexdigest()
        #    f.write('\n%s' % image_digest)
        #    f.close()
        #    self.category = CategoryDirectory(self.myownpath, self.width, self.height, method=self.method)
        #    self.image.set_from_pixbuf(self.category.get_image(filename))
        #else:
        self.category = CategoryDirectory(filename, self.width, self.height, method=self.method)
        next(self)
        self.cat_thumb.set_from_pixbuf(self.category.thumb)
        return self.image.get_pixbuf() is not None

    def load_pb (self, pb):
        self.category.pb = pb
        self.image.set_from_pixbuf(resize_image(pb, self.width, self.height, method=self.method))

    #def set_game_widget(self, game_widget):
    #    if self.has_image():
    #        game_widget.load_image(self.get_filename())

    def _freeze (self):
        """ returns a json writable object representation capable of being used to restore our current status """
        return {'image_dir': self.get_image_dir(),
                'filename': self.get_filename()}

    def _thaw (self, obj):
        """ retrieves a frozen status from a python object, as per _freeze """
        self.set_image_dir(obj.get('image_dir', None))
        self.image.set_from_pixbuf(self.category.get_image(obj.get('filename', None)))

class CategorySelector (gtk.ScrolledWindow):
    __gsignals__ = {'selected' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str,))}
    
    def __init__ (self, title=None, selected_category_path=None, path=None, extra=()):
        gtk.ScrolledWindow.__init__ (self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        if path is None:
            path = os.path.join(mmmpath, 'mmm_images')
        self.path = path
        self.thumbs = []
        model, selected = self.get_model(path, selected_category_path, extra)
        self.ignore_first = selected is not None
        
        self.treeview = gtk.TreeView()
        col = gtk.TreeViewColumn(title)
        r1 = gtk.CellRendererPixbuf()
        r2 = gtk.CellRendererText()
        col.pack_start(r1, False)
        col.pack_start(r2, True)
        col.set_cell_data_func(r1, self.cell_pb)
        col.set_attributes(r2, text=1)
        self.treeview.append_column(col)
        self.treeview.set_model(model)

        self.add(self.treeview)
        self.show_all()
        if selected is not None:
            self.treeview.get_selection().select_path(selected)
        self.treeview.connect("cursor-changed", self.do_select)

    def grab_focus (self):
        self.treeview.grab_focus()

    def cell_pb (self, tvcolumn, cell, model, it):
        # Renders a pixbuf stored in the thumbs cache
        cell.set_property('pixbuf', self.thumbs[model.get_value(it, 2)])

    def get_pb (self, path):
        thumbs = glob(os.path.join(path, "thumb.*"))
        thumbs.extend(glob(os.path.join(self.path, "default_thumb.*")))
        thumbs = [x for x in thumbs if os.path.exists(x)]
        thumbs.append(None)
        return load_image(thumbs[0], THUMB_SIZE, THUMB_SIZE)

    def get_model (self, path, selected_path, extra):
        # Each row is (path/dirname, pretty name, 0 based index)
        selected = None
        store = gtk.ListStore(str, str, int)
        store.set_sort_column_id(1, gtk.SORT_ASCENDING)
        files = [os.path.join(path, x) for x in os.listdir(path) if not x.startswith('.')]
        files.extend(extra)
        for fullpath, prettyname in [(x, _(os.path.basename(x))) for x in files if os.path.isdir(x)]:
            count = CategoryDirectory(fullpath).count_images()
            logging.debug("%s %s %s" % (fullpath, prettyname, count))
            store.append([fullpath, prettyname + (" (%i)" % count), len(self.thumbs)])
            self.thumbs.append(self.get_pb(fullpath))
        #if os.path.isdir(MYOWNPIC_FOLDER):
        #    count = CategoryDirectory(MYOWNPIC_FOLDER).count_images()
        #    store.append([MYOWNPIC_FOLDER, _("My Pictures") + (" (%i)" % count), len(self.thumbs)])
        #    self.thumbs.append(self.get_pb(MYOWNPIC_FOLDER))

        i = store.get_iter_first()
        while i:
            if selected_path == store.get_value(i, 0):
                selected = store.get_path(i)
                break
            i = store.iter_next(i)
        return store, selected

    def do_select (self, tree, *args, **kwargs):
        if self.ignore_first:
            self.ignore_first = False
        else:
            tv, it = tree.get_selection().get_selected()
            self.emit("selected", tv.get_value(it,0))

