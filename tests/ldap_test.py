#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, "/home/leonardo/src/lum")
import lum.ldapProtocol as ldap
import ConfigParser

c = ConfigParser.ConfigParser ()
c.add_section("LDAP")
c.read("lum.conf")

print "> Testing ldap connection...",
connection = ldap.Connection(c)
print "done"

if connection.is_user_present("test"):
	print "> Deleting test user...",
	connection.delete_user("test")
	print "done"

print "> Adding a test user...",
user = ldap.UserModel(username = "test", given_name = "Leonardo", sn="Robol",
                      uid = 1001, gid = 1001)
connection.add_user(user)
print "done"

print "> Getting user list...",
user_list = connection.get_users()
print "done."
print "Printing user list:"
for user in user_list:
	print "  " + str(user)

print "> Adding user test2...",
user = ldap.UserModel(username = "test2", given_name = "Pirlotti", sn="Robol", uid=1002, gid=1001)
connection.add_user(user)
print "done"

print "> Getting new user list...",
user_list = connection.get_users()
print "done."
print "Printing new user list:"
for user in user_list:
	print "  " + str(user)

print "> Removing user test2...",
connection.delete_user("test2")
print "done."
