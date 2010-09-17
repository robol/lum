#
# -*- coding: utf-8 -*-
#

import gtk

class lumTreeViewMenu(gtk.Menu):

	def __init__(self, parent):
		gtk.Menu.__init__(self)
		
		self.__parent = parent
		self.__edit_button = gtk.MenuItem("Modifica")
		self.__del_button  = gtk.MenuItem("Elimina")
		self.append (self.__edit_button)
		self.append (self.__del_button)
		
		self.__edit_button.show()
		self.__del_button.show()
		
		self.__edit_button.connect("activate", self.edit)
		self.__del_button.connect("activate",  self.delete)
		
		self.username = None
		
	def edit(self, button):
		self.__parent.edit_user()
		
	def delete(self, button):
		self.__parent.delete_user()
	
