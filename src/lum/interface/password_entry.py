#
# -*- coding: utf-8 -*-

import gtk, os
from utilities import create_builder

class lumPasswordEntry():

    def __init__(self, datapath):
    
        self.__builder = create_builder("LumPasswordEntry.ui")
        
        self.__dialog = self.__builder.get_object("password_dialog")

        pe = self.__builder.get_object("password_entry")
        pe.connect("activate", lambda widget : self.__dialog.response(1))

        spe = self.__builder.get_object("ssh_password_entry")
        spe.connect("activate", lambda widget : self.__dialog.response(1))
        
    def run(self):

        ret = self.__dialog.run()

        if (ret == 1):
            password = self.__builder.get_object("password_entry").get_text()
            ssh_password = self.__builder.get_object("ssh_password_entry").get_text()
        else:
            password = None
            ssh_password = None
            
        self.__dialog.destroy ()
        return password, ssh_password
        
