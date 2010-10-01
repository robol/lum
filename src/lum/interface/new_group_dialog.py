#
# -*- coding: utf-8 -*-
#
# 

from utilities import create_builder, show_error_dialog, _

class lumNewGroupDialog():

    def __init__(self, datapath, connection):

        self.__builder = create_builder("LumNewGroupDialog.ui")
        
        self.__dialog = self.__builder.get_object("new_group_dialog")

        gid = connection.next_free_gid()
        self.__builder.get_object("gid_entry").set_text(str(gid))

    def run(self):

        if self.__dialog.run() == 1:
            group_name = self.__builder.get_object("group_name_entry").get_text()

            try:
                gid = int(self.__builder.get_object("gid_entry").get_text())
            except ValueError:
                show_error_dialog(_("Insert a valid gid"))
                self.__dialog.destroy()
                return (None, None)

            self.__dialog.destroy()
            return (group_name, gid)

        else:
            self.__dialog.destroy()
            return (None, None)
