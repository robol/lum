#
# -*- coding: utf-8 -*-

import gtk, os
from lum.ldap_protocol import UserModel

class lumNewUserDialog():
	
	def __init__(self, datapath, connection):
		
		signals = {
			'on_username_entry_focus_out_event': 	self.guess_params,
		}
		
		self.__builder = gtk.Builder()
		self.__builder.add_from_file(os.path.join(datapath, "ui/LumNewUserDialog.ui"))
		
		self.__window = self.__builder.get_object("new_user_dialog")
		self.__connection = connection
		self.usermodel = None
		
		self.__builder.connect_signals(signals)
		
	def guess_params(self, widget = None, event_data = None):
		"""Guess parameters"""
		if widget is None:
			widget = self.__builder.get_object("username_entry")
		
		username = widget.get_text()
		
		# Guess Surname
		sn = self.__builder.get_object("sn_entry")
		if sn.get_text() == "":
			sn.set_text(username.split(".")[-1].capitalize())
		
		# Guess user home
		home = self.__builder.get_object("home_entry")
		if home.get_text() == "" and username != "":
			home.set_text("/home/" + username)
		
	def run(self):
		"""Run dialog"""
		
		# Check if the user says "save"...
		if self.__window.run() == 1:
			
			# And then retrieve data
			username = self.__builder.get_object("username_entry").get_text()
			givenName = self.__builder.get_object("givenName_entry").get_text()
			sn = self.__builder.get_object("sn_entry").get_text()
			home = self.__builder.get_object("home_entry").get_text()
			shell = self.__builder.get_object("shell_entry").get_text()
			
			# Set uid to 0 so ldap_protocol will autodetermine the first free uid
			# when creating the user
			uid = 0
			
			group = self.__builder.get_object("group_entry").get_text()
			gid = self.__connection.gid_from_group(group)
			
			# Check if this is an existent user
			if self.__connection.is_present("uid=%s" % username):
				
				m = gtk.MessageDialog(type = gtk.MESSAGE_ERROR, buttons = gtk.BUTTONS_OK)
				m.set_markup("L'utente è già esistente!\nSpecificare un diverso username")
				m.set_title("Utente già esistente")
				m.run()
				m.destroy ()
				self.__window.destroy()
				return None
			
			# Ask the user if he intended to create the group
			if gid is None:
				messageDialog = gtk.MessageDialog(type = gtk.MESSAGE_QUESTION, buttons = gtk.BUTTONS_YES_NO)
				messageDialog.set_markup("Il gruppo <b>%s</b> non esiste, crearlo ora?" % group)
				messageDialog.set_title("Gruppo inesistente")
				
				if messageDialog.run() == gtk.RESPONSE_YES:
					self.__connection.add_group(group)
					gid = self.__connection.gid_from_group(group)
				else:
					self.__window.destroy()
					return None
				
				messageDialog.destroy()
			
			self.usermodel = UserModel(username = username, given_name = givenName, 
									   sn = sn, uid = uid, gid = gid, login_shell = shell)
		self.__window.destroy()
		

