#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of lum, the LDAP User Manager
# 
# Author: Leonardo Robol <robol@poisson.phc.unipi.it>
# Date: 5 Sep 2010
#

from lum.interface.app import lumApp
import sys, os, gtk, signal

if __name__ == "__main__":

    # Create main application
    app = lumApp()
    
    # and start it
    app.start ()

    # Connect signals
    signal.signal(signal.SIGINT,  lambda x,y : gtk.main_quit())
    signal.signal(signal.SIGTERM, lambda x,y : gtk.main_quit())
    
    # Start the gtk main loop
    gtk.main()
    
    
