#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

# The Executive Functions Module is responsible for executing various scripted
# operations. Many of these functions are threaded as to not interfere with the
# main GUI thread. The status codes and interaction with these threads are 
# done using the Publisher() object. 

import sys
import os
import wx
import serial
from wx.lib.pubsub import Publisher # inter-thread communications
from obstools import obsmathlib
from obstools import argoterm
from obstools import obslib
import threading
import multiprocessing
import time

DEFAULT_REPEAT_INTERVAL = 100
DEFAULT_DOME_PULSE_READ_INTERVAL = 50
DEFAULT_HARDWARE_READOUT_INTERVAL = 150
DEFAULT_SLEEP_TIME = 5.0

MODULE_LONG_NAME = "Executive Functions"
MODULE_VERSION = "0.1.0"
MODULE_AUTHOR = "Matthew Cutone"
MODULE_COPYRIGHT = "2012"

NORMALIZE_DATA = 0x00
NORMALIZE_CONTROL = 0x0B
POWER_OFF = 0x80
MOVE_LEFT = 0x20
MOVE_RIGHT = 0x10
DOME_CLOSE = 0x40
DOME_OPEN = 0x09 # Control
DOME_PULSE = 0x80
SENSE_ZERO_AZMTH = 0x20
SENSE_RAIN = 0x40

ACTION_BYTE_MAP = {'DOME_CCW' : MOVE_LEFT,
                   'DOME_CW'  : MOVE_RIGHT 
                  }

DOME_CMD_TABLE = {"SHUTTER_CLOSE": 'a',
                  "SHUTTER_OPEN": 'b',
                  "SHUTTER_STOP": 'c',
                  "DOME_CW": 'd',
                  "DOME_CCW": 'e',
                  "DOME_STOP": 'f',
                  "FOCUS_OUT": 'g',
                  "FOCUS_IN": 'h',
                  "FOCUS_STOP": 'i',
                  "CTRL_DISABLE": '7',
                  "CTRL_ENABLE": '8'}
                           
TRACKING_SPEED = -0.05

# The following are threaded tasks intended not to interfere with the GUI. They 
# communicate to the GUI using the Publisher() object. The GUI's functions are 
# invoked through the publisher. 
#
# NEW: The threaded code now executes lists of actions. The lists are in the
# following format:
#
# {0: [action, duration, delay}
#

def GetVersionStrings():
    return MODULE_LONG_NAME, MODULE_VERSION, MODULE_AUTHOR, MODULE_COPYRIGHT

CR_CHAR = chr(13)
CRLF_CHAR = CR_CHAR + chr(10)

class DomeControlInterface(threading.Thread):
    def __init__(self, port, baudrate, qin, qout, qerr):
        self.port = port
        self.baudrate = baudrate
        
        self.qin = qin
        self.qout = qout
        self.qerr = qerr
        
        threading.Thread.__init__(self)

        self._s = serial.Serial(self.port, self.baudrate, timeout=1, writeTimeout=1)
        
    def run(self):
        #self._s.setDTR(True)
        time.sleep(0.01)
        
        running = True
        while running:
            if not self.qin.empty():
                cmd = self.qin.get()
                
                if cmd in DOME_CMD_TABLE.keys():
                    self._s.write(DOME_CMD_TABLE[cmd])
                    self._s.flush()
                    time.sleep(0.1)
                    
                #if self.qin.get() == '?' and not self.qout.full():
                    
            
                    #self._s.write('?')
                    #time.sleep(0.01)
                    
                    #if self._s.inWaiting() > 0:
                        #byte = self._s.readline()[0:3]
                        #try:
                            #slew_rate, direction = byte.split(',')
                            
                            #if not self.qout.full():
                                #self.qout.put((slew_rate, direction))
                                
                            #self._s.flushInput()
                        #except:
                            #if not self.qout.full():
                                #self.qout.put((0, 0))
                            
                            #self._s.flushInput()
                            
            time.sleep(0.02)

class HandPaddleInterface(threading.Thread):
    def __init__(self, port, baudrate, qin, qout, qerr):
        self.port = port
        self.baudrate = baudrate
        
        self.qin = qin
        self.qout = qout
        self.qerr = qerr
        
        threading.Thread.__init__(self)

        self._s = serial.Serial(self.port, self.baudrate, timeout=1, writeTimeout=1)
        
    def run(self):
        #self._s.setDTR(True)
        time.sleep(0.01)
        
        running = True
        while running:
            if not self.qin.empty():
                if self.qin.get() == '?' and not self.qout.full():
            
                    self._s.write('?')
                    time.sleep(0.01)
                    
                    if self._s.inWaiting() > 0:
                        byte = self._s.readline()[0:3]
                        try:
                            slew_rate, direction = byte.split(',')
                            
                            if not self.qout.full():
                                self.qout.put((slew_rate, direction))
                                
                            self._s.flushInput()
                        except:
                            if not self.qout.full():
                                self.qout.put((0, 0))
                            
                            self._s.flushInput()
                            
            time.sleep(0.02)

class SerialCommDec(threading.Thread):
    def __init__(self, port, baudrate, qin, qout, qerr):
        self.port = port
        self.baudrate = baudrate
        
        self.qin = qin
        self.qout = qout
        self.qerr = qerr
        
        self.rdir = 1 # 1 or -1 for direction
        self.rvel = 8 # rotational velocity
        self.racc = 1 # rotational acceleration
        self.rdec = 1 # rotational deceleration
        self.svel = 0.05
        
        self.tracking = False

        threading.Thread.__init__(self)
        
        self._connection_attempts = 0
        
        # try to establish a connection 
        connected = self.AttemptConnection()
        
    def AttemptConnection(self):
        port_opened = False
        
        connection_attempts = 0
        
        while connection_attempts < 3:
            print("attempting to connect RA controller {0}/3".format(connection_attempts+1))
            # can we open the port?
            
            has_port = True
            try:
                self._s = serial.Serial(self.port, self.baudrate, timeout=1, writeTimeout=1)
            except:
                has_port = False
                print "cannot connect, I suck"

            # if open, does it respond when written to?
            if has_port:
                if self._s.isOpen():
                    can_write = True
                    can_read = True
                    try:
                        self._s.write("QT{cr}HR{cr}{cmd}{crlf}".format(cmd="RS", cr=CR_CHAR, crlf=CRLF_CHAR))
                    except serial.serialutil.writeTimeoutError:
                        can_write = False
                        self._s.close()
                    
                    try:
                        self._s.read(self._s.inWaiting())
                    except serial.serialutil.SerialTimeoutException:
                        can_read = False
                        self._s.close()
                        
                    if can_write and can_read: 
                        self._s.flush()
                        break
                else:
                    pass
                    #print "Nope"
            
            connection_attempts += 1
            
            time.sleep(0.1)
        
        if connection_attempts == 3: 
            port_opened = False
            self._s = None
        else: 
            port_opened = True
        
        self.qout.put(1)
        #self.qin.task_done()
            
        if port_opened:
            self.WriteReadSCL('PR5')
            self.WriteReadSCL('AC3')
            self.WriteReadSCL('DE3')
            self.WriteReadSCL('AM3')
            self.WriteReadSCL('VE8')
            self.WriteReadSCL('MT1') # multi-processing must be enabled 
            self.WriteReadSCL('JA8')
            self.WriteReadSCL('JL8')
            self.WriteReadSCL('JS5')
        
        return port_opened
    
    def IsMoving(self):
        moving = False
        status = self.WriteReadSCL('RS')
        
        if status != None:
            if ("M" in status) or ("J" in status):
                moving = True
        
        return moving
    
    def WriteReadSCL(self, cmd):
        try:
            self._s.write("QT{cr}HR{cr}{cmd}{crlf}".format(cmd=cmd, cr=CR_CHAR, crlf=CRLF_CHAR))
            self._s.flush()
        except:
            #self._s.close()
            self.AttemptConnection()
        
        resp = self.ReadSCL()
        
        return resp
    
    def ReadSCL(self):
        while True:
            try:
                c = self._s.read(self._s.inWaiting())
            except:
                #self._s.close()
                c = None
                self.AttemptConnection()
            
            if c != None:
                if len(c) > 0:
                    break
                else:
                    time.sleep(0.05)

        return c
        
    def run(self):
        # serial communication port
        #self._s.flushInput()
        #self._s.flushOutput()
        
        # begin control loop
        running = True
        while running:
            # =========================
            # Get Input for Queues
            # =========================
            if not self.qerr.empty():
                err = self.qerr.get()
                
                if err == 0:
                    print("THREAD {}: error {} recieved".format(self.port, err))

                elif err == 1:
                    print("THREAD {}: error {} recieved, ending process".format(self.port, err))
                    #running = False
                
                self.qerr.task_done()
            else:
                if not self.qin.empty():
                    cmd, val = self.qin.get()

                    print cmd
                    
                    if cmd == "MOVE":
                        moving = self.IsMoving()
                        if not moving:
                            self.WriteReadSCL('CJ'.format(self.rvel))
                            
                        self.qin.task_done()
                        
                    elif cmd == "STOP":
                        self.WriteReadSCL('SJ')
                        
                        while 1:
                            if not self.IsMoving():
                                break
                        
                        self.qout.put(1)
                        self.qin.task_done()
                    
                    elif cmd == "DI_NORTH":
                        self.rdir = -1
                        self.WriteReadSCL('DI{0}'.format(self.rdir))
                        
                    elif cmd == "DI_SOUTH":
                        self.rdir = 1
                        self.WriteReadSCL('DI{0}'.format(self.rdir))
                    
                    elif cmd == "SPEED":
                        self.rvel = val
                        self.WriteReadSCL('JS{0}'.format(self.rvel))
                    
                    elif cmd == "ACCEL":
                        self.racc = val
                        self.WriteReadSCL('JA{0}'.format(self.racc))
                        
                    elif cmd == "DECEL": 
                        self.rdec = val
                        self.WriteReadSCL('JL{0}'.format(self.rdec))
                            
                    elif cmd == "CLOSE":
                        self.WriteReadSCL('ST')
                        
                        #self._s.setDTR(False)
                        time.sleep(0.1)
                        self._s.close()
                        self._s = None
                        
                        running = False
                        self.qin.task_done()
                        self.join()
        

class SerialCommRA(threading.Thread):
    def __init__(self, port, baudrate, qin, qout, qerr):
        self.port = port
        self.baudrate = baudrate
        
        self.qin = qin
        self.qout = qout
        self.qerr = qerr
        
        self.rdir = 1 # 1 or -1 for direction
        self.rvel = 8 # rotational velocity
        self.racc = 1 # rotational acceleration
        self.rdec = 1 # rotational deceleration
        self.svel = 0.05
        
        self.tracking = False

        threading.Thread.__init__(self)
        
        connected = self.AttemptConnection()
        
        if connected:
            self.WriteReadSCL('PR5')
            self.WriteReadSCL('AC3')
            self.WriteReadSCL('DE3')
            self.WriteReadSCL('AM3')
            self.WriteReadSCL('VE8')
            self.WriteReadSCL('MT1') # multi-processing must be enabled 
            self.WriteReadSCL('JA8')
            self.WriteReadSCL('JL8')
            self.WriteReadSCL('JS5')
        
    def AttemptConnection(self):
        port_opened = False
        
        connection_attempts = 0
        
        while connection_attempts < 3:
            print("attempting to connect DEC controller {0}/3".format(connection_attempts+1))
            has_port = True
            try:
                self._s = serial.Serial(self.port, self.baudrate, timeout=1, writeTimeout=1)
            except:
                has_port = False
                print "cannot connect, I suck"

            # if open, does it respond when written to?
            if has_port:
                if self._s.isOpen():
                    can_write = True
                    can_read = True
                    try:
                        self._s.write("QT{cr}HR{cr}{cmd}{crlf}".format(cmd="RS", cr=CR_CHAR, crlf=CRLF_CHAR))
                    except serial.serialutil.writeTimeoutError:
                        can_write = False
                        self._s.close()
                    
                    try:
                        self._s.read(self._s.inWaiting())
                    except serial.serialutil.SerialTimeoutException:
                        can_read = False
                        self._s.close()
                        
                    if can_write and can_read: 
                        self._s.flush()
                        break
                else:
                    pass
                    #print "Nope"

            connection_attempts += 1
            
            time.sleep(0.1)
        
        if connection_attempts == 3: 
            port_opened = False
            self._s = None
        else: 
            port_opened = True

        self.qout.put(1)
        #self.qin.task_done()

        if port_opened:
            self.WriteReadSCL('PR5')
            self.WriteReadSCL('AC3')
            self.WriteReadSCL('DE3')
            self.WriteReadSCL('AM3')
            self.WriteReadSCL('VE8')
            self.WriteReadSCL('MT1') # multi-processing must be enabled 
            self.WriteReadSCL('JA8')
            self.WriteReadSCL('JL8')
            self.WriteReadSCL('JS5')
        
        return port_opened
    
    def IsMoving(self):
        moving = False
        status = self.WriteReadSCL('RS')
        
        if status != None:
            if ("M" in status) or ("J" in status):
                moving = True
        
        return moving
    
    def WriteReadSCL(self, cmd):
        try:
            self._s.write("QT{cr}HR{cr}{cmd}{crlf}".format(cmd=cmd, cr=CR_CHAR, crlf=CRLF_CHAR))
            self._s.flush()
        except:
            #self._s.close()
            self.AttemptConnection()
        
        resp = self.ReadSCL()
        
        return resp
    
    def ReadSCL(self):
        while True:
            try:
                c = self._s.read(self._s.inWaiting())
            except:
                #self._s.close()
                c = None
                self.AttemptConnection()
            
            if c != None:
                if len(c) > 0:
                    break
                else:
                    time.sleep(0.05)
                    
        return c
        
    def run(self):

        # 0 = stop motion
        # 1 = start jogging
        # 2 = start jogging
        
        # begin control loop
        running = True
        while running:
            if self._s != None:
                # =========================
                # Get Input for Queues
                # =========================
                if self._s != None:
                    if not self.qerr.empty():
                        err = self.qerr.get()
                        
                        if err == 0:
                            print("THREAD {0}: error {1} recieved".format(self.port, err))

                        elif err == 1:
                            print("THREAD {0}: error {1} recieved, ending process".format(self.port, err))
                            #running = False
                        
                        self.qerr.task_done()
                    else:
                        if not self.qin.empty():
                            cmd, val = self.qin.get()
                            
                            print cmd
                            
                            if cmd == "MOVE":
                                if not self.tracking:
                                    moving = self.IsMoving()
                                    if not moving:
                                        self.WriteReadSCL('CJ'.format(self.rvel))
                                else:
                                    pass
                                    
                                self.qin.task_done()
                                
                            elif cmd == "STOP":
                                if not self.tracking:
                                    self.WriteReadSCL('SJ')
                                    
                                    while 1:
                                        if not self.IsMoving():
                                            self.qout.put(1)
                                            break
                                    
                                else:
                                    self.WriteReadSCL('CS{0}'.format(TRACKING_SPEED))
                                    self.qout.put(1)
                                    
                                self.qin.task_done()
                            
                            elif cmd == "DI_EAST":
                                if not self.tracking:
                                    self.rdir = 1
                                    self.WriteReadSCL('DI{0}'.format(self.rdir))
                                else:
                                    self.WriteReadSCL('CS{0}'.format(self.rvel+TRACKING_SPEED))
                                
                            elif cmd == "DI_WEST":
                                if not self.tracking:
                                    self.rdir = -1
                                    self.WriteReadSCL('DI{0}'.format(self.rdir))
                                else:
                                    self.WriteReadSCL('CS{0}'.format(-(self.rvel+TRACKING_SPEED)))
                            
                            elif cmd == "START_TRACK":
                                if not self.tracking:
                                    self.rdir = -1
                                    self.WriteReadSCL('DI{0}'.format(self.rdir))
                                    self.WriteReadSCL('JS{0}'.format(-TRACKING_SPEED))
                                    self.WriteReadSCL('CJ')
                                
                                    self.tracking = True
                                
                                else:
                                    pass
                            
                            elif cmd == "STOP_TRACK":
                                self.WriteReadSCL('ST')
                                
                                while 1:
                                    if not self.IsMoving():
                                        break
                                
                                self.tracking = False
                                print("put")
                                self.qout.put(1)
                                self.qin.task_done()
                            
                            elif cmd == "SPEED":
                                self.rvel = val
                                self.WriteReadSCL('JS{0}'.format(self.rvel))
                            
                            elif cmd == "ACCEL":
                                self.racc = val
                                self.WriteReadSCL('JA{0}'.format(self.racc))
                                
                            elif cmd == "DECEL": 
                                self.rdec = val
                                self.WriteReadSCL('JL{0}'.format(self.rdec))
                                    
                            elif cmd == "CLOSE":
                                self.WriteReadSCL('ST')
                                
                                #self._s.setDTR(False)
                                time.sleep(0.1)
                                self._s.close()
                                self._s = None
                                
                                running = False
                                self.qin.task_done()
                                self.join()

class ThreadedHardwareMacroAction(threading.Thread):
    def __init__(self, qin, action, duration, delay=2.5):
        self.action = action
        self.duration = duration
        self.delay = delay
        self.qin = qin
        threading.Thread.__init__(self)

    def run(self):
        print("do step {}".format(self.action))
        self.qin.put(self.action)
        time.sleep(self.duration)
        self.qin.put("DOME_STOP")
        # inter-action delay to protect motors from damage
        time.sleep(self.delay)
        
        wx.CallAfter(Publisher().sendMessage, "macro", 0)

#class ThreadedHardwareMacroAction(threading.Thread):
    #def __init__(self, qin, actions, delay=2.5):
        #self.actions = actions # actions dictionary
        #self.delay = delay
        #self.qin = qin
        #threading.Thread.__init__(self)

    #def run(self):
        #for key in self.actions.keys():
            #action, duration, delay = actions[key]
            #self.qin.put(action)
            #time.sleep(duration)
            ## reset the controller
            ##self.hwc.resetDataRange()
            
            #self.qin.put("DOME_STOP")
            ## inter-action delay to protect motors from damage
            #time.sleep(delay)
        
        #wx.CallAfter(Publisher().sendMessage, "macro", 0)
        
        #del self.hwc
        
class ThreadedDomeRotation(threading.Thread):
    def __init__(self, port='lpt1', direction='cw', domeAngle=5):
        self.direction = direction
        self.angle = domeAngle
        self.hwc = obslib.ApparatusInterface('lpt1')
        threading.Thread.__init__(self)
        
    def run(self):
        #self.hwc.moveDome(self.direction, self.angle)
        time.sleep(5)
        wx.CallAfter(Publisher().sendMessage, "update", False)
        
        del self.hwc

class ThreadedSystemShutdown(threading.Thread):
    def __init__(self, dc_qin, stoptrackfunc):
        self.dc_qin = dc_qin
        self.stoptrackfunc = stoptrackfunc
        
        self.abort = False
        
        threading.Thread.__init__(self)
        
    def run(self):
        step = 0
        while True:
            if self.abort:
                wx.CallAfter(Publisher().sendMessage, "display", "Shutdown routine caught abort signal, shutdown procedure halted!")
                wx.CallAfter(Publisher().sendMessage, "shutdown", 0)
                
                break
            else:
                if step == 0:
                    wx.CallAfter(Publisher().sendMessage, "display", "Disabling tracking and stopping dome.")
                    self.dc_qin.put("DOME_STOP")
                    self.stoptrackfunc()
                    time.sleep(15.0)
                    wx.CallAfter(Publisher().sendMessage, "display", "Second attempt to stop tracking. Hope you checked the limit switches ...")
                    self.stoptrackfunc()
                    time.sleep(1.0)
                    
                elif step == 1:
                    wx.CallAfter(Publisher().sendMessage, "display", "First attempt to close dome shutter.")
                    self.dc_qin.put("SHUTTER_CLOSE")
                    
                    time.sleep(2.0)
                    
                elif step == 2:
                    wx.CallAfter(Publisher().sendMessage, "display", "Second attempt to close dome shutter.")
                    self.dc_qin.put("SHUTTER_CLOSE")
                    
                    time.sleep(2.0)
    
                elif step == 3:
                    wx.CallAfter(Publisher().sendMessage, "display", "Shutdown procedure completed, bye.")
                    wx.CallAfter(Publisher().sendMessage, "shutdown", 0)
                    
                    break
                 
                #elif step == 3:
                    #wx.CallAfter(Publisher().sendMessage, "display", "Disconnecting power to the telescope.")
                    #self.hwc.powerOff()
                    #time.sleep(DEFAULT_SLEEP_TIME)
                
                #elif step == 4:
                    #wx.CallAfter(Publisher().sendMessage, "display", "Rotating dome to zero azimuth.")
                    #self.hwc.zeroDomeAzmth()
                    #time.sleep(DEFAULT_SLEEP_TIME)
                
                #elif step == 5:
                    #wx.CallAfter(Publisher().sendMessage, "display", "Rotating dome to maximize solar energy collection.")
                    #self.hwc.solarAlign()
                    #self.hwc.resetDataRange()
                    #self.hwc.resetControlRange()
                    #time.sleep(DEFAULT_SLEEP_TIME)
                    
                #elif step == 6:
                    #wx.CallAfter(Publisher().sendMessage, "display", "Shutdown procedure completed, bye.")
                    #wx.CallAfter(Publisher().sendMessage, "shutdown", 0)
                    
                    #del self.hwc
                    
                    break # last step so we break the loop
                
                step += 1
                
                
# SIDERIAL DRIVE
## enable sideral drive
#req_dat = self.WriteReadSCL('RS')
#if 'J' in req_dat:
    #r_dir = self.WriteReadSCL('DI').split('=').strip(CR_CHAR)
    #if int(float(r_dir[1])) == -1:
        ## if going same direction, throttle down
        #self.WriteReadSCL('CS{}'.format(self.svel))
    #elif int(float(r_dir[1])) == 1:
        ## if going opposite direction, stop then jog
        #while 1:
            #req_dat = self.WriteReadSCL('RS')
            #if 'J' not in req_dat:
                #break;
        
        #self.WriteReadSCL('JS{}'.format(self.svel))

#elif 'F' not in req_dat:
