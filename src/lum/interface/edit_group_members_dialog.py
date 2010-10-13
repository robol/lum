#
# -*- coding: utf-8 -*-
#

import gtk
from utilities import create_builder, _

class lumEditGroupMembersDialog():

    def __init__(self, connection, group_name):
        
        self.__builder = create_builder("LumEditGroupMembers.ui")        
        self.__dialog = self.__builder.get_object("edit_group_members_dialog")
        self.__connection = connection

        self.__builder.get_object("new_button").connect("clicked",
                                                        self.new_user)
        self.__builder.get_object("remove_button").connect("clicked",
                                                           self.delete_user)

        # Get only non structural members
        self.__original_members = filter(lambda x : not x[1], 
                                         self.__connection.get_members(group_name, True))
        self.__original_members = map(lambda x : x[0],
                                      self.__original_members)

        store = self.__builder.get_object("members_store")
        for uid in self.__original_members:
            store.append((uid,))

        renderer = self.__builder.get_object("member_cellrenderer")
        renderer.set_property("editable", True)
        renderer.connect("edited", self.on_renderer_edited)

    def on_renderer_edited(self, renderer, path, new_text):
        treeview = self.__builder.get_object("members_treeview")
        t_model, t_iter = treeview.get_selection().get_selected()
        if t_iter is None:
            return

        t_model.set_value(t_iter, 0, new_text)
        

    def run(self):
        
        if self.__dialog.run() == 1:
            
            store = self.__builder.get_object("members_store")
            it = store.get_iter_first()

            users_to_add = []
            users_to_remove = []

            users_in_store = []

            while(it is not None):
                uid = store.get_value(it, 0)
                users_in_store.append(uid)
                if uid not in self.__original_members:
                    users_to_add.append(uid)
                it = store.iter_next(it)

            for uid in self.__original_members:
                if uid not in users_in_store:
                    users_to_remove.append(uid)

            self.__dialog.destroy()
            return users_to_add, users_to_remove

        else:
            self.__dialog.destroy()
            return (None, None)
    
    def new_user(self, button):
        """Create a new empty row"""
        store = self.__builder.get_object("members_store")
        it = store.append((_("Insert uid here"),))

        # Get path
        path = store.get_path(it)
        
        # Start editing the new entry
        treeview = self.__builder.get_object("members_treeview")
        column = self.__builder.get_object("members_column")
        treeview.set_cursor(path, column, True)
        

    def delete_user(self, button):
        """Delete selected user"""
        treeview = self.__builder.get_object("members_treeview")
        t_model, t_iter = treeview.get_selection().get_selected()

        if t_iter is None:
            return

        store = self.__builder.get_object("members_store")
        store.remove(t_iter)
