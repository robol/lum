#
# -*- coding: utf-8 -*-
#
# Implementation of treeviews to manage
# users and groups

import gtk
from utilities import _, package_dir
from menu_item import lumUserTreeViewMenu, lumGroupTreeViewMenu
import os

class UserTreeView(gtk.TreeView):

    def __init__(self, model, parent):
        """
        Create the new UserTreeView starting from
        a UserStore
        """

        gtk.TreeView.__init__(self)
        self.set_model(model)
        self.__model = model
        self.__parent = parent

        # Create popup menu
        self.__popup_menu = lumUserTreeViewMenu(self.__parent)
        self.connect("button-press-event", self.on_button_press_event)

        # Load pixbuf
        pixbuf_path = os.path.join(package_dir, "ui", "user.png")
        pixbuf_image = gtk.Image()
        pixbuf_image.set_from_file(pixbuf_path)
        pixbuf = pixbuf_image.get_pixbuf()

        # User image column
        renderer = gtk.CellRendererPixbuf()
        renderer.set_property("pixbuf", pixbuf)
        column = gtk.TreeViewColumn()
        column.pack_start(renderer, True)
        column.set_expand(False)
        self.append_column(column)
        

        # username column
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn()
        column.pack_start(renderer)
        column.set_title(_("User"))
        column.add_attribute(renderer, "text", 0)
        column.set_expand(True)
        self.append_column(column)

        # Name column
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn()
        column.set_title(_("Name"))
        column.pack_start(renderer)
        column.add_attribute(renderer, "text", 1)
        column.set_expand(True)
        self.append_column(column)

        # group column
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn()
        column.pack_start(renderer)
        column.set_title(_("Group"))
        column.add_attribute(renderer, "text", 2)
        column.set_expand(True)
        self.append_column(column)

    def apply_filter(self, entry):
        """User GtkEntry as filter"""
        self.__filter_entry = entry
        self.__filtered_model = self.__model.filter_new()
        self.__filtered_model.set_visible_func(self.visible_func)

        entry.connect("changed", lambda x : self.__filtered_model.refilter())
        self.set_model(self.__filtered_model)

    def visible_func(self, model, treeiter, user_data = None):
        key = self.__filter_entry.get_text().lower()
        username = model.get_username(treeiter)
        name = model.get_given_name(treeiter)
        
        if username is not None and key in username.lower():
            return True
        if name is not None and key in name.lower():
            return True
        return False

    def get_selected_user(self):
        t_model, t_iter = self.get_selection().get_selected()
        if t_iter is None:
            return (None, None)
        t_iter = self.__filtered_model.convert_iter_to_child_iter(t_iter)
        return self.__model.get_usermodel(t_iter), t_iter

    def on_button_press_event(self, user_treeview, event):
        """Catch press button event on treeview and, if the user right
        clicked on it, open the popup menu"""
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            pathinfo = user_treeview.get_path_at_pos(x,y)
            if pathinfo is None:
                return
            path, col, cellx, celly = pathinfo
            user_treeview.grab_focus()
            user_treeview.set_cursor(path, col, 0)
            usermodel, t_iter = self.get_selected_user()
            self.__popup_menu.username = usermodel.get_username()
            self.__popup_menu.popup(None, None, None, event.button, event.time)

        

class GroupTreeView(gtk.TreeView):

    def __init__(self, model, parent):

        gtk.TreeView.__init__(self)
        self.set_model(model)
        self.__model = model
        self.__parent = parent

        # Create popup menu
        self.__popup_menu = lumGroupTreeViewMenu(self.__parent)
        self.connect("button-press-event", self.on_button_press_event)

        # Load image
        pixbuf_path = os.path.join(package_dir, "ui", "group.png")
        pixbuf_image = gtk.Image()
        pixbuf_image.set_from_file(pixbuf_path)
        pixbuf = pixbuf_image.get_pixbuf()

        # Group image
        renderer = gtk.CellRendererPixbuf()
        renderer.set_property("pixbuf", pixbuf)
        column = gtk.TreeViewColumn()
        column.pack_start(renderer)
        column.set_expand(False)
        self.append_column(column)

        # Group name
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn()
        column.pack_start(renderer)
        column.set_title(_("Group"))
        column.add_attribute(renderer, "text", 0)
        column.set_expand(True)
        self.append_column(column)
        
        # Group ID
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn()
        column.pack_start(renderer)
        column.set_title("GID")
        column.set_expand(True)
        column.add_attribute(renderer, "text", 1)
        self.append_column(column)


    def apply_filter(self, entry):
        """Apply filter based on a GtkEntry"""
        
        self.__filter_entry = entry
        self.__filtered_model = self.__model.filter_new()
        self.__filtered_model.set_visible_func(self.visible_func)

        self.__filter_entry.connect("changed", lambda x : self.__filtered_model.refilter())
        self.set_model(self.__filtered_model)

    def visible_func(self, model, treeiter, user_data = None):
        key = self.__filter_entry.get_text()
        group_name = model.get_group_name(treeiter)
        if group_name is not None and key in group_name.lower():
            return True
        else:
            return False

    def get_selected_group(self):
        t_model, t_iter = self.get_selection().get_selected()
        if t_iter is None:
            return (None, None)
        t_iter = self.__filtered_model.convert_iter_to_child_iter(t_iter)
        return self.__model.get_group_name(t_iter), t_iter

    
    def on_button_press_event(self, group_treeview, event):
        """Catch button press on group treeview and show popup
        menu if the user right-clicked."""
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            pathinfo = group_treeview.get_path_at_pos(x,y)
            if pathinfo is None:
                return

            path, col, cellx, celly = pathinfo
            group_treeview.grab_focus()
            group_treeview.set_cursor(path, col, 0)
            group, t_iter = self.get_selected_group()
            self.__popup_menu.group = group
            self.__popup_menu.popup(None, None, None, event.button, event.time)

