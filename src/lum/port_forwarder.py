#
# -*- coding: utf-8 -*-
#
# Author: Leonardo Robol <leo@robol.it>
#


# Port to use for the tunnelled connections
forward_port = 62342


import paramiko, threading, SocketServer, gobject, select, sys

class PortForwarder(threading.Thread, gobject.GObject):

    __gsignals__ = {
        'tunnel-opened': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                          ())
        }

    def __init__(self, remote_host, remote_port, username, password):
        """Create a new forwarder server with the given
        transport"""
        self.remote_host = remote_host
        self.remote_port = remote_port

        self.is_active = False

        self.__client = paramiko.SSHClient()
        self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__client.connect(remote_host, username = username, password = password)
        self.transport = self.__client.get_transport()

        # Constructors
        threading.Thread.__init__(self)
        gobject.GObject.__init__(self)

        self.server = ForwardServer(self.remote_host,
                                    self.remote_port,
                                    self.transport)


    def stop_serving(self):
        self.server.shutdown()

    def run(self):
        """Actually serve the request to the forwarder port"""        
        gobject.idle_add(lambda x : self.emit("tunnel-opened"), False)
        self.server.serve_forever()

class ForwardServer (SocketServer.ThreadingTCPServer):

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, remote_host, remote_port, transport):
        self.remote_host = remote_host
        self.remote_port = int(remote_port)
        self.transport = transport
        SocketServer.ThreadingTCPServer.__init__(self, ('127.0.0.1', forward_port), Handler)
     
class Handler (SocketServer.BaseRequestHandler): 
    def handle(self):
        print "Hello"
        sys.stdout.flush()
        print "Calling self.server.transport.open_channel('direct-tcpip', (%s, %d), (%s, %d))" % (self.server.remote_host,
                                                                                                  self.server.remote_port,
                                                                                                  '127.0.0.1', forward_port)
        chan = self.server.transport.open_channel('direct-tcpip',
                                                  (self.server.remote_host, self.server.remote_port),
                                                  ('127.0.0.1',forward_port))
        while True:
            r, w, x = select.select([self.request, chan], [], [])
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
        chan.close()
        self.request.close()
