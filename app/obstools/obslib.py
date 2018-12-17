# ======================================================================
# HARDWARE CONTROLLER - 60CM TELESCOPE DRIVER
# ======================================================================

# -- NOTES --
# 1. Hardware Control Driver for the 60CM telescope at York University.
#    I/O ranges are backwards on this IBM laptop, need to be changed
#    on the production machine. Were are out of luck on future versions
#    of Windows since the LPT port is no longer supported.

# -- RANGES --
# I/O RANGE  |  PORT NAME
# ----------------------------------------------------------------------
# 3bc - 3bf  |  MDA/LPT parallel port (still used on ThinkPads)
# 378 - 37f  |  LPT1 parallel port (typical)
# 278 - 27f  |  LPT2 parallel port (rare)

''' HARDWARE CONTROLLER - 60CM TELESCOPE DRIVER '''

import os
import sys
import ctypes
import time
import string
import math
import platform

MAX_BUFFER_SIZE = 0xff
DEFAULT_PARALLEL_PORT = 'lpt1'
DEGREE_PER_PULSE = 1.4388889
DEFAULT_SLEEP_TIME = 5.0
SOLAR_ALIGN_TIME = 8.0
DOME_OPEN_TIME = 90.0 # 5 seconds more than timed

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

# ======================================================================
# HARDWARE INTERFACE CLASS: wrapper of inpout.dll
# ======================================================================

class HardwareInterface:
    def __init__(self, port=DEFAULT_PARALLEL_PORT):
        ''' Initialize the parallel port DLL and create a python object.
        Get the I/O range for the selected port. '''
        self.port = ctypes.windll.inpout32
        self.dataAddr, self.statusAddr, self.controlAddr = self.__getPortRanges(port)

    def setData(self, data):
        ''' Write data to the data port; returns getDataRangeState() if data
        is valid, else returns 0 '''
        if data <= MAX_BUFFER_SIZE:
            self.port.Out32(self.dataAddr, data)
            return self.getDataRangeState()
        else:
            return 0

    def setControl(self, data):
        ''' Write data to the data port; returns getControlRangeState() if data
        is valid, else returns 0 '''
        if data <= MAX_BUFFER_SIZE:
            self.port.Out32(self.controlAddr, data)
            return self.getControlRangeState()
        else:
            return 0

    def resetDataRange(self):
        ''' Normalize parrallel port data range by writing normalizing byte '''
        self.port.Out32(self.dataAddr, NORMALIZE_DATA)
        
        return 1

    def resetControlRange(self):
        ''' Normalize parrallel port control range by writing normalizing byte '''
        self.port.Out32(self.controlAddr, NORMALIZE_CONTROL)
        
        return 1

    def getDataRangeState(self):
        ''' Get data range state; returns state '''
        state = self.port.Inp32(self.dataAddr)
        
        return state

    def getStatusRangeState(self):
        ''' Get status range state; returns state '''
        state = self.port.Inp32(self.statusAddr)
        
        return state

    def getControlRangeState(self):
        ''' Get control range state; returns state '''
        state = self.port.Inp32(self.controlAddr)
        
        return state

    def __getPortRanges(self, port='lpt1'):
        ''' Calculate port addresses for given parallel port, returns 
        (dataAddr, statusAddr, controlAddr) '''
        #addrBase = {'lpt1' : 0xEC00, 'lpt2' : 0xE880, 'mda' : 0xE800} # 64-bit
        #if (sys.maxsize > 2**32):
            #addrBase = {'lpt1' : 0xEC00, 'lpt2' : 0xE880, 'mda' : 0xE800} # 64-bit
        #else:
        addrBase = {'lpt1' : 0x378, 'lpt2' : 0x278, 'mda' : 0x3bc} # 32-bit
        
        port = port.lower()

        if port in addrBase.keys():
            baseAddr = addrBase[port]

            # Typical LTP parallel port address ranges
            dataAddr = baseAddr
            statusAddr = baseAddr + 1
            controlAddr = baseAddr + 2

            return (dataAddr, statusAddr, controlAddr)

        else:
            return 0 # return this if port name is invalid

# ======================================================================
# DOME INTERFACE CLASS
# ======================================================================

class ApparatusInterface(HardwareInterface):
    def __init__(self, port=DEFAULT_PARALLEL_PORT):
        ''' Initializes the hardware interface module and inherits its methods. '''
        HardwareInterface.__init__(self, port)
        self.coverOpen = False # assumes cover is closed on start
        self.domeAngle = 0.00
    
    def isOpen(self):
        return self.coverOpen

    def powerOff(self):
        ''' Shutdown the telescope control console; returns 1 '''
        self.setData(POWER_OFF)
        time.sleep(DEFAULT_SLEEP_TIME)
        self.resetDataRange()
        
        return 1

    def solarAlign(self):
        ''' Move telescope to face south to optimize solar collector, 
        call after dome is at zero; returns 1 '''
        # Move dome 25 degrees from zero to optimize solar capture.
        self.setData(MOVE_RIGHT)
        time.sleep(SOLAR_ALIGN_TIME) # solar align takes 8 seconds from zero - mdc: 12/08/13

        self.resetDataRange()
        self.resetControlRange()
        
        return 1
    
    def DetectVoltage(self):
        state = False

        if (self.getStatusRangeState() & SENSE_RAIN) == SENSE_RAIN:
            state = True

        return state

    def getRainPulse(self):
        ''' Check rain detector for signal; if raining returns True else 
        returns False '''
        # getRainPulses() is designed to grab a byte from the STATUS port,
        # where the rain sensor is connected, and check to see if it has
        # sensed rain.  Since the pin the rain sensor is attached to is
        # an INVERTED pin, - if a '1' is found, the port is 'low'
        #                  - if a '0' is found, the port is 'high' and a
        #                    detection has been made
        # getRainPulses() is a boolean function, simply returning 'true'
        # or 'false' depending on if rain is detected or not
        # [rainSensor is on pin#10, @ BASE+01, hex mask 0x040]

        state = True # pin is inverted so negate

        #CHECK HEX-mask....might not be correct
        if (self.getStatusRangeState() & SENSE_RAIN) == SENSE_RAIN:
            state = False

        return state

    def zeroDomeAzmth(self):
        ''' Zero the dome to azimuth, dome will rotate until it reached 
        zero; returns 1 '''
        self.setData(MOVE_LEFT)

        RUNNING = 1
        while RUNNING:
            isAbsPosition = self.getStatusRangeState() & SENSE_ZERO_AZMTH
            if isAbsPosition == SENSE_ZERO_AZMTH:
                RUNNING = 0

        self.resetDataRange()
        self.resetControlRange()
        
        return 1

    def moveDome(self, direction, degrees):
        ''' Move dome CW or CCW at arbitrary angle (degrees); returns 1 '''
        # The moveDome routine is a generic method that receives the direction
        # of movement, and by how many degrees, and tells the dome to move
        # by those parameters.
        # Since the dome works in 'pulses' and not degrees, the method first
        # converts the degrees to pulses then sends the dome moving
        # it counts the pulses and then exits the moving when the pulses are
        # equal to the required amount.

        spin = {'cw' : MOVE_RIGHT, 'ccw' : MOVE_LEFT}
        pulses = degrees * DEGREE_PER_PULSE

        pulses = int(pulses) # convert pulses to integer
        initialState = self.getStatusRangeState() & DOME_PULSE

        self.setData(spin[direction])
        total = 0
        while (total < pulses):
            currentState = self.getStatusRangeState() & DOME_PULSE
            time.sleep(0.01)
            if initialState != currentState:
                total += 1
                initialState = currentState

        self.resetDataRange()
        
        return 1

    def openDome(self, blocking=False):
        ''' Sends signal to open the dome; returns 1 '''
        self.setControl(DOME_OPEN)
        time.sleep(DEFAULT_SLEEP_TIME)
        
        if blocking:
            time.sleep(DOME_OPEN_TIME)
            
        self.resetControlRange()
        self.coverOpen = True
        
        return 1

    def closeDome(self):
        ''' Sends signal to close the dome; returns 1 '''
        self.setData(DOME_CLOSE)
        time.sleep(DEFAULT_SLEEP_TIME)
        self.resetDataRange()
        
        return 1

    def totalShutDown(self):
        ''' Function to shutdown the entire apparatus. Closes dome, 
        powers down the telescope, zeros the dome, and solar aligns; returns 1 '''
        # The totalShutDown() routine is designed to robustly and completely shut down 
        # the entire apparatus. It begins by closing the dome. The program could
        # be shutting down due to rain, so it's important to first close the      
        # dome.  The second step is to turn off the telescope.  Third is to       
        # bring the dome back to zero azimuth or 'park'                           
        #                                                                         
        # After parking the dome, the port is initialized using the               
        # initializedPort() routine and then program is terminated.               
        #                                                                         
        # As of 12 May 2009, this routine does not park the telescope, 
        # it only turns it off - will be added in the future.     
        #                                                                         
        # Each step is accompanied with a logfile record and a 10 second delay. 

        self.closeDome()
        time.sleep(DEFAULT_SLEEP_TIME)
        self.powerOff()
        time.sleep(DEFAULT_SLEEP_TIME)
        self.zeroDomeAzmth()
        time.sleep(DEFAULT_SLEEP_TIME)
        self.solarAlign()
        self.resetDataRange()
        self.resetControlRange()
        time.sleep(DEFAULT_SLEEP_TIME)
        
        return 1

# ======================================================================
# TEST FUNCTIONS
# ======================================================================

def displayParallelStatus(hwc):
    print "DATA RANGE    :", hwc.getDataRangeState()
    print "CONTROL RANGE :", hwc.getControlRangeState()
    print "STATUS RANGE  :", hwc.getStatusRangeState()

def main():
	
    return 1

if __name__ == '__main__':
    main()

