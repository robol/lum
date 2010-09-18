#
# -*- coding: utf-8 -*-
#

import gtk

def show_error_dialog(message):
    """Show an error dialog with message"""

    dialog = gtk.MessageDialog(type = gtk.MESSAGE_ERROR,
                               buttons = gtk.BUTTONS_OK)
    dialog.set_title ("Ldap User Manager")
    dialog.set_markup(message)

    dialog.run()
    dialog.destroy()


def ask_question(message):
    """Ask a question to the user"""
    dialog = gtk.MessageDialog(type = gtk.MESSAGE_QUESTION,
                               buttons = gtk.BUTTONS_YES_NO)
    dialog.set_title("Ldap User Manager")
    dialog.set_markup(message)
    
    if dialog.run() == gtk.RESPONSE_YES:
        dialog.destroy()
        return True
    else:
        dialog.destroy()
        return False
