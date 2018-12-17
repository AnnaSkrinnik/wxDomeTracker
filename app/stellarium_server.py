#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

# setallarium_server module is a server with "black-box" functionality. Server
# threading and connection handling is handled automatically.

# This file was written in Janurary 2011

import socket
import threading
import Queue
import struct
import time

import wx
from wx.lib.pubsub import Publisher # inter-thread communications

HOST = 'localhost'
PORT = 10001

PACKET_FORMAT = "3iIii"
PACKET_SIZE = 24 
TYPE = 0 # unused
TIME = 0 # unused
RA = 0x100000000 / 24 
DEC = 0x40000000 / 90 
STATUS = 0 # unused

SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 10001
SOCKET_QUEUE_SIZE = 2
SOCKET_TIMEOUT = 10

class StellariumInterface:
    def __init__(self, host, port):
        self.inputQueue = Queue.Queue(PACKET_SIZE)
        self.server = StellariumDisplayServer(host, port, self.inputQueue)
        self.server.setDaemon(True)
        self.server.start()

    def compileBinaryPacket(self, time=TIME, ra=RA, dec=DEC):
        packet = struct.pack("3iIii", 24, 0, TIME, ra, dec, STATUS)
        
        return packet
        
    def setData(self, time, ra, dec):
        packet = self.compileBinaryPacket(time, ra, dec)
        if self.inputQueue.qsize() < 1: # bad but works
            self.inputQueue.put(packet)
        else:
            pass

class StellariumDisplayServer(threading.Thread):
    def __init__(self, host, port, inputQueue):
        threading.Thread.__init__(self)
        self.inputQueue = inputQueue
        self.host = host
        self.port = port
        
    def run(self):
        running = True
        while running:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            #s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 0)
            s.bind((self.host, self.port))
            s.listen(SOCKET_QUEUE_SIZE)
            client, addr = s.accept() # wait for connections
            #client.settimeout(-1)
            wx.CallAfter(Publisher().sendMessage, "display_server", 1)
            
            if not self.handleRequest(client, addr, self.inputQueue):
                continue
            
            client.close()
            
    def handleRequest(self, client, addr, inputQueue):
        running = True

        while running:
            client.setblocking(1)
            #data = client.recv(1024)
            #if data == "":
            #    client.close()
            #    break
            #else:
            packet = inputQueue.get()
            if packet:
                try:
                    client.send(packet)
                except:
                    running = False
            else:
                # clean-up code here
                running = False
                
        return 1

def old_server(): 
    fmt = 'hhqIii' 
    netPacket = struct.pack(fmt, PACKET_SIZE, TYPE, TIME, RA, DEC, STATUS) 
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.bind((HOST, PORT)) 
    s.listen(1) 
    conn, addr = s.accept() 
    
    print 'Connected by', addr 
    
    running = 1 
    while running:
        print "sending data"
        time.sleep(0.25)
        conn.send(netPacket) 
    
    conn.close()

def main():
    svr = StellariumInterface('localhost', 10001)

    while 1:
        time.sleep(1)
        svr.setData(TIME, RA, DEC)
        
        continue
        
    return 0
    
if __name__ == "__main__":
    main()
