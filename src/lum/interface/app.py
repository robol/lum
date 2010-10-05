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
from lum.exceptions import *

# Import interface
from about import lumAbout
from new_user_dialog import lumNewUserDialog
from connect_dialog import lumConnectDialog
from password_entry import lumPasswordEntry
from edit_user_dialog import lumEditUserDialog
from menu_item import lumUserTreeViewMenu, lumGroupTreeViewMenu
from new_group_dialog import lumNewGroupDialog
from change_user_password_dialog import lumChangeUserPasswordDialog
from utilities import _, show_error_dialog, ask_question, create_builder, show_info_dialog
from stores import UserStore, GroupStore

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
    
        self.__group_store = GroupStore(self.__datapath)
        self.__user_store = UserStore(self.__datapath, self.__group_store)
        
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
            'on_filter_group_entry_changed':              self.group_refilter,
            'on_forget_password_menu_item_activate':    self.forget_password,
            'on_edit_user_menu_item_activate':            self.edit_user,
            'on_change_password_menu_item_activate': self.change_password,

            # Group menu callbacks
            'on_new_group_menuitem_activate':    self.new_group,
            'on_delete_group_menuitem_activate': self.delete_group,
            'on_properties_group_menuitem_activate': self.group_properties,
            
            # Popup menus
            'on_user_treeview_button_press_event':         self.on_user_treeview_button_press_event,
            'on_group_treeview_button_press_event':        self.on_group_treeview_button_press_event,
        }
        
        # Autoconnect signals
        self.__builder.connect_signals (signals)
        
        # Create initial configuration
        self.__configuration = Configuration()
        
        # Activate filter on users...
        self.__users_treefilter = self.__user_store.filter_new()
        self.__users_treefilter.set_visible_func(self.filter_users)

        # ...and groups
        self.__group_treefilter = self.__group_store.filter_new()
        self.__group_treefilter.set_visible_func(self.filter_groups)
        
        # Change the model of the treeview
        self.__builder.get_object("user_treeview").set_model(self.__users_treefilter)
        self.__builder.get_object("group_treeview").set_model(self.__group_treefilter)
        
        # Some initial values
        self.__uri, self.__bind_dn = None, None
        
        # Create popup menu
        self.__user_popup_menu = lumUserTreeViewMenu(self)
        self.__group_popup_menu = lumGroupTreeViewMenu(self)

    def __del__(self):
        lum_application = None
    
    def start(self):
        """Start lumApp"""
        
        # Show all
        self.__window.show_all()
        self.__connection = None
        
        
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
        key = self.__builder.get_object("filter_user_entry").get_text()
        
        if key == "":
            return True
        
        if key in model.get_value(treeiter, 0).lower():
            return True
        if key in model.get_value(treeiter, 1).lower():
            return True
        if key in model.get_value(treeiter, 2).lower():
            return True
            
        return False

    def filter_groups(self, model, treeiter, user_data = None):
        """Filter group based on user insertion in the filter entry"""
        key = self.__builder.get_object("filter_group_entry").get_text()
        if key == "":
            return True

        if key in model.get_value(treeiter, 1).lower():
            return True

        return False

    def __get_selected_user(self):
        """Obtain usermodel and a treeview iter
        of the selected user in the treeview"""
        treeview = self.__builder.get_object("user_treeview")

        # t_model is the GtkTreeFilterModel, and t_iter refers to it
        t_model, t_iter = treeview.get_selection().get_selected()

        if t_iter is None:
            # Then nothing is selected and we can return None
            return (None, None)

        it = t_model.convert_iter_to_child_iter(t_iter)
        usermodel = self.__user_store.get_usermodel(it)

        return usermodel, it

    def __get_selected_group(self):
        """Obtain selected group and a treeview iter
        of it or None, None if there is no group selected"""

        treeview = self.__builder.get_object("group_treeview")
        
        # t_model is the GtkTreeFilterModel and t_iter refers
        # to the entry in it
        t_model, t_iter = treeview.get_selection().get_selected()

        if t_iter is None:
            # Then there is nothing selected
            return (None, None)

        group = t_model.get_value(t_iter, 1)

        # Return group_name and iter to the group_store and not
        # to the GtkTreeFilterModel
        return (group, t_model.convert_iter_to_child_iter(t_iter))
        

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
        self.__users_treefilter.refilter()

    def group_refilter(self, entry):
        """Callback to refilter groups"""
        self.__group_treefilter.refilter()
        
        
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
            self.__user_popup_menu.username = usermodel.get_username()
            self.__user_popup_menu.popup(None, None, None, event.button, event.time)

    def on_group_treeview_button_press_event(self, group_treeview, event):
        """Catch button press on group treeview and show popup
        menu if the user right-clicked."""
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            pathinfo = group_treeview.get_path_at_pos(x,y)
            if pathinfo is None:
                return

            path, col, cellx, celly = pathinfo
            group_treeview.grab_focus()
            group_treeview.set_cursor(path, col, 0)
            group, t_iter = self.__get_selected_group()
            self.__group_popup_menu.group = group
            self.__group_popup_menu.popup(None, None, None, event.button, event.time)
        
    def delete_user(self, menu_item = None):
        """Delete the selected user"""
        usermodel, t_iter = self.__get_selected_user()

        if t_iter is None:
            show_info_dialog(_("Select a user to delete!"))
            return

        # Users tend to delete many things they do not want
        # to delete
        if not ask_question(_("Really delete user <b>%s</b>?") % usermodel.get_username()):
            return

        # Delete user from ldap first
        try:
            self.__connection.delete_user(usermodel.get_dn())
        except LumInsufficientPermissionsError:
            show_error_dialog(_("Insufficient permissions to delete user"))
            return None

        # Delete user from internal dictionary
        self.__user_model_store.pop(usermodel.get_username())

        # Delete user from ldap and from the user_store
        user_store = self.__builder.get_object("user_store")
        user_store.remove(t_iter)

        self.statusbar_update(_("User %s deleted.") % usermodel.get_username())
            
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
        self.__user_store.clear()
        self.__user_model_store = {}
        
        
    def reload_user_list(self, menu_item = None):
        """Reload user list in the main window"""
        if self.__check_connection():
            self.clear_user_list()
            users = self.__connection.get_users()
            self.update_group_list()
            for user in users:
                self.push_user(user)

    def clear_group_list(self):
        """Clear group list"""
        self.__group_store.clear()

    def update_group_list(self, menu_item = None):
        """Update group list and internal group dictionary"""
        if self.__check_connection():
            for gid, group in self.__connection.get_groups().items():
                self.__group_store.append(gid, group)

            
                
    def edit_user(self, menu_item = None):
        """Edit selected user"""
        usermodel, t_iter = self.__get_selected_user()
        if t_iter is None: 
            show_info_dialog(_("Select a user to modify"))
            return

        # Create the dialog
        ldap_data = usermodel.to_ldif()
        ldap_dn   = "uid=%s,ou=%s" % (usermodel.get_username(), self.__users_ou)
        old_user = UserModel((ldap_dn, ldap_data))
        dialog = lumEditUserDialog(self.__datapath, usermodel, self.__group_store)
        
        new_usermodel = dialog.run()
        if (new_usermodel is not None):

            try:
                self.__connection.modify_user(old_user, new_usermodel)
            except LumInsufficientPermissionsError:
                show_error_dialog(_("Insufficient permissions to edit user"))
                return None

            self.statusbar_update(_("User %s successfully modified") % new_usermodel.get_username())
            
            # TODO: Reload only selected user
            self.reload_user_list()

    def change_password(self, menu_item = None):
        """Change password of selected user"""
        usermodel, t_iter = self.__get_selected_user()
        if t_iter is None:
            show_info_dialog(_("You need to select a user to change its password"))
            return

        password_dialog = lumChangeUserPasswordDialog(self.__datapath, usermodel.get_username())
        new_password = password_dialog.run()
        if new_password is None:
            return False
        else:
            try:
                self.__connection.change_password(usermodel.get_username(), new_password)
            except LumInsufficientPermissionsError:
                show_error_dialog(_("Insufficient permissions to change user password"))
                return False
            return True

                
    def push_user(self, usermodel):
        """Add a user on the treeview in the main window"""
        self.__user_store.append(usermodel)
        
    def statusbar_update(self, message):
        """Update statusbar with new message"""
        statusbar = self.__builder.get_object("statusbar")
        statusbar.push(0, message)
        
    def create_new_user_dialog(self, menu_item):
        """Create new user"""
        if not self.__check_connection():
            return None

        new_user_dialog = lumNewUserDialog(self.__datapath, self.__connection)
       
        try:
            new_user_dialog.run()
        except LumInsufficientPermissionsError:
            show_error_dialog(_("Insufficient permissions to accomplish operation"))
            return None
        
        if new_user_dialog.usermodel is not None:
            if self.__check_connection():
                new_user_dialog.usermodel.set_dn("uid=%s,%s" % (new_user_dialog.usermodel.get_username(),
                                                                self.__users_ou))

                try:
                    self.__connection.add_user(new_user_dialog.usermodel)
                except LumAlreadyExistsError:
                    show_error_dialog(_("User <b>%s</b> already exists in the ldap tree, " + 
                                        "cannot create one more") % new_user_dialog.usermodel.get_username())
                    return None
                except LumInsufficientPermissionsError:
                    show_error_dialog(_("Insufficient permissions to create the user"))
                    return None
                self.statusbar_update(_("User %s created correctly.") % new_user_dialog.usermodel.get_username())

                # Reload user list because the dialog may have created a new group
                # and then pushing the user will not update the group list too
                self.reload_user_list()


    def new_group(self, menu_item = None):
        """Create a new group catching the callback from menu"""
        if not self.__check_connection():
            return None

        new_group_dialog = lumNewGroupDialog(self.__datapath,
                                             self.__connection)
        group_name, gid = new_group_dialog.run()

        if group_name is not None:
            try:
                self.__connection.add_group(group_name, gid)
            except LumInsufficientPermissionsError:
                show_error_dialog(_("Insufficient permissions to create group"))
                return None
            except LumAlreadyExistsError:
                show_error_dialog(_("Group <b>%s</b> already exists in the database," + 
                                    " cannot add one more.") % group_name)
                return None

            self.__group_store.append(gid, group_name)
            self.statusbar_update(_("Group %s successfully created.") % group_name)

    def delete_group(self, menu_item = None):
        """Delete the group selected in the group_treeview"""
        if not self.__check_connection():
            return None

        group, t_iter = self.__get_selected_group()

        # If nothing is selected we can return and do nothing.
        # We should only notify the user that what he would like
        # to do can not be done now.
        if t_iter is None:
            show_info_dialog(_("Select a group before asking for its deletion."))
            return

        # Users tend to delete many things they do not want to delete
        if len(self.__connection.get_members(group)) == 0:
            question = _("Really delete group <b>%s</b>?") % group
        else:
            question = _("Really delete the non empty group <b>%s</b>?" +
                         " This will lead to integrity problems.") % group
        if not ask_question(question):
            return

        # Finally we delete the group
        try:
            self.__connection.delete_group(group)
        except LumInsufficientPermissionsError:
            show_error_dialog(_("Insufficient permissions to delete group"))
            return None

        # and delete the group from the treeview
        self.__group_store.remove(t_iter)

        # Finally show the successful operation in the statusbar
        self.statusbar_update(_("Group %s successfully deleted.") % group)

    def group_properties(self, menu_item = None):
        """View selected group properties, such as members and
        gidNumber"""

        if not self.__check_connection():
            return None

        group, t_iter = self.__get_selected_group()
        if t_iter is None:
            show_info_dialog(_("Select a group to view its properties"))

        # Get group_members, that are the only interesting property
        # we can get from ldap
        group_members = self.__connection.get_members(group)

        # Get gid
        gid = self.__group_store.get_gid(t_iter)

        # Show info dialog
        dialog_text =  _("<b>Name:</b> %s\n") % group
        dialog_text += "<b>Gid</b>: %s\n" % gid
        if len(group_members) > 0:
            dialog_text += _("<b>Members</b>: ")
            dialog_text += ", ".join(group_members)
        else:
            dialog_text += _("This group is empty.")

        # Show info dialog.
        show_info_dialog(dialog_text)

 
            
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
        
        



