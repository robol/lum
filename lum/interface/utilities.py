#
# -*- coding: utf-8 -*-
#

import gtk, gettext, locale, os


# Internationalization support
gettext.bindtextdomain("lum", "locale")
gettext.textdomain("lum")
locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())
_ = gettext.gettext

package_dir = os.path.realpath(os.path.join(__file__,
                                           os.path.pardir))

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

def create_builder(interface_file):
    """Create a gtk.Builder loading the
    right interface file"""
    
    builder = gtk.Builder()
    builder.set_translation_domain("lum")

    builder.add_from_file(os.path.join(package_dir,
                                       os.path.join("ui", interface_file)))

    return builder
    
