# -*- coding: utf-8 -*-
#
#

import ldap, ldap.modlist, re, ldif, sys
from exceptions import LumError

ldifwriter = ldif.LDIFWriter(sys.stdout)

class UserModel():

    def __init__(self, username, given_name, sn, uid, gid,
                 login_shell = "/bin/sh", additional_data = None):

        self.__ldif = dict ()
        
        if username is not None:
		    self.__ldif['objectClass'] = ["inetOrgPerson",
		                                  "posixAccount",
		                                  "person",
		                                  "shadowAccount",
		                                  "organizationalPerson",
		                                  "top"]
		    
		    self.__ldif['uid'] = [str(username)]
		    self.__ldif['cn'] = [str(username)]
		    self.__ldif['sn'] = [str(sn)]
		    self.__ldif['gecos'] = [" ".join([given_name, sn])]
		    self.__ldif['givenName'] = [str(given_name)]
		    self.__ldif['uidNumber'] = [str(uid)]
		    self.__ldif['gidNumber'] = [str(gid)]
		    self.__ldif['loginShell'] = [str(login_shell)]
		    self.__ldif['homeDirectory'] = ["/home/%s" % username]
        
        self.dn = None

        if additional_data is None:
            return
        for key in additional_data:
            self.__ldif[key] = list(str(additional_data[key]))

    def __getitem__(self, item):
        return self.__ldif[item]

    def to_ldif(self):
        return dict(self.__ldif)
        
    def fill_from_dict(self, dic):
    	self.__ldif = dict(dic)
    	
    def get_uid(self):
    	return self.__ldif['uid'][0]
    
    def get_given_name(self):
    	return self.__ldif['givenName'][0]
    
    def get_surname(self):
    	return self.__ldif['sn'][0]
    	
    def __repr__(self):
    	return "<lum.LdapProtocol.UserModel \"%s a.k.a %s %s\">" % (self.get_uid(), self.get_given_name(), self.get_surname())
        
def ldap_to_user_model(ldap_result):
	"""
	Convert an ldap returned value to a UserModel object
	"""
	user = UserModel (None, None, None, None, None)
	user.fill_from_dict (ldap_result[1])
	user.dn = ldap_result[0]
	return user

class Connection():

    def __init__(self, config, password = None):
        """
        Create a connection to the specified uri
        """

        # Piccola funzioncina comoda per ottenere dati
        # dalla configurazione
        get = lambda x : config.get("LDAP", x)
        self.__get = get

        self.__config = config
        self.__ldap = ldap.initialize(get("uri"))

        bind_dn = get("bind_dn")
        self.__base_dn = get("base_dn")

	self.__users_ou = get("users_ou")

        # Retrieve password from the file specified in
        # the configuration file
        try:
            if password is None:
                with open(get("secret_file"), 'r') as f:
                    password = f.read().strip("\n")
        except IOError, e:
            raise LumError('Error opening password file %s' % get("secret_file"))

        # Bind to the database with the provided credentials
        try:
            self.__ldap.simple_bind_s(bind_dn, password)
        except Exception, e:
            raise LumError('Error connecting to the server, check your credentials')

	if not self.is_present(get("users_ou")):
	    self.add_ou(get("users_ou"))

    def add_user(self, user):
        """
        Add a user to the LDAP database
        """
        users_ou = self.__get("users_ou")
        if not self.is_present(users_ou):
            raise LumError("users organizationalUnit not present, maybe you need to create it?")
        dn = "uid=%s,%s" % (user['uid'][0], users_ou)
        self.__ldap.add_s(dn, ldap.modlist.addModlist(user.to_ldif()))

    def delete_user(self, user):
		"""
		Delete an user given the uid or the UserModel
		"""
		if isinstance(user, UserModel):
			user = user['uid'][0]
		self.__ldap.delete_s("uid=%s,%s" % (user, self.__users_ou))

    def is_user_present(self, username):
	"""
	Test if user is present
	"""
	return self.is_present ("uid=%s" % username)

    def is_present(self, object):
        """
        Test if object is present in database
        """
	# Strip base_dn
	object = object.split(",")[0]
        res = self.__ldap.search_s(self.__base_dn, ldap.SCOPE_SUBTREE, object)
        if len(res) == 0:
            return False
	return True
        
    def add_ou(self, ou):
        """
        Add an organizationalUnit to the database.
        Usage example: add_ou("People")
        """
        ldif = dict()
        ldif['objectClass'] = ['organizationalUnit',
                               'top']
        ldif['ou'] = [re.findall(r"ou=(\w+),", ou)[0]]

        ldifwriter.unparse(ou, ldif)
        self.__ldap.add_s(ou, ldap.modlist.addModlist(ldif))
        
    def get_user(self, uid):
    	return self.get_users(uid)[0]

    def get_users(self, key = None):
	"""
	Get user that match the given key or all users if
	key is not given.
	"""
	if key is None:
		key = "*"
	users = self.__ldap.search_s(self.__base_dn, ldap.SCOPE_SUBTREE, "uid=%s" % key)
	return map(ldap_to_user_model, users)

