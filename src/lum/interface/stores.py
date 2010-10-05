#
# -*- coding: utf-8 -*-
#

import gtk, gobject, os
from lum.ldap_protocol import UserModel
from utilities import _

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

        # Make the store sorted
        self.set_sort_func(1, self.sort)
        self.set_sort_column_id(1, gtk.SORT_ASCENDING)

    def sort(self, model, iter1, iter2):
        """Sort groups"""

        group_1 = model.get_value(iter1, 1)
        group_2 = model.get_value(iter2, 1)

        # None is greater than everything because this make things
        # work, but I can't get why yet.
        if group_1 is None:
            return True
        if group_2 is None:
            return False
        return (group_1.lower() > group_2.lower())


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

        # Sort users
        self.set_sort_func(1, self.sort)
        self.set_sort_column_id(1, gtk.SORT_ASCENDING)

    def sort(self, model, iter1, iter2):
        """Sort users"""

        user1 = model.get_value(iter1, 1)
        user2 = model.get_value(iter2, 1)

        if user1 is None:
            return True
        if user2 is None:
            return False
        
        return user1.lower() > user2.lower()



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
