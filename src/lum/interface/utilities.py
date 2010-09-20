#
# -*- coding: utf-8 -*-
#

import gtk, gettext, locale, os
    
_ = gettext.gettext
package_dir = os.path.realpath(os.path.join(__file__,
                                           os.path.pardir))

def gettext_init():
    # Load local translations
    if os.path.join("src", "lum", "interface") in package_dir:
        lum_base = os.path.realpath(os.path.join(package_dir,
                                                 os.path.pardir,
                                                 os.path.pardir,
                                                 os.path.pardir,
                                                 "locale"))
        gettext.bindtextdomain("lum", lum_base)
    else:
        gettext.bindtextdomain("lum")

    gettext.textdomain("lum")
    try:
        locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())
    except locale.Error:
        print "Unable to load localized strings"


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
    try:
        builder.set_translation_domain("lum")
    except locale.Error:
        print "Unable to load localized interface"

    builder.add_from_file(os.path.join(package_dir,
                                       os.path.join("ui", interface_file)))

    return builder
    
