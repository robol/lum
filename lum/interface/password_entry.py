#
# -*- coding: utf-8 -*-

import gtk, os
from utilities import create_builder

class lumPasswordEntry():

    def __init__(self, datapath):
    
        self.__builder = create_builder("LumPasswordEntry.ui")
        
        self.__dialog = self.__builder.get_object("password_dialog")
        
    def run(self):
    
        if (self.__dialog.run() == 1):
            password = self.__builder.get_object("password_entry").get_text()
        else:
            password = None
            
        self.__dialog.destroy ()
        return password
        
