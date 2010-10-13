#
# -*- coding: utf-8 -*-
#

import gtk
from utilities import _

class lumUserTreeViewMenu(gtk.Menu):

    def __init__(self, parent):
        gtk.Menu.__init__(self)
        
        self.__parent = parent
        self.__edit_button = gtk.MenuItem(_("Edit"))
        self.__del_button  = gtk.MenuItem(_("Delete"))
        self.__pwd_button  = gtk.MenuItem(_("Change password"))

        self.append (self.__edit_button)
        self.append (self.__del_button)
        self.append (self.__pwd_button)
        
        self.__edit_button.show()
        self.__del_button.show()
        self.__pwd_button.show()
        
        self.__edit_button.connect("activate", self.edit)
        self.__del_button.connect("activate",  self.delete)
        self.__pwd_button.connect("activate",  self.change_password)
        
        self.username = None
        
    def edit(self, button):
        self.__parent.edit_user()
        
    def delete(self, button):
        self.__parent.delete_user()
    
    def change_password(self, button):
        self.__parent.change_password()


class lumGroupTreeViewMenu(gtk.Menu):

    def __init__(self, parent):
        gtk.Menu.__init__(self)

        # Save internal data
        self.__parent = parent
        self.__delete_button = gtk.MenuItem(_("Delete"))
        self.__properties_button = gtk.MenuItem(_("Properties"))
        self.__edit_button = gtk.MenuItem(_("Edit members"))
        
        for it in (self.__delete_button, self.__properties_button,
                   self.__edit_button):
            self.append(it)
            it.show()

        self.__delete_button.connect("activate", self.delete_cb)
        self.__properties_button.connect("activate", self.properties_cb)
        self.__edit_button.connect("activate", self.edit_button_cb)

    def edit_button_cb(self, button):
        self.__parent.edit_group_members()

    def delete_cb(self, menu_item):
        self.__parent.delete_group()

    def properties_cb(self, menu_item):
        self.__parent.group_properties()
