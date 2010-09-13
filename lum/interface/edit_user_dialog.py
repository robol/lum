#
# -*- coding: utf-8 -*-
#

import gtk, os, gobject

class lumEditUserDialog():

	def __init__(self, datapath, usermodel, group_dict):
		
		self.__builder = gtk.Builder()
		self.__builder.add_from_file(os.path.join(datapath,
												  "ui/LumEditUserDialog.ui"))
		self.__dialog = self.__builder.get_object("dialog")
		
		self.__givenname_entry = self.__builder.get_object("givenname_entry")
		self.__sn_entry = self.__builder.get_object("sn_entry")
		self.__group_combobox = self.__builder.get_object("group_combobox")
		
		# Fill data
		self.__givenname_entry.set_text(usermodel['givenName'][0])
		self.__sn_entry.set_text(usermodel['sn'][0])
		
		self.__group_model = self.__builder.get_object("group_model")
										   
		self.__group_iter = None
		for gid, group in group_dict.items():
			it = self.__group_model.append((int(gid), group))
			if gid == usermodel['gidNumber'][0]:
				self.__group_iter = it
				
		if (self.__group_iter is not None):
			self.__group_combobox.set_active_iter(self.__group_iter)
		
		# Shell and home
		self.__shell_entry = self.__builder.get_object("shell_entry")
		self.__shell_entry.set_text(usermodel['loginShell'][0])
		self.__home_entry = self.__builder.get_object("home_entry")
		self.__home_entry.set_text(usermodel['homeDirectory'][0])
		
		self.__usermodel = usermodel
		
		
	def run(self):
		"""Run the dialog"""
		
		if self.__dialog.run() == 0:
			self.__dialog.destroy()
			return None
		else:
			
			# Save data
			self.__usermodel['givenName'] = [self.__givenname_entry.get_text()]
			self.__usermodel['sn'] = [self.__sn_entry.get_text()]
			self.__usermodel['homeDirectory'] = [self.__home_entry.get_text()]
			self.__usermodel['loginShell'] = [self.__shell_entry.get_text()]
			
			# Get group id
			it = self.__group_combobox.get_active_iter()
			self.__usermodel['gidNumber'] = [str(self.__group_model.get_value(it, 0))]
			
			self.__dialog.destroy()
			return self.__usermodel
		
