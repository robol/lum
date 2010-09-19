#
# -*- coding: utf-8 -*-

import gtk, os
from utilities import create_builder

class lumAbout():
    
    def __init__(self, datapath):
    
        self.__builder = create_builder("LumAbout.ui")
        
        dialog = self.__builder.get_object("about_dialog")
        
        dialog.run ()
        dialog.destroy ()
        
