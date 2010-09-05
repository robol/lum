#
# -*- coding: utf-8 -*-
#
# This file is part of lum, the LDAP User Manager
# 
# Author: Leonardo Robol <robol@poisson.phc.unipi.it>
# Date: 5 Sep 2010
#
#

import os
from ConfigParser import ConfigParser

class Configuration():
	"""Configuration objects allow
	code to fetch user preferences and 
	to change them permanently rewriting
	the user Confugration file."""

	def __init__(self):
		
		# Check if configuration directory exists
		# or can be created. If it doesn't, load default
		# settings and do not save new values
		if (self.user_has_directory()):
			self.__persistent = True
		else:
			self.__persistent = False
			
		# Load configuration default values and, if it exists,
		# load values in the configuration file
		self.__conf = ConfigParser()
		
		# Add an [LDAP] section
		self.__conf.add_section ("LDAP")
		self.__conf.set("LDAP", "uri", "ldap://localhost")
		self.__conf.set("LDAP", "base_dn", "dc=example,dc=com")
		self.__conf.set("LDAP", "bind_dn", "cn=admin,dc=example,dc=com")
		self.__conf.set("LDAP", "users_ou", "ou=People,dc=example,dc=com")
		self.__conf.set("LDAP", "groups_ou", "ou=Groups,dc=example,dc=com")
		
		if self.__persistent and os.path.exists(self.__conf_file):
			try:
				self.__conf.read(self.__conf_file)
			except OSError:
				self.__persistent = False
			
	def user_has_directory(self):
		"""Check if user has a .lum directory in the
		home or if it can be created.
		"""
		
		conf_dir = os.path.expanduser("~/.lum")
		self.__conf_file = os.path.join(conf_dir, "lum.conf")
		
		if os.path.exists(conf_dir):
			return True
		else:
			try:
				os.mkdir(conf_dir)
			except OSError:
				return False
				
		return True
		
	def get(self, section, option):
		"""Get an option"""
		
		return self.__conf.get(section, option)
		
	def lock(self):
		"""Lock configuration directory"""
		while os.path.exists(self.__lock_file):
			sleep(30)
		with open(self.__lock_file, "w") as lock_file:
			lock_file.write("Lum lock")
	
	def unlock(self):
		"""Unlock configuration directory"""
		if os.path.exists(self.__lock_file):
			os.remove(self.__lock_file)
		
	def set(self, section, option, value):
		"""Set an option"""
		self.__conf.set(section, option, value)
		if self.__persistent:
			try:
				self.lock()
				with open(self.__conf_file, "w") as conf_file:
					self.__conf.write(conf_file)
			except OSError:
				self.__persistent = False
			finally:
				self.unlock()
				
				
