#
# -*- coding: utf-8 -*-
#

import gtk, os

class lumUserPasswordDialog():

	def __init__(self, datapath, username):
		
		self.__builder = gtk.Builder()
		self.__builder.add_from_file(os.path.join(datapath,
						"ui/LumUserPasswordDialog.ui"))
		self.__dialog = self.__builder.get_object("dialog")
		self.__dialog.set_title("Imposta password per %s" % username)
	def run(self):
		
		if self.__dialog.run():
			password_1 = self.__builder.get_object("password_entry_1").get_text()
			password_2 = self.__builder.get_object("password_entry_2").get_text()
			
			if password_1 != password_2:
				mb = gtk.MessageDialog(buttons = gtk.BUTTONS_OK, type = gtk.MESSAGE_ERROR)
				mb.set_markup("Le password inserite non coincidono. Ritentare.")
				mb.run ()
				mb.destroy()
				return self.run()
			else:
				self.__dialog.destroy()
				return password_1
		self.__dialog.destroy()
		return None

