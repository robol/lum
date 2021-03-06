#
# -*- coding: utf-8 -*-

import gtk, os
from lum.ldap_protocol import UserModel
from utilities import _, show_error_dialog, ask_question, create_builder

class lumNewUserDialog():
    
    def __init__(self, datapath, connection):
        
        signals = {
            'on_username_entry_focus_out_event':     self.guess_params,
        }
        
        self.__builder = create_builder("LumNewUserDialog.ui")
        
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
            email = self.__builder.get_object("email_entry").get_text()
            
            # Set uid to 0 so ldap_protocol will autodetermine the first free uid
            # when creating the user
            uid = 0
            
            group = self.__builder.get_object("group_entry").get_text()
            gid = self.__connection.gid_from_group(group)
            
            # Check if this is an existent user
            if self.__connection.is_present("uid=%s" % username):
                show_error_dialog(_("User %s is present, not overwriting it!") % username)
                self.__window.destroy()
                return None
            
            # Ask the user if he intended to create the group and destroy window
            # before the call to the ldap module, that could raise an exception
            # catched by our parent (i.e. lumApp)
            if gid is None:
                if ask_question(_("The group %s doesn't exists, create it now?") % group):
                    self.__window.destroy()
                    self.__connection.add_group(group)
                    gid = self.__connection.gid_from_group(group)
                else:
                    self.__window.destroy()
                    return None
            else:
                self.__window.destroy()
            
            # Fill UserModel
            self.usermodel = UserModel()
            self.usermodel.set_username(username)
            self.usermodel.set_gid(gid)
            self.usermodel.set_surname(sn)
            self.usermodel.set_given_name(givenName)
            self.usermodel.set_home(home)
            self.usermodel.set_shell(shell)
            self.usermodel.set_email(email)

        else:
            
            self.__window.destroy()
            
            
        

