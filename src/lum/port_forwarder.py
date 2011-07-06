#
# -*- coding: utf-8 -*-
#
# Author: Leonardo Robol <leo@robol.it>
#


# Port to use for the tunnelled connections
forward_port = 62342

import paramiko, threading, SocketServer, gobject, select
import sys, gettext, socket

_ = gettext.gettext

class PortForwarder(threading.Thread, gobject.GObject):

    daemon = True

    __gsignals__ = {
        'tunnel-opened': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                          ()),
        'error-occurred': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                           (gobject.TYPE_STRING,))
        }

    def __init__(self, remote_host, remote_port, username, password):
        """Create a new forwarder server with the given
        transport"""
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.username = username
        self.password = password

        # Constructors
        threading.Thread.__init__(self)
        gobject.GObject.__init__(self)
        self.server = None

    def stop_serving(self):
        if self.server is not None:
            self.server.stop_requested = True
            self.server.shutdown()
            self.server.socket.shutdown(socket.SHUT_RDWR)
            self.server.socket.close()
        if self.__client is not None:
            self.__client.close()
        print "Server shutdown"

    def run(self):
        """Actually serve the request to the forwarder port"""        
        print "Connecting via SSH...",
        try:
            self.__client = paramiko.SSHClient()
            self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.__client.connect(self.remote_host, 
                                  username = self.username, 
                                  password = self.password)
            self.transport = self.__client.get_transport()
        except Exception, e:
            self.emit("error-occurred", e)
            return
        else:
            print "done"

        print "Creating the server",
        self.server = ForwardServer(self.remote_host,
                                    self.remote_port,
                                    self.transport,
                                    self)
        print "done"

        print "Starting the server...",
        if not self.server.setup_successful:
            self.stop_serving()
            print "no, setup wasn't successful"
            del self.server
            self.emit("error-occurred", e)
            return

        gobject.timeout_add(500, lambda x : self.emit("tunnel-opened"), False)
        self.server.serve_forever()
        print "starting"



class ForwardServer (SocketServer.ThreadingTCPServer, gobject.GObject):

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, remote_host, remote_port, transport, forwarder):
        self.stop_requested = False
        self.forwarder = forwarder
        self.setup_successful = False
        self.remote_host = remote_host
        self.remote_port = int(remote_port)
        self.transport = transport
        gobject.GObject.__init__(self)
        try:
            SocketServer.ThreadingTCPServer.__init__(self, ('127.0.0.1', forward_port), Handler)
        except Exception, e:
            print e
            self.forwarder.emit("error-occurred", 
                                _("Error binding the server for the port forwarding. Maybe there is another instance of lum running?"))
        else:
            self.setup_successful = True
     
class Handler (SocketServer.BaseRequestHandler): 

    def handle(self):
        try:
            print "Request catched!"
            chan = self.server.transport.open_channel('direct-tcpip',
                                                      ('127.0.0.1', self.server.remote_port),
                                                      ('127.0.0.1',forward_port))
            while True:
                r, w, x = select.select([self.request, chan], [], [], 0.4)
                print "select() just returned"
                if self.server.stop_requested:
                    break

                if self.request in r:
                    data = self.request.recv(1024)
                    if len(data) == 0:
                        break
                    chan.send(data)
                if chan in r:
                    data = chan.recv(1024)
                    if len(data) == 0:
                        break
                    self.request.send(data)

            print "Closing up channel"
            chan.close()
            self.request.close()
        except Exception, e:
            print e
            self.server.forwarder.emit("error-occurred", e)
            return
