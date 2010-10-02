#
# -*- coding: utf-8 -*-

import gtk, os
from utilities import _, create_builder
from new_server_dialog import lumNewServerDialog

class lumConnectDialog():


    def __init__(self, datapath, configuration):
    
        self.__configuration = configuration
        
        self.__builder = create_builder("LumConnectDialog.ui")
        self.__dialog = self.__builder.get_object("connect_dialog")
        
        for renderer in ('uri_cellrenderer', 'bind_dn_cellrenderer', 'base_dn_cellrenderer',
                         'users_ou_cellrenderer', 'groups_ou_cellrenderer'):
            self.__builder.get_object(renderer).set_property("editable", True)
        
        
        signals = {
            'on_connect_button_activate':        self.on_connect_button_cb,
            'on_add_button_activate':            self.on_add_button_cb,
            'on_uri_cellrenderer_edited':        self.on_uri_edited,
            'on_bind_dn_edited':    self.on_bind_dn_edited,
            'on_base_dn_edited':    self.on_base_dn_edited,
            'on_users_ou_edited':     self.on_users_ou_edited,
            'on_groups_ou_edited':    self.on_groups_ou_edited,
            'on_uri_cellrenderer_editing_started': self.on_uri_start_editing,
            'on_remove_button_clicked':         self.on_remove_button_cb,
            
            # Activate
            'on_treeview_row_activated':            self.on_connect_button_cb,
        }
        
        self.__builder.connect_signals(signals)
        
        image = gtk.Image()
        image.set_from_file(os.path.join(datapath, "ui/server.png"))
        self.__pixbuf = image.get_pixbuf()
        
        self.__credentials = (None, None, None, None, None)
        self.__old_uri = None
        
        for uri in self.__configuration.sections():
            if not self.__configuration.has_option(uri, "bind_dn"):
                bind_dn = _("Insert bind dn")
            else:
                bind_dn = self.__configuration.get(uri, "bind_dn")
            if self.__configuration.has_option(uri, "base_dn"):
                base_dn = self.__configuration.get(uri, "base_dn")
            else:
                base_dn = _("Insert base dn")
            if self.__configuration.has_option(uri, "users_ou"):
                users_ou = self.__configuration.get(uri, "users_ou")
            else:
                users_ou = _("Insert users organizational unit")
            if self.__configuration.has_option(uri, "groups_ou"):
                groups_ou = self.__configuration.get(uri, "groups_ou")
            else:
                groups_ou = _("Insert groups organizational unit")
            
            self.__builder.get_object("server_store").append((self.__pixbuf, uri, bind_dn,
                                            base_dn, users_ou, groups_ou))

        self.__dialog.set_title(_("Connection to LDAP server"))
        
        
    def run(self):
    
        # If the user click Cancel we return None
        self.__dialog.run ()
        self.__dialog.destroy()
        return self.__credentials
            
            
    def on_connect_button_cb(self, widget):
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
        # Create new server dialog
        dialog = lumNewServerDialog()
        t_model = self.__builder.get_object("server_store")
        uri, bind_dn, base_dn, users_ou, groups_ou = dialog.run()
        if uri is None:
            return None
        it = t_model.append((self.__pixbuf, uri, bind_dn,
                             base_dn, users_ou, groups_ou))

        # Call this to update the configuration
        if not self.__configuration.has_section(uri):
            self.__configuration.add_section(uri)

        self.__configuration.set(uri, "bind_dn", bind_dn)
        self.__configuration.set(uri, "base_dn", base_dn)
        self.__configuration.set(uri, "users_ou", users_ou)
        self.__configuration.set(uri, "groups_ou", groups_ou)
        
        
    def on_uri_edited(self, renderer, path, new_text):
        treeview = self.__builder.get_object("treeview")
        t_model, t_iter = treeview.get_selection().get_selected()
        if t_iter is None:
            return
        else:
            t_model.set(t_iter, 1, new_text)
        
        if self.__old_uri == new_text:
            return
        
        # If the selected section exists, then we need to add
        # it and then copy all the data
        if not self.__configuration.has_section(new_text):
            self.__configuration.add_section(new_text)

        # Copy data from the old section and then
        # delete it
        if self.__configuration.has_section(self.__old_uri):
            for option in self.__configuration.options(self.__old_uri):
                o = self.__configuration.get(self.__old_uri, option)
                self.__configuration.set(new_text, option, o)
            self.__configuration.remove_section(self.__old_uri)            

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
