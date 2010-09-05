#
# -*- coding: utf-8 -*-
#
# This file is part of lum, the LDAP User Manager
# 
# Author: Leonardo Robol <robol@poisson.phc.unipi.it>
# Date: 5 Sep 2010
#

import pygtk
import gtk
import os
import gnomekeyring

pygtk.require("2.0")

from ldapProtocol import UserModel, Connection
from configuration import Configuration
from exceptions import LumError

class lumApp():

	def __init__(self, datapath):
		
		# Save datapath that we will need to call all
		# other Dialogs
		self.__datapath = datapath
		
		# Load interface file
		self.__builder = gtk.Builder()
		self.__builder.add_from_file(os.path.join(datapath, "ui/LumApp.ui"))
		
		# Load main window
		self.__window = self.__builder.get_object("window")
		
		# Signal definition
		signals = {
		
			# Quit signals
			'on_quit_menu_item_activate': 		gtk.main_quit,
			'window_destroy_event_cb':			gtk.main_quit,
			'on_window_destroy':				gtk.main_quit,
			
			# Callbacks
			'on_about_menu_item_activate':		self.show_about_dialog,
			'on_new_user_menu_item_activate':	self.create_new_user_dialog,
			'on_connect_menu_item_activate': 	self.connect,
		}
		
		# Autoconnect signals
		self.__builder.connect_signals (signals)
		
		# Create initial configuration
		self.__configuration = Configuration()
		
		
		
		
	def start(self):
		"""Start lumApp"""
		
		# Show all
		self.__window.show_all()
		self.__connection = None

		
	def connect(self, menu_item = None):
		"""Connect to server"""
		# Get password from keyring
		try:
			pw_id = self.__configuration.get("LDAP", "password")
			password = gnomekeyring.item_get_info_sync('login', pw_id, ).get_secret()
		except:
			# Ask for password...
			password_dialog = lumPasswordEntry(self.__datapath)
			password = password_dialog.run()
			if password is not None:
			
				pw_id = gnomekeyring.item_create_sync('login', gnomekeyring.ITEM_GENERIC_SECRET,
											  self.__configuration.get("LDAP", "bind_dn"), dict(),
											  password, True)
											  
				self.__configuration.set("LDAP", "password", str(pw_id))
				
				try:
					self.__connection = Connection(password)
				except LumError:
					error_box = gtk.MessageDialog(parent = self.__window, type = gtk.MESSAGE_ERROR,
										buttons = gtk.BUTTONS_OK)
					error_box.set_title("Errore di connessione")
					error_box.set_markup("Errore durante la connessione al server, controllare le proprie credenziali!")
					error_box.run()
					error_box.destroy()
			else:
				self.__connection = None
		
	def show_about_dialog(self, menu_item):
		"""Show about dialog"""
		lumAbout(self.__datapath)
		
	def create_new_user_dialog(self, menu_item):
		"""Create new user"""
		new_user_dialog = lumUserDialog(self.__datapath)
		new_user_dialog.run()
		
		if new_user_dialog.usermodel is not None:
			if self.check_connection():
				self.__connection.add_user(new_user_dialog.usermodel)
			
	def check_connection(self):
		if self.__connection is None:
			self.connect ()
		return (self.__connection is not None)
		
		
class lumAbout():
	
	def __init__(self, datapath):
	
		self.__builder = gtk.Builder()
		self.__builder.add_from_file(os.path.join(datapath, "ui/LumAbout.ui"))
		
		dialog = self.__builder.get_object("about_dialog")
		
		dialog.run ()
		dialog.destroy ()
		
class lumUserDialog():

	def __init__(self, datapath, usermodel = None):
		
		self.__builder = gtk.Builder()
		self.__builder.add_from_file(os.path.join(datapath, "ui/LumNewUserDialog.ui"))
		
		self.__window = self.__builder.get_object("new_user_dialog")
		
		self.usermodel = None
		
		# Fill the data
		if usermodel is not None:
			self.__builder.get_object("username_entry").set_text(usermodel['username'])
			self.__builder.get_object("givenName_entry").set_text(usermodel['givenName'])
			self.__builder.get_object("sn_entry").set_text(usermodel['sn'])
			self.__builder.get_object("home_entry").set_text(usermodel['homeDirectory'])
			self.__builder.get_object("shell_entry").set_text(usermodel['loginShell'])
			self.__builder.get_object("uid_spinbutton").set_value(usermodel['uid'])
			self.__builder.get_object("gid_spinbutton").set_value(usermodel['gid'])
		
		
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
			uid = self.__builder.get_object("uid_spinbutton").get_value()
			gid = self.__builder.get_object("gid_spinbutton").get_value()
			
			self.usermodel = UserModel(username = username, given_name = givenName, 
									   sn = sn, uid = uid, gid = gid, login_shell = shell)
		self.__window.destroy()
		
class lumPasswordEntry():

	def __init__(self, datapath):
	
		self.__builder = gtk.Builder()
		self.__builder.add_from_file(os.path.join(datapath, "ui/LumPasswordEntry.ui"))
		
		self.__dialog = self.__builder.get_object("password_dialog")
		
	def run(self):
	
		if (self.__dialog.run() == 1):
			password = self.__builder.get_object("password_entry").get_text()
		else:
			password = None
			
		self.__dialog.destroy ()
		return password
	

