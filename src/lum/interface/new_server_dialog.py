#
# -*- coding: utf-8
#
#

import gtk
from utilities import create_builder

class lumNewServerDialog():

    def __init__(self):
        
        # Get interface file
        self.__builder = create_builder("LumNewServerDialog.ui")

    def run(self):

        dialog = self.__builder.get_object("dialog")
        
        if dialog.run() == 1:
            uri = self.__builder.get_object("uri_entry").get_text()
            bind_dn = self.__builder.get_object("bind_dn_entry").get_text()
            base_dn = self.__builder.get_object("base_dn_entry").get_text()

            users_ou = self.__builder.get_object("users_ou_entry").get_text()
            groups_ou = self.__builder.get_object("groups_ou_entry").get_text()

            dialog.destroy()
            return (uri, bind_dn, base_dn, users_ou, groups_ou)

        else:
            dialog.destroy()
            return (None, None, None, None, None)
