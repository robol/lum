#
# -*- coding: utf-8 -*-

import ldap, ldap.modlist, re, ldif, sys
from exceptions import LumError
from configuration import Configuration

# This is just for debug
ldifwriter = ldif.LDIFWriter(sys.stdout)

class UserModel():

    def __init__(self, ldap_output = None):

        # Create an internatl dictionary that represent
        # ldap data
        self.__ldif = dict ()
        self.__dn = None
    
        # If ldap_output is passed to UserModel we can assume
        # to build an object representing a real LdapObject
        if ldap_output is not None:
            self.__dn = ldap_output[0]
            self.__ldif = dict(ldap_output[1])
            if not ldap_output[1].has_key("givenName"):
                self.set_given_name("")
            
        # If that is not the case we shall give the object
        # a Class that usually represent users in Ldap databases
        else:
            self.__ldif['objectClass'] = ["inetOrgPerson",
                                          "posixAccount",
                                          "person",
                                          "shadowAccount",
                                          "organizationalPerson",
                                          "top"]
                                                  
    def __getitem__(self, item):
        """Deprecated method to get item from the
        internal dictionary"""
        return self.__ldif[item]
        
    def __setitem__(self, item, value):
        """Deprecated method to set item in the
        internal dictionary"""
        self.__ldif[item] = value
    
    def get_dn(self):
        """Return the distinguished name of the object.
        Need some work to do the right thing."""
        return self.__dn
        
    def set_dn(self, dn):
        """Set Distinguished name of the Ldap object"""
        self.__dn = dn
    
    def get_uid(self):
        """Return the uid number of the user, or 0
        if it is not set"""
        if self.__ldif.has_key("uidNumber"):
            return self.__ldif['uidNumber'][0]
        else:
            return str(0)
        
    def set_uid(self, uid):
        """Set uid of the user. Setting it to zero
        means to autodetermine the first free uid when
        necessary"""
        self.__ldif['uidNumber'] = [str(uid)]
        
    def get_username(self):
        """Return username of the user"""
        return self.__ldif['uid'][0]
    
    def set_username(self, username):
        """Set username of the user"""
        self.__ldif['uid'] = [str(username)]
        
    def get_gid(self):
        """Return gid number. You shall use the
        method ldap_protocol.group_from_gid to
        get the group_name"""
        return self.__ldif['gidNumber'][0]
        
    def set_gid(self, gid):
        """Set the gid of the user"""
        self.__ldif['gidNumber'] = [str(gid)]
    
    def get_given_name(self):
        """Get the given name (i.e. the name)
        of the user"""
        return self.__ldif['givenName'][0]
        
    def get_gecos(self):
        """Return a complete name of the user, such
        as Tim Smith"""
        return self.__ldif['gecos'][0]
        
    def set_given_name(self, given_name):
        """Set the given name (i.e. the name) of the
        user"""
        self.__ldif['givenName'] = [str(given_name)]
        self.__ldif['cn'] = [str(given_name)]

        # Gecos shall be in the form name + " " + surname, but
        # if surname is not set, set only the name
        if self.__ldif.has_key("sn"):
            self.__ldif['gecos'] = [str(self.__ldif['givenName'][0] + " " + 
                                    self.__ldif['sn'][0]).strip()]
        else:
            self.__ldif['gecos'] = [str(given_name)]
    
    def get_surname(self):
        """Return surname of the user"""
        return self.__ldif['sn'][0]
        
    def set_surname(self, sn):
        """Set surname of the user"""
        self.__ldif['sn'] = [str(sn)]

        # Set gecos, including name if it is available
        if self.__ldif.has_key("givenName"):
            self.__ldif['gecos'] = [str(self.__ldif['givenName'][0] + " " + 
                                    self.__ldif['sn'][0]).strip()]
        else:
            self.__ldif['gecos'] = [str(sn)]
        
    def get_home(self):
        """Returns home directory of the user"""
        return self.__ldif['homeDirectory'][0]
        
    def set_home(self, home):
        """Set home directory of the user"""
        self.__ldif['homeDirectory'] = [str(home)]
        
    def get_shell(self):
        """Return the shell of the user"""
        return self.__ldif['loginShell'][0]
    
    def set_shell(self, shell):
        """Set the shell of the user"""
        self.__ldif['loginShell'] = [str(shell)]
        
    def __str__(self):
        return "%s a.k.a %s %s" % (self.get_uid(), 
                                    self.get_given_name(), 
                                    self.get_surname())
    def to_ldif(self):
        """Return a dictionary to be passed to ldap
        methods"""
        return dict(self.__ldif)


class Connection():

    def __init__(self, uri, bind_dn, password, base_dn, users_ou, groups_ou):
        """
        Create a connection to the specified uri
        """
        
        # Save data
        self.__uri = uri
        self.__bind_dn = bind_dn
        self.__base_dn = base_dn
        self.__password = password
        self.__users_ou = users_ou
        self.__groups_ou = groups_ou
        
        self.__ldap = ldap.initialize(uri)

        # Bind to the database with the provided credentials
        try:
            self.__ldap.simple_bind_s(bind_dn, password)
        except Exception, e:
            raise LumError('Error connecting to the server, check your credentials')
        
        # Check if there are missing ou and add them
        if not self.is_present(self.__users_ou):
            print "Adding missing OrganizationalUnit: %s" % self.__users_ou
            self.add_ou(self.__users_ou)
        
        if not self.is_present(self.__groups_ou):
            print "Adding missing OrganizationalUnit: %s" % self.__groups_ou
            self.add_ou(self.__groups_ou)

    def add_user(self, user, modify = False):
        """
        if result_type == ldap.RES_SEARCH_RESULT:
            raise StopIteration
        Add a user to the LDAP database
        """
        users_ou = self.__users_ou
        if not self.is_present(users_ou):
            raise LumError("users organizational unit not present!")
            
        # This means that we have to autodetermine the first free uid
        if (int(user.get_uid()) == 0):
            user.set_uid(self.next_free_uid())
        
        # Distinguished name
        dn = "uid=%s,%s" % (user['uid'][0], users_ou)

        self.__ldap.add_s(dn, ldap.modlist.addModlist(user.to_ldif()))
            
    def modify_user(self, old_user, new_user):
        """Modify existing user (i.e. replace it)"""
        users_ou = self.__users_ou
        if not self.is_present(users_ou):
            raise LumError("users organizational unit not present!")
        
        # Distinguished name
        new_dn = "uid=%s,%s" % (new_user.get_username(), users_ou)
        old_dn = "uid=%s,%s" % (old_user.get_username(), users_ou)
        
        self.__ldap.modify_s(old_dn, ldap.modlist.modifyModlist(old_user.to_ldif(), new_user.to_ldif()))
    
    def add_group(self, group_name):
        """Add a new group, autodetermining gid."""
        groups_ou = self.__groups_ou
        
        dn = "cn=%s,%s" % (group_name, groups_ou)
        
        group_ldif = {
            'cn': [str(group_name)],
            'gidNumber': [str(self.next_free_gid())],
            'objectClass': ['posixGroup', 'top'],
        }
        
        self.__ldap.add_s(dn, ldap.modlist.addModlist(group_ldif))
        
    def next_free_uid(self):
        """Determine next free uid"""
        users = self.get_users()
        uids = map(lambda x : int(x['uidNumber'][0]), users)
        if len(uids) == 0:
            return 1100
        return (max(uids) + 1)
        
    def next_free_gid(self):
        """Determine next free gid"""
        groups_ou = self.__groups_ou
        groups = self.__ldap.search_s(groups_ou, ldap.SCOPE_ONELEVEL, "cn=*")
        
        if len(groups) == 0: 
            return 1100
        
        gids = map(lambda x : int(x[1]['gidNumber'][0]), groups)
        
        
        return (max(gids) + 1)
    
    def delete_user(self, user):
        """
        Delete an user given the uid or the UserModel
        """
        self.__ldap.delete_s(user)

    def is_user_present(self, username):
        """
        Test if user is present
        """
        return self.is_present ("uid=%s" % username)
    
    def gid_from_group(self, group_name):
        """Return gid of the given group"""
        if self.__ldap is not None:
            groups = self.__ldap.search_s(self.__base_dn,
                                          ldap.SCOPE_SUBTREE, "cn=%s" % group_name)
            if len(groups) == 0:
                return None
            else:
                return groups[0][1]['gidNumber'][0]
        else:
            return None
    
    def group_from_gid(self, gid):
        """Return group name"""
        if self.__ldap is not None:
            group = self.__ldap.search_s(self.__groups_ou,
                                         ldap.SCOPE_ONELEVEL, "gidNumber=%d" % int(gid))
            if len(group) == 0:
                return "unknown"
            return group[0][1]['cn'][0]

    def is_present(self, ob):
        """
        Test if object is present in database
        """
        # Strip base_dn
        ob = ob.split(",")[0]
        res = self.__ldap.search_s(self.__base_dn, ldap.SCOPE_SUBTREE, ob)
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
        print ou
        ldif['ou'] = [re.findall(r"ou=(\w+),", ou)[0]]
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
        msgid = self.__ldap.search(self.__base_dn, ldap.SCOPE_SUBTREE, "uid=%s" % key)
        return UserIterator(self.__ldap, msgid)
        
    def get_groups(self, key = None):
        if key is None:
            key = "*"
        groups = map(lambda x : x[1], self.__ldap.search_s(self.__groups_ou, ldap.SCOPE_ONELEVEL, "cn=%s" % key))
        ret = dict()
        for group in groups:
            ret[group['gidNumber'][0]] = group['cn'][0]
        return ret
        
class UserIterator():
    """UserIterator permits to extract ldap query
    result while the ldap_module is still searching, 
    reducing search time"""

    def __init__(self, ldap_connection, msgid):
        self.__ldap = ldap_connection
        self.__msgid = msgid
        
    def __iter__(self):
        return self
        
    def next(self):
        result_type, data = self.__ldap.result(msgid = self.__msgid, all = 0)
        for user in data:
            return UserModel(user)
        if result_type == ldap.RES_SEARCH_RESULT:
            raise StopIteration
        

