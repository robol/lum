# -*- coding: utf-8 -*-
#
#

import ldap
from exceptions import LumException

class UserModel():

    def __init__(self, username, given_name, uid, gid):
        self._username = username
        self.given_name = given_name
        self._uid = uid
        self._gid = gid

class Connection():

    def __init__(self, config):
        """
        Create a connection to the specified uri
        """

        self._config = config
        self._ldap = ldap.initialize(config.uri)

        bind_dn = config.bind_dn

        # Retrieve password from the file specified in
        # the configuration file
        try:
            with open(config.secret_file, 'r') as f:
                password = f.read ()
        except IOError, e:
            raise LumError('Error reading the password file, aborting connection')
        
        # Bind to the database with the provided credentials
        try:
            self._connection = self._ldap.simple_bind_s(bind_dn, password)
        except Exception, e:
            raise LumError('Error connecting to the server, check your credentials')

    def add_user(self, user):
        """
        Add a user to the LDAP database
        """
        users_ou = self._config.users_ou
        

    def get_user(self, key = None):
        """
        Get user that match the given key or all users if
        key is not given.
        """
        pass
