#
# -*- coding: utf-8 -*-

import gtk, os

class lumAbout():
    
    def __init__(self, datapath):
    
        self.__builder = gtk.Builder()
        self.__builder.add_from_file(os.path.join(datapath, "ui/LumAbout.ui"))
        
        dialog = self.__builder.get_object("about_dialog")
        
        dialog.run ()
        dialog.destroy ()
        
