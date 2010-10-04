#
# -*- coding: utf-8 -*-
#

import gtk, gettext, locale, os, gobject
from lum.ldap_protocol import UserModel
    
_ = gettext.gettext
package_dir = os.path.realpath(os.path.join(__file__,
                                           os.path.pardir))

def gettext_init():
    # Load local translations
    if os.path.join("src", "lum", "interface") in package_dir:
        lum_base = os.path.realpath(os.path.join(package_dir,
                                                 os.path.pardir,
                                                 os.path.pardir,
                                                 os.path.pardir,
                                                 "locale"))
        gettext.bindtextdomain("lum", lum_base)
    else:
        gettext.bindtextdomain("lum")

    gettext.textdomain("lum")
    try:
        locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())
    except locale.Error:
        print "Unable to load localized strings"


def show_error_dialog(message):
    """Show an error dialog with message"""

    dialog = gtk.MessageDialog(type = gtk.MESSAGE_ERROR,
                               buttons = gtk.BUTTONS_OK)
    dialog.set_title ("Ldap User Manager")
    dialog.set_markup(message)

    dialog.run()
    dialog.destroy()

def show_info_dialog(message):
    """Show an information dialog"""
    
    dialog = gtk.MessageDialog(type = gtk.MESSAGE_INFO,
                               buttons = gtk.BUTTONS_OK)
    dialog.set_title("Ldap User Manager")
    dialog.set_markup(message)

    dialog.run()
    dialog.destroy()
    


def ask_question(message):
    """Ask a question to the user"""
    dialog = gtk.MessageDialog(type = gtk.MESSAGE_QUESTION,
                               buttons = gtk.BUTTONS_YES_NO)
    dialog.set_title("Ldap User Manager")
    dialog.set_markup(message)
    
    if dialog.run() == gtk.RESPONSE_YES:
        dialog.destroy()
        return True
    else:
        dialog.destroy()
        return False

def create_builder(interface_file):
    """Create a gtk.Builder loading the
    right interface file"""
    
    builder = gtk.Builder()
    try:
        builder.set_translation_domain("lum")
    except locale.Error:
        print "Unable to load localized interface"

    builder.add_from_file(os.path.join(package_dir,
                                       os.path.join("ui", interface_file)))

    return builder

class GroupStore(gtk.ListStore):

    def __init__(self, datapath):

        # Create space for the data we have to save
        gtk.ListStore.__init__(self, gtk.gdk.Pixbuf,
                               gobject.TYPE_STRING,
                               gobject.TYPE_INT)

        # Preload group_image
        group_image = gtk.Image()
        group_image.set_from_file(os.path.join(datapath,
                                               "ui", "group.png"))
        self.__group_image_pixbuf = group_image.get_pixbuf()

    def append(self, gid, group):
        """Append group and gid to the list"""

        data_to_append = (self.__group_image_pixbuf,
                          str(group), int(gid))
        gtk.ListStore.append(self, data_to_append)

    def get_group_name(self, gid):
        """Return group_name from gid. This method accept
        event a GtkTreeiter"""
        
        if isinstance(gid, gtk.TreeIter):
            return self.get_value(gid, 1)
        
        it = self.get_iter_first()
        while it is not None:
            if self.get_value(it, 2) == gid:
                return self.get_value(it, 1)
            else:
                it = self.iter_next(it)
        return None

    def get_gid(self, group_name):
        """Get the gid from group_name or from an iter"""
        
        if isinstance(group_name, gtk.TreeIter):
            return self.get_value(group_name, 2)

        it = self.get_iter_first()
        while it is not None:
            if self.get_value(it, 1) == group_name:
                return self.get_value(it, 2)
            else:
                it = self.iter_next(it)
        return None


class UserStore(gtk.ListStore):

    def __init__(self, datapath, group_store):

        # Save datapath
        self.__datapath = datapath

        # And group_store 
        self.__group_store = group_store

        # Preload user image pixbuf
        user_image = gtk.Image()
        user_image.set_from_file(os.path.join(self.__datapath,
                                              "ui", "user.png"))
        self.__user_image_pixbuf = user_image.get_pixbuf()
        
        # Init a ListStore with required fields, i.e.
        # - User image
        # - Username
        # - Name
        # - Group
        # - UserModel
        gtk.ListStore.__init__(self, gtk.gdk.Pixbuf,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               gobject.TYPE_STRING,
                               UserModel)

    def append(self, usermodel):
        """Override append method of ListStore making it
        more lum-friendly"""

        username = usermodel.get_username()
        name = usermodel.get_gecos()
        gid = usermodel.get_gid()

        group = self.__group_store.get_group_name(gid)
        if group is None:
            group = _("Unknown")

        data_to_append = (self.__user_image_pixbuf,
                          username, name, group, usermodel)
        gtk.ListStore.append(self, data_to_append)

    def get_usermodel(self, it):
        """Return usermodel associated with entry"""
        return self.get_value(it, 4)
