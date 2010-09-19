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
import time

# Require a recent pygtk version
pygtk.require("2.0")

# Import modules from lum
from lum.ldap_protocol import UserModel, Connection
from lum.configuration import Configuration
from lum.exceptions import LumError

# Import interface
from about import lumAbout
from new_user_dialog import lumNewUserDialog
from connect_dialog import lumConnectDialog
from password_entry import lumPasswordEntry
from edit_user_dialog import lumEditUserDialog
from menu_item import lumTreeViewMenu
from change_user_password_dialog import lumChangeUserPasswordDialog
from utilities import _, show_error_dialog, ask_question, create_builder

lum_application = None

class lumApp(gobject.GObject):

    def __init__(self):

        # Quite a hack, but working
        self.__datapath = os.path.realpath(os.path.join(__file__, os.path.pardir))

        global lum_application
        if lum_application is not None:
            raise LumErorr("Cannot create more that one lum_application!")
        else:
            lum_application = self
    
        # Images
        self.__user_image = gtk.Image()
        self.__user_image.set_from_file(os.path.join(self.__datapath, "ui/user.png"))
        self.__user_image = self.__user_image.get_pixbuf()
        
        # Internal space for usermodels
        # Usermodel will be saved in a dictionary using uids as keys,
        # so it will be easy to get them even from entry in the treeview
        self.__user_model_store = {}
        
        # Gobject constructor
        gobject.GObject.__init__ (self)
        
        # Load interface file
        self.__builder = create_builder("LumApp.ui")
        
        # Load main window
        self.__window = self.__builder.get_object("window")
        
        # Signal definition
        signals = {
        
            # Quit signals
            'on_quit_menu_item_activate':         gtk.main_quit,
            'window_destroy_event_cb':            gtk.main_quit,
            'on_window_destroy':                gtk.main_quit,
            
            # Callbacks
            'on_about_menu_item_activate':        self.show_about_dialog,
            'on_new_user_menu_item_activate':    self.create_new_user_dialog,
            'on_connect_menu_item_activate':     self.connect,
            'on_reload_user_list_menu_item_activate':     self.reload_user_list,
            'on_delete_user_menu_item_activate':        self.delete_user,
            'on_filter_entry_changed':                    self.refilter,
            'on_forget_password_menu_item_activate':    self.forget_password,
            'on_edit_user_menu_item_activate':            self.edit_user,
            
            # Popup menus
            'on_user_treeview_button_press_event':         self.on_user_treeview_button_press_event,
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
        
        # Make the list sorted
        user_store = self.__builder.get_object("user_store")
        user_store.set_sort_func(1, self.sort)
        user_store.set_sort_column_id(1, gtk.SORT_ASCENDING)
        
        # Some initial values
        self.__uri, self.__bind_dn = None, None
        
        # Create popup menu
        self.__popup_menu = lumTreeViewMenu(self)

    def __del__(self):
        lum_application = None
        
    
    def sort(self, model, iter1, iter2):
        return (model.get_value(iter1, 0).lower() > model.get_value(iter2, 0).lower())
        
    def start(self):
        """Start lumApp"""
        
        # Show all
        self.__window.show_all()
        self.__connection = None
        
        self.__group_dict = dict()

        
    def connect(self, menu_item = None):
        """Connect to server"""
        
        # Determine which server to connect to
        connect_dialog = lumConnectDialog(self.__datapath, self.__configuration)
        uri, bind_dn, base_dn, users_ou, groups_ou = connect_dialog.run()
        
        # Update internal information
        self.__uri = uri 
        self.__bind_dn = bind_dn
        self.__base_dn = base_dn
        self.__users_ou = users_ou
        self.__groups_ou = groups_ou
        
        if uri is None:
            return
        
        # Add base_dn if necessary
        if not self.__bind_dn.endswith(self.__base_dn): self.__bind_dn += ",%s" % self.__base_dn
        if not self.__users_ou.endswith(self.__base_dn): self.__users_ou += ",%s" % self.__base_dn
        if not self.__groups_ou.endswith(self.__base_dn): self.__groups_ou += ",%s" % self.__base_dn
        
        # Get password from keyring
        password = self.ask_password()
        
        # Notify user of connection
        self.statusbar_update(_("Connecting to %s.") % uri)
        
        # Try to connect to the specified server
        try:
            self.__connection = Connection(uri = self.__uri, bind_dn = self.__bind_dn, password = password, 
                                           base_dn = self.__base_dn, users_ou = self.__users_ou, 
                                           groups_ou = self.__groups_ou)
        except LumError:
            
            # If we can't, maybe password is wrong, so ask it again
            self.forget_password()
            password = self.ask_password()
            
            # and retry the connection. But if we fail even this time, then
            # abort
            try:
                self.__connection = Connection(uri = self.__uri, bind_dn = self.__bind_dn, password = password, 
                                           base_dn = self.__base_dn, users_ou = self.__users_ou, 
                                           groups_ou = self.__groups_ou)
            except:
            
                # You had two opportunities, and both are gone. 
                show_error_dialog(
                    _("Error while connecting to the server, check your credentials and your connectivity"))
                
                self.__connection = None
                
                self.statusbar_update(_("Connection failed."))
        
        # If you managed to open the connection, show it in the status bar
        if self.__connection is not None:
            self.statusbar_update(_("Connection to %s initialized") % uri)
            self.reload_user_list()
            
    def filter_users(self, model, treeiter, user_data = None):
        """Filter users based on what is placed in filter_entry"""
        key = self.__builder.get_object("filter_entry").get_text()
        
        if key == "":
            return True
        
        if key in model.get_value(treeiter, 0).lower():
            return True
        if key in model.get_value(treeiter, 1).lower():
            return True
        if key in model.get_value(treeiter, 2).lower():
            return True
            
        return False

    def __get_selected_user(self):
        """Obtain usermodel and a treeview iter
        of the selected user in the treeview"""
        treeview = self.__builder.get_object("user_treeview")
        t_model, t_iter = treeview.get_selection().get_selected()
        if t_iter is None:
            return (None, None)
        username = t_model.get_value(t_iter, 0)
        try:
            usermodel = self.__user_model_store[username]
            return (usermodel, t_iter)
        except KeyError:
            show_error_dialog(_("Internal application error! Try reloading user list"))
            return (None, None)
        

    def ask_password(self):
        """A simple routine that ask for password, if it is not yet in
        the keyring"""
        display_name = "@".join([self.__bind_dn, self.__uri])
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
                'username':        self.__bind_dn,
                'server':        self.__uri,
                'protocol':        'ldap',
                'port':            '389',
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
        
    def on_user_treeview_button_press_event(self, user_treeview, event):
        """Catch press button event on treeview and, if the user right
        clicked on it, open the popup menu"""
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            pathinfo = user_treeview.get_path_at_pos(x,y)
            if pathinfo is None:
                return
            path, col, cellx, celly = pathinfo
            user_treeview.grab_focus()
            user_treeview.set_cursor(path, col, 0)
            usermodel, t_iter = self.__get_selected_user()
            self.__popup_menu.username = usermodel.get_username()
            self.__popup_menu.popup(None, None, None, event.button, event.time)
        
    def delete_user(self, menu_item = None):
        """Delete the selected user"""
        usermodel, t_iter = self.__get_selected_user()

        # Delete user from internal dictionary
        self.__user_model_store.remove(usermodel)

        # Delete user from ldap and from the user_store
        user_store = self.__builder.get_object("user_store")
        user_store.remove(user_model.convert_iter_to_child_iter(t_iter))
        self.__connection.delete_user(usermodel.get_dn())
        self.statusbar_update(_("User %s deleted.") % username)
            
    def forget_password(self, menu_item = None):
        if not gnomekeyring.is_available():
            return None
        if self.__uri is None or self.__bind_dn is None:
            return None
        display_name = "@".join([self.__bind_dn, self.__uri])
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
            self.__group_dict = self.__connection.get_groups()
            for user in users:
                self.push_user(user)
            
                
    def edit_user(self, menu_item = None):
        """Edit selected user"""
        usermodel, t_iter = self.__get_selected_user()
        if t_iter is None: 
            return

        # Create the dialog
        ldap_data = usermodel.to_ldif()
        ldap_dn   = "uid=%s,ou=%s" % (usermodel.get_username(), self.__users_ou)
        old_user = UserModel((ldap_dn, ldap_data))
        dialog = lumEditUserDialog(self.__datapath, usermodel, self.__group_dict)
        
        new_usermodel = dialog.run()
        if (new_usermodel is not None):
            self.__connection.modify_user(old_user, new_usermodel)

            self.statusbar_update(_("User %s successfully modified") % new_usermode.get_username())
            
            # TODO: Reload only selected user
            self.reload_user_list()

    def change_password(self):
        """Change password of selected user"""
        usermodel, t_iter = self.__get_selected_user()
        if t_iter is None:
            return

        password_dialog = lumChangeUserPasswordDialog(self.__datapath, usermodel.get_username())
        new_password = password_dialog.run()
        if new_password is None:
            return False
        else:
            self.__connection.change_password(usermodel.get_username(), new_password)
            return True

                
    def push_user(self, usermodel):
        """Add a user on the treeview in the main window"""
        user_store = self.__builder.get_object("user_store")
        if self.__group_dict.has_key(usermodel.get_gid()):
            group = self.__group_dict[usermodel.get_gid()]
        else:
            group = "unknown"
        user_store.append((usermodel.get_username(), usermodel.get_gecos(),
                            group, self.__user_image))
        self.__user_model_store[usermodel.get_username()] = usermodel
        
    def statusbar_update(self, message):
        """Update statusbar with new message"""
        statusbar = self.__builder.get_object("statusbar")
        statusbar.push(0, message)
        
    def create_new_user_dialog(self, menu_item):
        """Create new user"""
        if not self.__check_connection():
            return None

        new_user_dialog = lumNewUserDialog(self.__datapath, self.__connection)
        new_user_dialog.run()
        
        if new_user_dialog.usermodel is not None:
            if self.__check_connection():
                self.__connection.add_user(new_user_dialog.usermodel)
                self.statusbar_update(_("User %s created correctly.") % new_user_dialog.usermodel.get_username())
        self.reload_user_list()
            
    def __check_connection(self):
        if self.__connection is None:
            if ask_question(_("Not connected to any LDAP server, connect now?")):
                self.connect ()
            else:
                return False
        if self.__connection is not None:
            return True
        else:
            show_error_dialog(_("Error while connecting to LDAP server, aborting operation."))
            return False
        
        



