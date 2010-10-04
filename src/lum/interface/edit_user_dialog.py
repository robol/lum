#
# -*- coding: utf-8 -*-
#

import gtk, os, gobject
from utilities import _, create_builder

class lumEditUserDialog():

    def __init__(self, datapath, usermodel, group_store):
        
        self.__builder = create_builder("LumEditUserDialog.ui")
        self.__dialog = self.__builder.get_object("dialog")
        
        self.__givenname_entry = self.__builder.get_object("givenname_entry")
        self.__sn_entry = self.__builder.get_object("sn_entry")
        self.__group_combobox = self.__builder.get_object("group_combobox")
        
        # Fill data
        self.__givenname_entry.set_text(usermodel.get_given_name())
        self.__sn_entry.set_text(usermodel.get_surname())
        
        self.__group_model = self.__builder.get_object("group_model")
                                       
        # Copy group data in the model
        self.__group_iter = None
        it = group_store.get_iter_first()
        while it is not None:
            gid = group_store.get_gid(it)
            group = group_store.get_group_name(it)
            new_it = self.__group_model.append((int(gid), group))
            if gid == int(usermodel.get_gid()):
                self.__group_iter = it
            it = group_store.iter_next(it)
                
        if (self.__group_iter is not None):
            self.__group_combobox.set_active_iter(self.__group_iter)
        
        # Shell and home
        self.__shell_entry = self.__builder.get_object("shell_entry")
        self.__shell_entry.set_text(usermodel.get_shell())
        self.__home_entry = self.__builder.get_object("home_entry")
        self.__home_entry.set_text(usermodel.get_home())
        self.__email_entry = self.__builder.get_object("email_entry")
        self.__email_entry.set_text(usermodel.get_email())
        
        self.__usermodel = usermodel

        self.__dialog.set_title(_("Editing user %s") % usermodel.get_username())
        
        
    def run(self):
        """Run the dialog"""
        
        if self.__dialog.run() == 0:
            self.__dialog.destroy()
            return None
        else:
            
            # Save data
            self.__usermodel.set_given_name(self.__givenname_entry.get_text())
            self.__usermodel.set_surname(self.__sn_entry.get_text())
            self.__usermodel.set_home(self.__home_entry.get_text())
            self.__usermodel.set_shell(self.__shell_entry.get_text())
            self.__usermodel.set_email(self.__email_entry.get_text())
            
            # Get group id
            it = self.__group_combobox.get_active_iter()
            self.__usermodel.set_gid(self.__group_model.get_value(it, 0))
            
            self.__dialog.destroy()
            return self.__usermodel
        
