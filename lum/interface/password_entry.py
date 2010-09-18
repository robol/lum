#
# -*- coding: utf-8 -*-

import gtk, os

class lumPasswordEntry():

    def __init__(self, datapath):
    
        self.__builder = gtk.Builder()
        self.__builder.add_from_file(os.path.join(datapath, "ui/LumPasswordEntry.ui"))
        
        self.__dialog = self.__builder.get_object("password_dialog")
        
    def run(self):
    
        if (self.__dialog.run() == 1):
            password = self.__builder.get_object("password_entry").get_text()
        else:
            password = None
            
        self.__dialog.destroy ()
        return password
        
