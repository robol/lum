#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of lum, the LDAP User Manager
# 
# Author: Leonardo Robol <robol@poisson.phc.unipi.it>
# Date: 5 Sep 2010
#

from lum.interface.app import lumApp
import sys, os, gtk

if __name__ == "__main__":
    
    # Determine if we are running a local version of the script
    # or if we are installed system-wide
    datapath = os.path.dirname(sys.argv[0])
    if os.path.exists(os.path.join(datapath, "ui/LumApp.ui")):
        pass
    elif os.path.exists("/usr/share/lum/ui/lumApp.ui"):
        datapath = "/usr/share/lum/"
    else:
        sys.stderr.write ("Interface files not found, aborting\n")
        sys.exit(1)
    
    app = lumApp(datapath)
    
    app.start ()
    
    # Start the gtk main loop
    gtk.main()
    
    
