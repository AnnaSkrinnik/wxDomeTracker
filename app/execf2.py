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
    
class SerialCommProcess(threading.Thread):
    def __init__(self, port, baudrate, qin, qconf, qout, qerr):
        self.port = port
        self.baudrate = baudrate
        
        self.qin = qin
        self.qconf = qconf
        self.qout = qout
        self.qerr = qerr
        
        self.rdir = 1 # 1 or -1 for direction
        self.rvel = 8 # rotational velocity
        self.racc = 1 # rotational acceleration
        self.rdec = 1 # rotational deceleration
        self.svel = 3
        
        self.tracking = False

        threading.Thread.__init__(self)

        self._s = serial.Serial(self.port, self.baudrate, timeout=1, writeTimeout=1)
    
    def WriteReadSCL(self, cmd):
        self._s.write("{cmd}{cr}".format(cmd=cmd, cr=CR_CHAR))
        self._s.flush()
        
        resp = self.ReadSCL()
        
        return resp
    
    def ReadSCL(self):
        t_buff = ""
        while 1:
            if self._s.inWaiting() > 0:
                byte = self._s.read(1)
                t_buff += byte
                
                if byte == CR_CHAR:
                    break
        
        return t_buff
        
    def run(self):
        # serial communication port
        self.WriteReadSCL('PR5')
        self.WriteReadSCL('AC3')
        self.WriteReadSCL('DE3')
        self.WriteReadSCL('AM3')
        self.WriteReadSCL('VE8')
        self.WriteReadSCL('MT1') # multi-processing must be enabled 
        self.WriteReadSCL('JA8')
        self.WriteReadSCL('JL8')
        self.WriteReadSCL('JS5')
        
        # 0 = stop motion
        # 1 = start jogging
        # 2 = start jogging
        
        # begin control loop
        running = True
        while running:
            if not self.qerr.empty():
                err = self.qerr.get()
                
                if err == 0:
                    print("THREAD {}: error {} recieved".format(self.port, err))

                elif err == 1:
                    print("THREAD {}: error {} recieved, ending process".format(self.port, err))
                    #running = False
                
                self.qerr.task_done()
            else:
                if not self.qconf.empty():
                    key, value = self.qconf.get()
                    if key == 0: 
                        self.rvel = value # set velocity
                        self.WriteReadSCL('JS{}'.format(self.rvel))
                    elif key == 1: 
                        self.rdir = value # set direction
                        self.WriteReadSCL('DI{}'.format(self.rdir))
                    elif key == 2: 
                        self.racc = value # set acceleration
                        self.WriteReadSCL('JA{}'.format(self.racc))
                    elif key == 3: 
                        self.rdec = value # set deceleration
                        self.WriteReadSCL('JL{}'.format(self.rdec))
                        
                    else:
                        pass
                    
                    self.qconf.task_done()
                
                if not self.qin.empty() and self.qconf.empty():
                    cmd = self.qin.get()
                    
                    if cmd == 1:
                        moving = ("M" in self.WriteReadSCL('RS'))
                        r_dir = self.WriteReadSCL('DI').strip(CR_CHAR).split('=')[1]
                        
                        if moving and (r_dir == '-1'):
                            self.WriteReadSCL('CS{}'.format(-self.rvel))
                        elif moving and (r_dir == '1'):
                            self.WriteReadSCL('SJ')
                            while 1:
                                req_dat = self.WriteReadSCL('RS')
                                if "M" not in req_dat:
                                    break;
                                
                            self.WriteReadSCL('CJ{}'.format(self.rvel))
                        else:
                            self.WriteReadSCL('CS{}'.format(-self.rvel))
                            #self.WriteReadSCL('CJ')
                            
                        self.qin.task_done()
                        
                    elif cmd == 0:
                        if self.tracking == True:    
                            moving = ("M" in self.WriteReadSCL('RS'))
                            r_dir = self.WriteReadSCL('DI').strip(CR_CHAR).split('=')[1]
                            
                            if moving and (r_dir == '-1'):
                                self.WriteReadSCL('CS{}'.format(-self.svel))
                            else:
                                
                        
                        else:
                            self.WriteReadSCL('SJ')
                            
                            # do not do anything else until the motors have stopped
                            while 1:
                                req_dat = self.WriteReadSCL('RS')
                                if 'J' not in req_dat:
                                    self.qout.put(1) # report stopped to main thread
                                    break;
                                
                    elif cmd == 3:
                        self.tracking = True
                        self.WriteReadSCL('SJ')
                        while 1:
                            req_dat = self.WriteReadSCL('RS')
                            if 'J' not in req_dat:
                                self.qout.put(1) # report stopped to main thread
                                break;
                                
                        self.WriteReadSCL('JS{}'.format(self.svel))
                        self.WriteReadSCL('DI{}'.format(-1)) # -1 for West
                        self.WriteReadSCL('CJ')
                        self.qin.task_done()
                    
                    elif cmd == 4:
                        self.tracking = False
                        while 1:
                            req_dat = self.WriteReadSCL('RS')
                            if 'J' not in req_dat:
                                self.qout.put(1) # report stopped to main thread
                                break;
                        
                        self.qin.task_done()
                                
                    elif cmd == 254:
                        pass
                        
                    elif cmd == 255:
                        self._s.close()
                        running = False
                        self.qin.task_done()
        
        self.join()
                
            #wx.CallAfter(Publisher().sendMessage, "ulconn", 0)
        
        #del self.hwc
    
class ThreadedHardwareMacroAction(threading.Thread):
    def __init__(self, port, actions, duration=5.00, delay=2.5):
        self.actions = actions
        self.duration = duration
        self.delay = delay
        threading.Thread.__init__(self)

    def run(self):
        self.hwc = obslib.ApparatusInterface('lpt1')
        self.hwc.setData(ACTION_BYTE_MAP[self.actions])
        time.sleep(self.duration)
        # reset the controller
        self.hwc.resetDataRange()
        
        wx.CallAfter(Publisher().sendMessage, "macro", 0)
        
        del self.hwc

class ThreadedHardwareMacroAction2(threading.Thread):
    def __init__(self, port, actions, delay=2.5):
        self.actions = actions # actions dictionary
        self.delay = delay
        threading.Thread.__init__(self)

    def run(self):
        self.hwc = obslib.ApparatusInterface('lpt1')
        for key in self.actions.keys():
            action, duration, delay = actions[key]
            self.hwc.setData(ACTION_BYTE_MAP[action])
            time.sleep(duration)
            # reset the controller
            self.hwc.resetDataRange()
            # inter-action delay to protect motors from damage
            time.sleep(delay)
        
        wx.CallAfter(Publisher().sendMessage, "macro", 0)
        
        del self.hwc
        
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
    def __init__(self, port):
        self.abort = False
        self.hwc = obslib.ApparatusInterface('lpt1')
        threading.Thread.__init__(self)
        
    def run(self):
        step = 0
        while True:
            if self.abort:
                wx.CallAfter(Publisher().sendMessage, "display", "Shutdown routine caught abort signal, shutdown procedure halted!")
                wx.CallAfter(Publisher().sendMessage, "shutdown", 0)
                
                del self.hwc
                
                break
            else:
                if step == 0:
                    wx.CallAfter(Publisher().sendMessage, "display", "Resetting data/control port ranges for shutdown routine.")
                    self.hwc.resetDataRange()
                    self.hwc.resetControlRange()
                    time.sleep(1.0)
                    
                elif step == 1:
                    wx.CallAfter(Publisher().sendMessage, "display", "First attempt to close dome shutter.")
                    self.hwc.closeDome()
                    #time.sleep(DEFAULT_SLEEP_TIME)
                    
                    self.hwc.resetDataRange()
                    self.hwc.resetControlRange()
                    time.sleep(2.0)
                    
                elif step == 2:
                    wx.CallAfter(Publisher().sendMessage, "display", "Second attempt to close dome shutter.")
                    self.hwc.closeDome()
                    #time.sleep(DEFAULT_SLEEP_TIME)
                    
                    self.hwc.resetDataRange()
                    self.hwc.resetControlRange()
                    time.sleep(2.0)
                 
                elif step == 3:
                    wx.CallAfter(Publisher().sendMessage, "display", "Disconnecting power to the telescope.")
                    self.hwc.powerOff()
                    time.sleep(DEFAULT_SLEEP_TIME)
                
                elif step == 4:
                    wx.CallAfter(Publisher().sendMessage, "display", "Rotating dome to zero azimuth.")
                    self.hwc.zeroDomeAzmth()
                    time.sleep(DEFAULT_SLEEP_TIME)
                
                elif step == 5:
                    wx.CallAfter(Publisher().sendMessage, "display", "Rotating dome to maximize solar energy collection.")
                    self.hwc.solarAlign()
                    self.hwc.resetDataRange()
                    self.hwc.resetControlRange()
                    time.sleep(DEFAULT_SLEEP_TIME)
                elif step == 6:
                    wx.CallAfter(Publisher().sendMessage, "display", "Shutdown procedure completed, bye.")
                    wx.CallAfter(Publisher().sendMessage, "shutdown", 0)
                    
                    del self.hwc
                    
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
