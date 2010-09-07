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
import gobject
import os
import gnomekeyring

# Require a recent pygtk version
pygtk.require("2.0")

# Import modules from lum
from ldap_protocol import UserModel, Connection
from configuration import Configuration
from exceptions import LumError

class lumApp(gobject.GObject):

	def __init__(self, datapath):
	
		# Images
		self.__user_image = gtk.Image()
		self.__user_image.set_from_file(os.path.join(datapath, "ui/user.png"))
		self.__user_image = self.__user_image.get_pixbuf()
		
		# Internal space for usermodels
		# Usermodel will be saved in a dictionary using uids as keys,
		# so it will be easy to get them even from entry in the treeview
		self.__user_model_store = {}
		
		# Gobject constructor
		gobject.GObject.__init__ (self)
		
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
			'on_reload_user_list_menu_item_activate': 	self.reload_user_list,
			'on_delete_user_menu_item_activate':		self.delete_user,
			'on_filter_entry_changed':					self.refilter,
			'on_forget_password_menu_item_activate':	self.forget_password,
		}
		
		# Autoconnect signals
		self.__builder.connect_signals (signals)
		
		# Create initial configuration
		self.__configuration = Configuration()
		
		# Activate filter
		self.__treefilter = self.__builder.get_object("user_store").filter_new()
		self.__treefilter.set_visible_func(self.filter_users)
		
		# Change the model of the treeview
		self.__builder.get_object("user_treeview").set_model(self.__treefilter)
		
	def start(self):
		"""Start lumApp"""
		
		# Show all
		self.__window.show_all()
		self.__connection = None

		
	def connect(self, menu_item = None):
		"""Connect to server"""
		# Get password from keyring
			
		password = self.ask_password()
		
		# Notify user of connection
		self.statusbar_update("Connecting to %s." % self.__configuration.get('LDAP', 'uri'))
		
		# Try to connect to the specified server
		try:
			self.__connection = Connection(password)
		except LumError:
			
			# If we can't, maybe password is wrong, so ask it again
			self.forget_password()
			password = self.ask_password()
			
			# and retry the connection. But if we fail even this time, then
			# abort
			try:
				self.__connection = Connection(password)
			except:
			
				# You had two opportunities, and both are gone. 
				error_box = gtk.MessageDialog(parent = self.__window, type = gtk.MESSAGE_ERROR,
									buttons = gtk.BUTTONS_OK)
			
				error_box.set_title("Errore di connessione")
				error_box.set_markup("Errore durante la connessione al server, controllare le proprie credenziali!")
				error_box.run()
				error_box.destroy()
				
				self.__connection = None
				
				self.statusbar_update("Connection failed.")
		
		# If you managed to open the connection, show it in the status bar
		if self.__connection is not None:
			self.statusbar_update("Connection to %s initialized" % self.__configuration.get("LDAP", "uri"))
			self.reload_user_list()
			
	def filter_users(self, model, treeiter, user_data = None):
		"""Filter users based on what is placed in filter_entry"""
		key = self.__builder.get_object("filter_entry").get_text()
		
		if key == "":
			return True
		
		if key in model.get_value(treeiter, 0):
			return True
		if key in model.get_value(treeiter, 1):
			return True
		if key in model.get_value(treeiter, 2):
			return True
			
		return False
		
	def ask_password(self):
		"""A simple routine that ask for password, if it is not yet in
		the keyring"""
		display_name = "@".join([self.__configuration.get("LDAP", "bind_dn"), self.__configuration.get("LDAP", "uri")])
		if gnomekeyring.is_available():
			for pw_id in gnomekeyring.list_item_ids_sync('login'):
				pw = gnomekeyring.item_get_info_sync("login", pw_id)
				if pw.get_display_name() == display_name:
					return pw.get_secret()
		
		# Ask for password...
		password_dialog = lumPasswordEntry(self.__datapath)
		password = password_dialog.run()
		if password is not None:
		
			atts = { 
				'application': 'Ldap User Manager',
				'username':		self.__configuration.get("LDAP", "bind_dn"),
				'server':		self.__configuration.get("LDAP", "uri"),
				'protocol':		'ldap',
				'port':			'389',
			}
			
			pw_id = gnomekeyring.item_create_sync('login', gnomekeyring.ITEM_GENERIC_SECRET,
										  display_name, atts, password, True)
		return password
		
	def refilter(self, entry):
		"""Callback to refilter treeview"""
		self.__treefilter.refilter()
		
		
	def show_about_dialog(self, menu_item):
		"""Show about dialog"""
		lumAbout(self.__datapath)
		
	def delete_user(self, menu_item = None):
		"""Delete the selected user"""
		user_store, treeiter = self.__builder.get_object("user_treeview").get_selection().get_selected()
		if treeiter is None:
			m = gtk.MessageDialog(type = gtk.MESSAGE_ERROR, buttons = gtk.BUTTONS_OK)
			m.set_markup("No user selected!")
			m.set_title("Error")
			m.run()
			m.destroy()
		else:
			# Get username from the liststore
			username = user_store.get_value(treeiter, 0)
			del self.__user_model_store[username]
			user_store.remove(treeiter)
			self.__connection.delete_user(username)
			self.statusbar_update("User %s deleted." % username)
			
	def forget_password(self, menu_item = None):
		if not gnomekeyring.is_available():
			return None
		display_name = "@".join([self.__configuration.get("LDAP", "bind_dn"), self.__configuration.get("LDAP", "uri")])
		for pw_id in gnomekeyring.list_item_ids_sync("login"):
			if gnomekeyring.item_get_info_sync("login", pw_id).get_display_name() == display_name:
				gnomekeyring.item_delete_sync('login', pw_id)
		
	def clear_user_list(self):
		self.__builder.get_object("user_store").clear()
		self.__user_model_store = {}
		
		
	def reload_user_list(self, menu_item = None):
		"""Reload user list in the main window"""
		if self.__check_connection():
			self.clear_user_list()
			users = self.__connection.get_users()
			for user in users:
				self.push_user(user)
				
	def push_user(self, usermodel):
		"""Add a user on the treeview in the main window"""
		user_store = self.__builder.get_object("user_store")
		user_store.append ((usermodel['uid'][0], " ".join([usermodel['givenName'][0], usermodel['sn'][0]]),
						   self.__connection.group_from_gid(usermodel['gidNumber'][0]), self.__user_image))
		self.__user_model_store[usermodel['uid'][0]] = usermodel
		
	def statusbar_update(self, message):
		"""Update statusbar with new message"""
		statusbar = self.__builder.get_object("statusbar")
		statusbar.push(0, message)
		
	def create_new_user_dialog(self, menu_item):
		"""Create new user"""
		self.__check_connection()
		new_user_dialog = lumNewUserDialog(self.__datapath, self.__connection)
		new_user_dialog.run()
		
		if new_user_dialog.usermodel is not None:
			if self.__check_connection():
				self.__connection.add_user(new_user_dialog.usermodel)
				self.statusbar_update("User %s created correctly." % new_user_dialog.usermodel['uid'][0])
		self.reload_user_list()
			
	def __check_connection(self):
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
		
class lumConnectDialog():

	def __init__(self, datapath, configuration):
		
		self.__builder = gtk.Builder()
		self.__builder.add_from_file(os.path.join(datapath, "ui/LumConnectDialog.ui"))
		
		self.__dialog = self.__builder.get_object("connect_dialog")
		
	def run(self):
	
		if self.__dialog.run() == 1:
			return True
		else:
			return False
	

