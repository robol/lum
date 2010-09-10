#
# -*- coding: utf-8 -*-

import gtk, os

class lumConnectDialog():


	def __init__(self, datapath, configuration):
	
		self.__configuration = configuration
		
		self.__builder = gtk.Builder()
		self.__builder.add_from_file(os.path.join(datapath, "ui/LumConnectDialog.ui"))
		
		self.__dialog = self.__builder.get_object("connect_dialog")
		
		self.__builder.get_object("uri_cellrenderer").set_property("editable", True)
		self.__builder.get_object("bind_dn_cellrenderer").set_property("editable", True)
		
		
		signals = {
			'on_connect_button_activate':		self.on_connect_button_cb,
			'on_add_button_activate':			self.on_add_button_cb,
			'on_uri_cellrenderer_edited':		self.on_uri_edited,
			'on_bind_dn_cellrenderer_edited':	self.on_bind_dn_edited,
			'on_uri_cellrenderer_editing_started': self.on_uri_start_editing,
		}
		
		self.__builder.connect_signals(signals)
		
		image = gtk.Image()
		image.set_from_file(os.path.join("ui/server.png"))
		self.__pixbuf = image.get_pixbuf()
		
		self.__credentials = (None, None)
		self.__old_uri = None
		
		
	def run(self):
	
		# If the user click Cancel we return None
		if self.__dialog.run() == 0:
			self.__dialog.destroy()
			return (None, None)
		else:
			self.__dialog.destroy()
			return self.__credentials
			
			
	def on_connect_button_cb(self, button):
		"""Store the URI and the bind_dn selected in
		the __credential variable of the object"""
		# Get selected entry
		treeview = self.__builder.get_object("treeview")
		t_model, t_iter = treeview.get_selection().get_selected()
		
		if t_iter is None:
			self.__credentials = (None, None)
		else:
			self.__credentials = (t_model.get_value(t_iter, 0),
								  t_model.get_value(t_iter, 1))
		
	def on_add_button_cb(self, button):
		"""Add a new entry"""
		t_model = self.__builder.get_object("server_store")
		t_model.append(("Insert server name", "Insert bind DN", self.__pixbuf))
		
		
	def on_uri_edited(self, renderer, path, new_text):
		treeview = self.__builder.get_object("treeview")
		t_model, t_iter = treeview.get_selection().get_selected()
		if t_iter is None:
			return
		else:
			t_model.set(t_iter, 0, new_text)
		
		if self.__old_uri == new_text:
			return
			
			
		self.__configuration.add_section(new_text)
		
		if self.__configuration.has_section(self.__old_uri):
			for option in self.__configuration.options():
				o = self.__configuration.get(self.__old_uri, option)
				self.__configuration.set(new_text, option)
			self.__configuration.remove_section(self.__old_uri)
			
	def on_uri_start_editing(self, renderer, editable, path):
		"""Save old uri for comparison"""
		print "uei"
		treeview = self.__builder.get_object("treeview")
		t_model, t_iter = treeview.get_selection().get_selected()
		self.__old_uri = t_model.get_value(t_iter, 0)
	
	def on_bind_dn_edited(self, renderer, path, new_text):
		treeview = self.__builder.get_object("treeview")
		t_model, t_iter = treeview.get_selection().get_selected()
		if t_iter is None:
			return
		else:
			t_model.set(t_iter, 1, new_text)
		
		uri = t_model.get_value(t_iter, 0)
		self.__configuration.set(uri, "bind_dn", new_text)
	
	
