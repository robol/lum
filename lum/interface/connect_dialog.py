#
# -*- coding: utf-8 -*-

import gtk, os

class lumConnectDialog():


	def __init__(self, datapath, configuration):
	
		self.__configuration = configuration
		
		self.__builder = gtk.Builder()
		self.__builder.add_from_file(os.path.join(datapath, "ui/LumConnectDialog.ui"))
		
		self.__dialog = self.__builder.get_object("connect_dialog")
		
		for renderer in ('uri_cellrenderer', 'bind_dn_cellrenderer', 'base_dn_cellrenderer',
						 'users_ou_cellrenderer', 'groups_ou_cellrenderer'):
			self.__builder.get_object(renderer).set_property("editable", True)
		
		
		signals = {
			'on_connect_button_activate':		self.on_connect_button_cb,
			'on_add_button_activate':			self.on_add_button_cb,
			'on_uri_cellrenderer_edited':		self.on_uri_edited,
			'on_bind_dn_edited':	self.on_bind_dn_edited,
			'on_base_dn_edited':	self.on_base_dn_edited,
			'on_users_ou_edited': 	self.on_users_ou_edited,
			'on_groups_ou_edited':	self.on_groups_ou_edited,
			'on_uri_cellrenderer_editing_started': self.on_uri_start_editing,
			'on_remove_button_clicked': 		self.on_remove_button_cb,
		}
		
		self.__builder.connect_signals(signals)
		
		image = gtk.Image()
		image.set_from_file(os.path.join("ui/server.png"))
		self.__pixbuf = image.get_pixbuf()
		
		self.__credentials = (None, None, None, None, None)
		self.__old_uri = None
		
		for uri in self.__configuration.sections():
			if not self.__configuration.has_option(uri, "bind_dn"):
				bind_dn = "Insert bind dn"
			else:
				bind_dn = self.__configuration.get(uri, "bind_dn")
			if self.__configuration.has_option(uri, "base_dn"):
				base_dn = self.__configuration.get(uri, "base_dn")
			else:
				base_dn = "Insert base dn"
			if self.__configuration.has_option(uri, "users_ou"):
				users_ou = self.__configuration.get(uri, "users_ou")
			else:
				users_ou = "Insert users organizational unit"
			if self.__configuration.has_option(uri, "groups_ou"):
				groups_ou = self.__configuration.get(uri, "groups_ou")
			else:
				groups_ou = "Inserto groups organizational unit"
			
			self.__builder.get_object("server_store").append((self.__pixbuf, uri, bind_dn,
											base_dn, users_ou, groups_ou))
		
		
	def run(self):
	
		# If the user click Cancel we return None
		self.__dialog.run ()
		self.__dialog.destroy()
		return self.__credentials
			
			
	def on_connect_button_cb(self, button):
		"""Store the URI and the bind_dn selected in
		the __credential variable of the object"""
		# Get selected entry
		treeview = self.__builder.get_object("treeview")
		t_model, t_iter = treeview.get_selection().get_selected()
		
		if t_iter is None:
			# TODO: Messagebox
			self.__credentials = (None, None, None, None, None)
		else:
			self.__credentials = (t_model.get_value(t_iter, 1),
								  t_model.get_value(t_iter, 2),
								  t_model.get_value(t_iter, 3),
								  t_model.get_value(t_iter, 4),
								  t_model.get_value(t_iter, 5))
								  
	def on_remove_button_cb(self, button):
		treeview = self.__builder.get_object("treeview")
		t_model, t_iter = treeview.get_selection().get_selected()
		
		uri = t_model.get_value(t_iter, 1)
		if self.__configuration.has_section(uri):
			self.__configuration.remove_section(uri)
		t_model.remove(t_iter)
		
	def on_add_button_cb(self, button):
		"""Add a new entry"""
		t_model = self.__builder.get_object("server_store")
		t_model.append((self.__pixbuf, "Insert server name", "Insert bind DN", "Insert base DN",
				"Insert users organizational unit", "Insert group organizational unit"))
		
		
	def on_uri_edited(self, renderer, path, new_text):
		treeview = self.__builder.get_object("treeview")
		t_model, t_iter = treeview.get_selection().get_selected()
		if t_iter is None:
			return
		else:
			t_model.set(t_iter, 1, new_text)
		
		if self.__old_uri == new_text:
			return
		
		if self.__configuration.has_section(self.__old_uri):
			for option in self.__configuration.options():
				o = self.__configuration.get(self.__old_uri, option)
				self.__configuration.set(new_text, option)
			self.__configuration.remove_section(self.__old_uri)
		if not self.__configuration.has_section(new_text):
			self.__configuration.add_section(new_text)
			
	def on_uri_start_editing(self, renderer, editable, path):
		"""Save old uri for comparison"""
		treeview = self.__builder.get_object("treeview")
		t_model, t_iter = treeview.get_selection().get_selected()
		self.__old_uri = t_model.get_value(t_iter, 1)
	
	def on_option_edited(self, renderer, path, new_text, option, field):
		treeview = self.__builder.get_object("treeview")
		t_model, t_iter = treeview.get_selection().get_selected()
		if t_iter is None:
			return
		else:
			t_model.set(t_iter, int(field), new_text)
		
		uri = t_model.get_value(t_iter, 1)
		
		self.__configuration.set(uri, option, new_text)
	
	def on_bind_dn_edited(self, renderer, path, new_text):
		self.on_option_edited(renderer, path, new_text, "bind_dn", 2)
		
	def on_base_dn_edited(self, renderer, path, new_text):
		self.on_option_edited(renderer, path, new_text, "base_dn", 3)
		
	def on_users_ou_edited(self, renderer, path, new_text):
		self.on_option_edited(renderer, path, new_text, "users_ou", 4)
	
	def on_groups_ou_edited(self, renderer, path, new_text):
		self.on_option_edited(renderer, path, new_text, "groups_ou", 5)
