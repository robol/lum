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
        self.__givenname_entry.set_text(usermodel.get_given_name())
        self.__sn_entry.set_text(usermodel.get_surname())
        
        self.__group_model = self.__builder.get_object("group_model")
                                           
        self.__group_iter = None
        group_list = group_dict.items()
        group_list.sort()
        for gid, group in group_list:
            it = self.__group_model.append((int(gid), group))
            if gid == usermodel.get_gid():
                self.__group_iter = it
                
        if (self.__group_iter is not None):
            self.__group_combobox.set_active_iter(self.__group_iter)
        
        # Shell and home
        self.__shell_entry = self.__builder.get_object("shell_entry")
        self.__shell_entry.set_text(usermodel.get_shell())
        self.__home_entry = self.__builder.get_object("home_entry")
        self.__home_entry.set_text(usermodel.get_home())
        
        self.__usermodel = usermodel

        self.__dialog.set_title("Modifica di %s" % usermodel.get_username())
        
        
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
            
            # Get group id
            it = self.__group_combobox.get_active_iter()
            self.__usermodel.set_gid(self.__group_model.get_value(it, 0))
            
            self.__dialog.destroy()
            return self.__usermodel
        
