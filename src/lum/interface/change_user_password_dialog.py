#
# -*- coding: utf-8 -*-
#

import gtk, os
from utilities import show_error_dialog, _, create_builder

# Maximum number of tries for the password
max_tries = 3

class lumChangeUserPasswordDialog():

    def __init__(self, datapath, username, count = 0):

        # Create the gtk Builder and load interface files
        self.__builder = create_builder("LumChangeUserPasswordDialog.ui")

        self.__dialog = self.__builder.get_object("dialog")
        self.__datapath = datapath
        self.__username = username
        self.__count = count + 1

    def run(self):

        if self.__count > max_tries:
            show_error_dialog(_("Maximum number of tries reached, aborting."))
            return None

        # References to password entries
        pe1 = self.__builder.get_object("password_entry_1")
        pe2 = self.__builder.get_object("password_entry_2")

        if self.__dialog.run() == 1:
            pw1 = pe1.get_text()
            pw2 = pe2.get_text()
            if (pw1 != pw2):
                show_error_dialog(_("Passwords do not match"))
                self.__dialog.destroy()
                return None
            else:
                self.__dialog.destroy()
                return pw1
        else:
            self.__dialog.destroy()
            return None
                

