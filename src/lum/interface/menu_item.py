#
# -*- coding: utf-8 -*-
#

import gtk
from utilities import _

class lumTreeViewMenu(gtk.Menu):

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
