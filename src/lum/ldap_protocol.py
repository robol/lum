#
# -*- coding: utf-8 -*-

import ldap, ldap.modlist, re, ldif, sys, random
from crypt import crypt
from exceptions import *
from configuration import Configuration
import gobject

# This is just for debug
ldifwriter = ldif.LDIFWriter(sys.stdout)

# Default objectClasses
default_objectClasses = [ "top",
                          "person",
                          "organizationalPerson",
                          "posixAccount",
                          "shadowAccount",
                          "inetOrgPerson" ]

# Utility functions
def random_string():
    """Generate a random string to be used as salt
    for crypt()"""
    length = 9
    r = ""
    possible_letters = [ ".", "/" ]
    ff = [ "a", "b", "c", "d", "e", "f", "g", "h", "i", 
           "j", "k", "h", "l", "m", "n", "o", "p", "q", 
           "r", "s", "t", "u", "v", "w", "x", "y", "z" ]
    possible_letters.extend(ff)
    possible_letters.extend(map(lambda x : x.capitalize(), ff))
    for letter in range(0,length):
        r += random.choice(possible_letters)
    return r

    

class UserModel(gobject.GObject):

    def __init__(self, ldap_output = None):

        gobject.GObject.__init__(self)

        # Create an internatl dictionary that represent
        # ldap data
        self.__ldif = dict ()
        self.__dn = None

        # Some fields to keep track of user name and
        # surname over the schema
        self.__name = ""
        self.__sn = ""
        self.__email = ""


        # If ldap_output is a UserModel object use __init__()
        # as a copy constructor
        if isinstance(ldap_output, UserModel):
            dn = ldap_output.get_dn()
            dictionary = ldap_output.to_ldif()

            # Copy internal objects
            self.__ldif = dict(dictionary)
            self.__dn = str(dn)

            # Give reference to originating object away
            ldap_output = None
    
        # If ldap_output is passed to UserModel and is not
        # a UserModel istance we can assume
        # to build an object representing a real LdapObject
        if ldap_output is not None:
            self.__dn = ldap_output[0]
            self.__ldif = dict(ldap_output[1])

            if self.__ldif.has_key("givenName"):
                self.__name = self.__ldif['givenName'][0]
            if self.__ldif.has_key("sn"):
                self.__sn = self.__ldif['sn'][0]

            
        # If that is not the case we shall give the object
        # a Class that usually represent users in Ldap databases
        else:
            self.__ldif['objectClass'] = default_objectClasses
                                                  
    def __getitem__(self, item):
        """Deprecated method to get item from the
        internal dictionary"""
        return self.__ldif[item]
        
    def __setitem__(self, item, value):
        """Deprecated method to set item in the
        internal dictionary"""
        self.__ldif[item] = value
    
    def get_dn(self, users_ou = None):
        """Return the distinguished name of the object.
        Need some work to do the right thing."""
        if self.__dn is not None:
            return self.__dn
        else:
            if users_ou is None:
                raise LumError("No Users ou specified for get_dn() but no dn present in UserModel")
            else:
                return "uid=%s,%s" % (self.get_username(), 
                                      users_ou)
        
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
        try:
            return self.__ldif['uid'][0]
        except KeyError:
            return ""
    
    def set_username(self, username):
        """Set username of the user"""
        self.__ldif['uid'] = [str(username)]
        
    def get_gid(self):
        """Return gid number. You shall use the
        method ldap_protocol.group_from_gid to
        get the group_name"""
        try:
            return self.__ldif['gidNumber'][0]
        except KeyError:
            return ""
        
    def set_gid(self, gid):
        """Set the gid of the user"""
        self.__ldif['gidNumber'] = [str(gid)]
    
    def get_given_name(self):
        """Get the given name (i.e. the name)
        of the user"""
        try:
            return self.__ldif['givenName'][0]
        except KeyError:
            return ""
        
    def get_gecos(self):
        """Return a complete name of the user, such
        as Tim Smith"""
        try:
            return self.__ldif['gecos'][0]
        except KeyError:
            return " ".join(filter(lambda x : x != "", 
                                   [self.__name, self.__sn]))
                
        
    def set_given_name(self, given_name):
        """Set the given name (i.e. the name) of the
        user"""
        if "inetOrgPerson" in self.__ldif['objectClass']:
            self.__ldif['givenName'] = [str(given_name)]

        self.__name = given_name

        # Gecos shall be in the form name + " " + surname, but
        # if surname is not set, set only the name
        if self.__sn == "":
            self.__ldif['gecos'] = [" ".join([self.__name,
                                              self.__sn])]
        else:
            self.__ldif['gecos'] = [str(given_name)]

        self.__ldif['cn'] = self.__ldif['gecos']
    
    def get_surname(self):
        """Return surname of the user"""
        try:
            return self.__ldif['sn'][0]
        except KeyError:
            return self.__sn
        
    def set_surname(self, sn):
        """Set surname of the user"""

        if "inetOrgPerson" in self.__ldif['objectClass']:
            self.__ldif['sn'] = [str(sn)]

        # Set surname
        self.__sn = sn

        # Set gecos, including name if it is available
        if self.__name == "":
            self.__ldif['gecos'] = [str(sn)]
        else:
            self.__ldif['gecos'] = [" ".join([self.__name,
                                             self.__sn])]

        # And set similar fields
        self.__ldif['cn'] = self.__ldif['gecos']
        
    def get_home(self):
        """Returns home directory of the user"""
        try:
            return self.__ldif['homeDirectory'][0]
        except KeyError:
            return ""
        
    def set_home(self, home):
        """Set home directory of the user"""
        self.__ldif['homeDirectory'] = [str(home)]
        
    def get_shell(self):
        """Return the shell of the user"""
        try:
            return self.__ldif['loginShell'][0]
        except KeyError:
            return ""
    
    def set_shell(self, shell):
        """Set the shell of the user"""
        self.__ldif['loginShell'] = [str(shell)]

    def get_email(self):
        """Return user email"""
        try:
            return self.__ldif['mail'][0]
        except KeyError:
            return self.__email

    def set_email(self, email):
        if "inetOrgPerson" in self.__ldif['objectClass']:
            self.__ldif['mail'] = [str(email)]

        self.__email = email

    def set_password(self, password, crypt_strategy = "CRYPT"):
        """Set userPassword field of the user. Only CRYPT
        is supported at the moment being"""
        if (crypt_strategy == "CRYPT"):
            salt = "$1$%s$" % random_string()
            value = "{CRYPT}" + crypt(password, salt)
            self.__ldif['userPassword'] = [value]
        else:
            raise LumUnsupportedError('$s crypt strategy is not supported')
        
    def __str__(self):
        return "%s a.k.a %s %s" % (self.get_uid(), 
                                    self.get_given_name(), 
                                    self.get_surname())
    def to_ldif(self):
        """Return a dictionary to be passed to ldap
        methods"""
        return dict(self.__ldif)


class Connection(gobject.GObject):

    __gsignals__ = {
        # Emitted with the list of missing ou
        'missing-ou': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                       (gobject.TYPE_PYOBJECT,)),
        'connection-completed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                 ())
        }
    
    def __init__(self, uri, bind_dn, password, base_dn, users_ou, groups_ou):
        """
        Create a connection to the specified uri
        """

        gobject.GObject.__init__(self)
        
        # Save data
        self.__uri = uri
        self.__bind_dn = bind_dn
        self.__base_dn = base_dn
        self.__password = password
        self.__users_ou = users_ou
        self.__groups_ou = groups_ou
        
        self.__ldap = ldap.initialize(uri)

    def set_password(self, password):
        self.__password = password

    def start(self):

        # Bind to the database with the provided credentials
        try:
            self.__ldap.simple_bind_s(self.__bind_dn, self.__password)
        except Exception, e:
            raise LumError('Error connecting to the server, check your credentials')
        
        # Check if there are missing ou and add them
        missing_ou = []
        if not self.is_present(self.__users_ou):
            missing_ou.append(self.__users_ou)
        
        if not self.is_present(self.__groups_ou):
            missing_ou.append(self.__users_ou)

        if missing_ou != []:
            self.emit("missing-ou", missing_ou)
        else:
            self.emit("connection-completed")

    def add_user(self, user):
        """
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

        try:
            self.__ldap.add_s(dn, ldap.modlist.addModlist(user.to_ldif()))
        except ldap.ALREADY_EXISTS:
            raise LumAlreadyExistsError("User %s already exists" % dn)
        except ldap.INSUFFICIENT_ACCESS:
            raise LumInsufficientPermissionsError("Insufficient permission to create %s" % dn)
            
    def modify_user(self, old_user, new_user):
        """Modify existing user (i.e. replace it)"""
        users_ou = self.__users_ou
        if not self.is_present(users_ou):
            raise LumError("users organizational unit not present!")
        
        # Distinguished name
        new_dn = new_user.get_dn(self.__users_ou)
        old_dn = old_user.get_dn(self.__users_ou)

        modlist = ldap.modlist.modifyModlist(old_user.to_ldif(),
                                             new_user.to_ldif())

        try:
            self.__ldap.modify_s(old_dn, modlist)
        except ldap.INSUFFICIENT_ACCESS:
            raise LumInsufficientPermissionsError("Insufficient accesso to modify user")
    
    def add_group(self, group_name, gid = None):
        """Add a new group, autodetermining gid."""
        groups_ou = self.__groups_ou
        
        dn = "cn=%s,%s" % (group_name, groups_ou)

        if gid is None:
            gid = str(self.next_free_gid())
        else:
            gid = str(gid)
        
        group_ldif = {
            'cn': [str(group_name)],
            'gidNumber': [gid],
            'objectClass': ['posixGroup', 'top'],
        }
        
        try:
            self.__ldap.add_s(dn, ldap.modlist.addModlist(group_ldif))
        except ldap.ALREADY_EXISTS:
            raise LumAlreadyExistsError("Group %s already exists in the ldap tree" % group_name)
        except ldap.INSUFFICIENT_ACCESS:
            raise LumInsufficientPermissionsError("Insufficient permissions to create the group")
        
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
        Delete an user given the dn, the UserModel
        or even the uid
        """
        if isinstance(user, UserModel):
            user = "uid=%s,%s" % (user.get_username(), 
                                  self.__users_ou)
        elif not self.__users_ou in user:
            user = "uid=%s,%s" % (user,
                                  self.__users_ou)

        try:
            self.__ldap.delete_s(user)
        except ldap.INSUFFICIENT_ACCESS:
            raise LumInsufficientPermissionsError("Insufficient permissions to delete user")
        

    def delete_group(self, group_name):
        """
        Delete a group given the name. 
        """
        try:
            self.__ldap.delete_s("cn=%s,%s" % (group_name,
                                               self.__groups_ou))
        except ldap.INSUFFICIENT_ACCESS:
            raise LumInsufficientPermissionsError("Insufficient permissions to delete group")

    def get_members(self, group_name):
        """Obtain all the members of group_name"""
        
        # There are two types of group members in
        # an ldap tree:
        # 1) Users that have a group as primary group, so
        #    they have a gidNumber field referring to group
        #    ID.
        # 2) Users that are listed in the memberUid of the
        #    group.

        users = []

        group_dn, group_data = self.__ldap.search_s(self.__groups_ou,
                                                    ldap.SCOPE_ONELEVEL,
                                                    "cn=%s" % group_name)[0]

        
        # Get users in memberUid field of the group
        if group_data.has_key("memberUid"):
            for user in group_data['memberUid']:
                users.append(user)

        # Get group gid
        gid = group_data['gidNumber'][0]

        # and then find users that have gidNumber referring to
        # the group
        matching_users = self.__ldap.search_s(self.__users_ou,
                                              ldap.SCOPE_ONELEVEL,
                                              "gidNumber=%s" % gid)
        for dn, user in matching_users:
            users.append(user['uid'][0])

        return users

    def change_password(self, uid, password):
        """Change password of selected user. If called when
        user has no password it will set the passord, making
        login possible."""

        # Get the user from LDAP
        user = self.get_user(uid)

        # Create a copy of the old user and change
        # its password
        new_user = UserModel(user)
        new_user.set_password(password)

        # Apply
        self.modify_user(user, new_user)
        

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
        ldif['ou'] = [re.findall(r"ou=(\w+),", ou)[0]]
        self.__ldap.add_s(ou, ldap.modlist.addModlist(ldif))
        
    def get_user(self, uid):
        users = self.__ldap.search_s(self.__users_ou, ldap.SCOPE_ONELEVEL, "uid=%s" % uid)
        try:
            return UserModel(users[0])
        except IndexError:
            raise LumUserNotFoundError("User %s not found in LDAP" % uid)

    def get_users(self, key = None):
        """
        Get user that match the given key or all users if
        key is not given.
        """
        msgid = self.__ldap.search(self.__users_ou, ldap.SCOPE_ONELEVEL, "uid=*")
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
        

