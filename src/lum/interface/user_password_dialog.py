#
# -*- coding: utf-8 -*-
#

import gtk, os
from utilies import _, show_error_dialog, create_builder

class lumUserPasswordDialog():

    def __init__(self, datapath, username):
        
        self.__builder = create_builder("ui/LumUserPasswordDialog.ui")
        self.__dialog = self.__builder.get_object("dialog")
        self.__dialog.set_title(_("Set password for user %s") % username)
    def run(self):
        
        if self.__dialog.run():
            password_1 = self.__builder.get_object("password_entry_1").get_text()
            password_2 = self.__builder.get_object("password_entry_2").get_text()
            
            if password_1 != password_2:
                show_error_dialog(_("Not matching passwords, retry."))
                return self.run()
            else:
                self.__dialog.destroy()
                return password_1
        self.__dialog.destroy()
        return None

