#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

# The SystemStateObject stores a large amount of variables used by the executive
# functions of the program. Storing these values in this object allows for
# centralized maintainence of these values. This object is instanced ONCE when
# the main application is started. 
#
# As per the specification of version 4.0, calculations are done within this 
# module to avoid redundancy.

# This file was created on 2012-01-12.

import sys
import os
import wx
import threading
import time

from obstools import obsmathlib
from obstools import argoterm
from obstools import obslib

MODULE_LONG_NAME = "System State Object"
MODULE_VERSION = "0.1.0"
MODULE_AUTHOR = "Matthew Cutone"
MODULE_COPYRIGHT = "2012"

def GetVersionStrings():
    return MODULE_LONG_NAME, MODULE_VERSION, MODULE_AUTHOR, MODULE_COPYRIGHT

class SystemStateObject(object):
    def __init__(self):
        #
        # Initialize default system variable values when this object is
        # instanced. All these values are to be accessed/updated within this
        # class.
        #
        
        self.interface_vars = {"TERMINAL_COM_ADDR"      : 0,
                               "TERMINAL_BAUDRATE"      : 38400,
                               "TERMINAL_INTERVAL"      : 500,
                               "PARALLEL_PORT"          : 'lpt1',
                               "ARGO_CONNECTED"         : False,
                               "ARGO_CONN_OBJECT"       : None,
                               "ARGO_COORDINATES"       : ((0,0,0), (0,0,0))
                              }
        self.device_vars    = {}
        self.server_vars    = {"SERVER_ON_START"        : 0,
                               "SERVER_HOST_ADDR"       : 'localhost',
                               "SERVER_PORT"            : 10001,
                               "SERVER_REFRESH"         : 150,
                               "SERVER_ACTIVE"          : False
                              }        
        self.telescope_vars = {
                               "TELESCOPE_LATITUDE"     : 43.775,
                               "TELESCOPE_LONGITUDE"    : -79.5,
                               "TELESCOPE_RA"           : (0,0,0),
                               "TELESCOPE_DEC"          : (0,0,0),
                               "TELESCOPE_HA"           : (0,0,0),
                               "TELESCOPE_ALT"          : 0.0,
                               "TELESCOPE_AZMTH"        : 0.0,
                               "TELESCOPE_AIRMASS"      : 0.0,
                               "TELESCOPE_MODE"         : 1,
                               "VIRTUAL_COORDINATES"    : ((0,0,0), (0,0,0))
                              }
        self.target_vars    = None # empty means no target selected
        self.time_vars      = {"CURRENT_GMT"            : (0,0,0),
                               "CURRENT_LT"             : (0,0,0),
                               "CURRENT_LMST"           : (0,0,0),
                               "JULIAN_DATE"            : 0.0,
                               "TIME_FRACTION"          : 0.0
                              }
        self.dome_vars      = {"DOME_OBJ_ALT"           : 0.0,
                               "DOME_OBJ_AZMTH"         : 0.0,
                               "DOME_OBJ_AIRMASS"       : 0.0,
                               "DOME_LAST_ALT"          : 0.0,
                               "DOME_LAST_AZMTH"        : 0.0,
                               "DOME_POSITION"          : 0.0,
                               "DOME_ACCUM"             : 0.0,
                               "DOME_MOTION"            : False,
                               "TRACK_MODE"             : 1,
                               "TRACK_ENABLED"          : False,
                               "TRACK_INTERVAL"         : 60,
                               "TRACK_THRESH"           : 5,
                               "TRACK_STAGE"            : 0
                              } 
        self.shutdown_vars  = {"SHUTDOWN_ENABLED"       : False,
                               "SHUTDOWN_DAY"           : 1,
                               "SHUTDOWN_MONTH"         : 1,
                               "SHUTDOWN_YEAR"          : 2011,
                               "SHUTDOWN_HOUR"          : 0,
                               "SHUTDOWN_MINUTE"        : 0,
                               "SHUTDOWN_ACTIVE"        : False
                              }
        self.sensor_vars    = {"SENSOR_ENABLED"         : True,
                               "SENSOR_INTERVAL"        : 1,
                               "SENSOR_WARNING"         : True,
                               "SENSOR_SHUTDOWN"        : True,
                               "SENSOR_DELAY"           : 300000,
                               "SENSOR_STATE"           : False
                              }
        self.calibr_vars    = {"CALIBRATION_ENABLED"    : True,
                               "CALIBRATION_RA_OFFSET"  : 0.0,
                               "CALIBRATION_DEC_OFFSET" : 0.0,
                               "CALIBRATION_OBJECT"     : None
                              }
        self.gui_vars       = {"GUI_CTRL_COUNT"         : 0,
                               "GUI_DISP_COUNT"         : 0,
                               "FILE_LOG_DIRECTORY"     : None,
                               "FILE_LOG_PATH"          : None,
                               "WEATHER_CURRENT"        : None,
                               "WEATHER_URL"            : None,
                               "BRIGHT_STARS_VISIBLE"   : False
                              }
        self.macros_vars    = {"MACRO_NAME"             : None,
                               "MACRO_RECORDING"        : False,
                               "MACRO_EVENT_RECORD"     : False,
                               "MACRO_RUNNING"          : False,
                               "MACRO_FLAGS"            : (False, False, False, False), # dome motion, telescope motion, power, focus
                               "MACRO_SCALE"            : 0, # 0 = siderial, 1 = local time
                               "MACRO_FILE_PATH"        : None
                              }
                              
        self.current_macro  = None
        
        #
        # This variable stores 'process' information. Processes are registered
        # here and used to keep track of running code. There are only a few
        # processes such as dome tracking, macro playback and hardware movement.
        #
        # This system allows us to prevent incompatible processes from running
        # together. 
        #
        # MDC
        #
        
        self.dt_processes   = []
    
    def LoadHWInterfaces(self, f_hwi):
        #
        # Load keys from file
        #
        exclude_vars = ["ARGO_CONNECTED", "ARGO_CONN_OBJECT", "ARGO_COORDINATES"]
        int_vars = ["TERMINAL_COM_ADDR", "TERMINAL_BAUDRATE", 
            "TERMINAL_INTERVAL", "SERVER_PORT", "SERVER_REFRESH", "SERVER_ON_START"]
        bool_vars = []
        
        f_conf = open(f_hwi, 'r')
        for reg_line in f_conf.readlines():
            print reg_line
            if reg_line != "":
                s_key, s_var = reg_line.strip('\n ').split('=')
                if s_key not in exclude_vars:
                    if s_key in self.interface_vars.keys():
                        if s_key in int_vars:
                            self.interface_vars[s_key] = int(float(s_var))
                if s_key in self.server_vars.keys():
                    if s_key not in exclude_vars:
                        if s_key in int_vars:
                            self.server_vars[s_key] = int(float(s_var))
                else:
                    print('Warning: Unknown key "{0}" in config file!'.format(s_key))
            
        f_conf.close()
            
            
    def SaveHWInterfaces(self, f_hwi):
        #
        # Write keys to a file to be loaded later
        #
        exclude_vars = ["ARGO_CONNECTED", "ARGO_CONN_OBJECT", "ARGO_COORDINATES"]
        
        f_conf = open(f_hwi, 'w')
        # write vars for interface
        for s_key in self.interface_vars.keys():
            if s_key not in exclude_vars:
                key_var = self.interface_vars[s_key]
                f_conf.write('{0}={1}\n'.format(s_key, key_var))
        
        # write vars for server 
        for s_key in self.server_vars.keys():
            if s_key not in exclude_vars:
                key_var = self.server_vars[s_key]
                f_conf.write('{0}={1}\n'.format(s_key, key_var))
            
        f_conf.close()
        
    def registerProcess(self, p_type):        
        self.dt_processes.append(p_type)
    
    def removeProcess(self, p_type):
        pass
    
    def getProcesses(self):
        return 0
    
    def updateSystemTime(self):
        # this is the primary function that updates this software's internal
        # time representation. this must be updated only once per main loop 
        # cycle in order to ensure that all calculations are done using the 
        # same time.
        
        currentUTC = time.gmtime()
        currentLT = time.localtime()
        
        year = currentUTC[0]
        month = currentUTC[1]
        day = currentUTC[2]
        hour = currentUTC[3]
        min = currentUTC[4]
        sec = currentUTC[5]
        N = currentUTC[7]
        
        # calculate fractional seconds

        self.time_vars["CURRENT_GMT"] = currentUTC
        self.time_vars["CURRENT_LT"] = currentLT
        self.time_vars["CURRENT_LMST"] = obsmathlib.calculateLMST()
        self.time_vars["JULIAN_DATE"] = obsmathlib.convertDateTimeJD(
            (year, month, day), 
            (hour, min, sec))
        return 1
    
    def getSystemTimeParameters(self):
        return (self.time_vars["CURRENT_GMT"],
            self.time_vars["CURRENT_LT"],
            self.time_vars["CURRENT_LMST"],
            self.time_vars["JULIAN_DATE"])
    
    def getSiderialTime(self):
        siderial_time = self.time_vars["CURRENT_LMST"]
        sys_t = time.time()
        frac_t = sys_t - int(sys_t)
        
        hour, min, sec = siderial_time
            
        sec = float("%.1f" % (sec + frac_t))
        
        n_siderial_time = (hour, min, sec)
        
        return n_siderial_time
    
    def SetTelescopeMode(self, mode=1):
        # set the telescope mode, 0 = 'encoders'; 1 = 'virtual'
        self.telescope_vars["TELESCOPE_RA"] = mode
        
        return mode
        
    def computeTelescopeParameters(self, ra, dec):
        currentLMST = self.time_vars["CURRENT_LMST"]
        
        alt = obsmathlib.calculateAltitude(ra, dec, currentLMST)
        ha = obsmathlib.HoursToRightAscension(obsmathlib.calculateHourAngle(ra, currentLMST))
        azmth = obsmathlib.calculateAzimuth(ra, dec, alt, currentLMST)
        airmass = obsmathlib.calculateAirmass(ra, dec, currentLMST)

        self.telescope_vars["TELESCOPE_RA"] = ra
        self.telescope_vars["TELESCOPE_DEC"] = dec
        self.telescope_vars["TELESCOPE_ALT"] = alt
        self.telescope_vars["TELESCOPE_AZMTH"] = azmth
        self.telescope_vars["TELESCOPE_HA"] = ha
        self.telescope_vars["TELESCOPE_AIRMASS"] = airmass
        
        return (ra, dec, ha, azmth, alt, airmass)
    
    def clearSystemTragetObject(self):
        self.target_vars = None
        
        return 1
    
    def isTarget(self):
        # simple convienence function to check if there is a target or not
        target = False
        if self.target_vars:
            target = True
        
        return target
        
    def setSystemTargetObject(self, ra, dec, name, epoch):
        # Create a new target dictionary and then compute values.
        # 
        # Note: TARGET_DATA_EXT contains data from the HYG database. If the
        # value is "None", this means that the data has been manually entered
        # by the user. That only yields a RA, DEC, and NAME value. The use of 
        # extended information allows for more relevant display options.
        #
        
        self.target_vars = {"TARGET_ID" : 1000,
            "TARGET_NAME"            : None,
            "TARGET_ALT"             : 0.0,
            "TARGET_AZMTH"           : 0.0,
            "TARGET_REF_RA"          : (0,0,0),
            "TARGET_REF_DEC"         : (0,0,0),
            "TARGET_RA"              : (0,0,0),
            "TARGET_DEC"             : (0,0,0),
            "TARGET_HA"              : (0,0,0),
            "TARGET_AIRMASS"         : 0.0,
            "TARGET_REF_EPOCH"       : 2000.0,
            "TARGET_EPOCH"           : 2000.0,
            "TARGET_COLOUR"          : 0.0,
            "TARGET_CIRCUMPOLAR"     : False,
            "TARGET_NEVER_VISIBLE"   : False,
            "TARGET_DATA_EXT"        : None
            }
        
        self.target_vars["TARGET_ID"] = 1000
        self.target_vars["TARGET_NAME"] = name
        self.target_vars["TARGET_REF_RA"] = ra
        self.target_vars["TARGET_REF_DEC"] = dec
        self.target_vars["TARGET_REF_EPOCH"] = epoch
        
        # compute if the star is circumpolar
        
        observer_latitude = self.telescope_vars["TELESCOPE_LATITUDE"]
        deg, mm, ss = self.target_vars["TARGET_REF_DEC"]
        object_declination = obsmathlib.DeclinationToDegrees(deg, mm, ss)
        
        if observer_latitude >= 0.0: # northern hemisphere (dec + lat) > 90
            if (object_declination + observer_latitude) > 90.0: 
                self.target_vars["TARGET_CIRCUMPOLAR"] = True
            else:
                self.target_vars["TARGET_CIRCUMPOLAR"] = False
        else:
            if (object_declination + observer_latitude) < -90.0: 
                self.target_vars["TARGET_CIRCUMPOLAR"] = True
            else:
                self.target_vars["TARGET_CIRCUMPOLAR"] = False
        
        return self.updateSystemTargetObject()

    def getSystemTargetInfo(self):
        target_data = (self.target_vars["TARGET_RA"],
            self.target_vars["TARGET_DEC"],
            self.target_vars["TARGET_EPOCH"],
            self.target_vars["TARGET_HA"],
            self.target_vars["TARGET_AZMTH"],
            self.target_vars["TARGET_ALT"],
            self.target_vars["TARGET_AIRMASS"],
            self.target_vars["TARGET_COLOUR"]
            )
            
        return target_data
        
    def updateSystemTargetObject(self, update_only=False):
        # if there is a target, recalculate all the values
        if self.target_vars:
            currentLMST = self.time_vars["CURRENT_LMST"]
            
            ra = self.target_vars["TARGET_REF_RA"]
            dec = self.target_vars["TARGET_REF_DEC"]
            epoch = self.target_vars["TARGET_REF_EPOCH"]
            colour = self.target_vars["TARGET_COLOUR"]
            
            new_ra, new_dec, new_epoch, ha, azmth, alt, airmass = self.computeObjectParameters(ra, dec, epoch)
            
            self.target_vars["TARGET_RA"] = new_ra
            self.target_vars["TARGET_DEC"] = new_dec
            self.target_vars["TARGET_AZMTH"] = azmth
            self.target_vars["TARGET_ALT"] = alt
            self.target_vars["TARGET_HA"] = ha
            self.target_vars["TARGET_AIRMASS"] = airmass
            self.target_vars["TARGET_EPOCH"] = new_epoch
            
            if not update_only:
                target_data = (new_ra, new_dec, new_epoch, 
                    ha, azmth, alt, airmass, colour)
            else:
                target_data = 1
        else:
            target_data = None
        
        return target_data
        
    def computeObjectParameters(self, ra, dec, epoch):
        currentLMST = self.time_vars["CURRENT_LMST"]
        
        new_ra, new_dec, new_epoch = obsmathlib.epochConvert(ra, dec, epoch)
        alt = obsmathlib.calculateAltitude(new_ra, new_dec, currentLMST)
        ha = obsmathlib.HoursToRightAscension(obsmathlib.calculateHourAngle(new_ra, currentLMST))
        azmth = obsmathlib.calculateAzimuth(new_ra, new_dec, alt, currentLMST)
        airmass = obsmathlib.calculateAirmass(new_ra, new_dec, currentLMST)
        
        return (new_ra, new_dec, new_epoch, ha, azmth, alt, airmass)
    
    def shutdownConditionCheck(self):
        local_time = self.time_vars["CURRENT_LT"]
        hour = local_time[0]
        min = local_time[1]
        
        shutdown_active = self.shutdown_vars["SHUTDOWN_ACTIVE"]
        shutdown_hour = self.shutdown_vars["SHUTDOWN_HOUR"]
        shutdown_min = self.shutdown_vars["SHUTDOWN_MINUTE"]
        
        dome_motion = self.dome_vars["DOME_MOTION"]
        target_airmass = self.target_vars["TARGET_AIRMASS"]
        
        #if shutdown_active != True and dome_motion == 0:
            ## shutdown time check
            #if (hour == self.shutdownHour) and (min == self.shutdownMinute) and self.shutdownEnabled:
                #self.shutdown_vars["SHUTDOWN_ACTIVE"] = True
                #msg = "System shutdown time has elapsed, shutdown procedure will initiate NOW!"
                #self.parent.writeOutput(msg, timestamp=True)
                #self.parent.tmrDomeTrackerPoll.Stop()
                #self.shutdownThread = execf.ThreadedSystemShutdown('lpt1')
                #self.shutdownThread.start()
                #self.shutdown_vars["TRACK_ENABLED"] = False
                #self.parent.stbMain.SetStatusText("Total Shutdown", 1)
                
            ## airmass threshold check 
            #if self.domeTrackingMode == 0 and self.domeTrackingEnabled:   
                #if target_airmass > 2.5 :
                    #self.shutdown_vars["SHUTDOWN_ACTIVE"] = True
                    #msg = "Telescope airmass exceeded threshold, shutdown procedure will initiate NOW!"
                    #self.writeOutput(msg, timestamp=True)
                    #self.tmrDomeTrackerPoll.Stop()
                    #self.shutdownThread = execf.ThreadedSystemShutdown('lpt1')
                    #self.shutdownThread.start()
                    #self.shutdown_vars["TRACK_ENABLED"] = False
                    #self.parent.stbMain.SetStatusText("Total Shutdown", 1)
            
            #elif self.domeTrackingMode == 1 and self.domeTrackingEnabled:
                #if target_airmass > 2.5:
                    #self.shutdown_vars["SHUTDOWN_ACTIVE"] = True
                    #msg = "Target airmass exceeded threshold, shutdown procedure will initiate NOW!"
                    #self.writeOutput(msg, timestamp=True)
                    #self.tmrDomeTrackerPoll.Stop()
                    #self.shutdownThread = execf.ThreadedSystemShutdown('lpt1')
                    #self.shutdownThread.start()
                    #self.shutdown_vars["TRACK_ENABLED"] = False
                    #self.parent.stbMain.SetStatusText("Total Shutdown", 1)
    
    def isShutdownActive(self):
        # convienence function to check is the shutdown flag
        return self.shutdown_vars["SHUTDOWN_ACTIVE"]
    
    def checkShutdownConditions(self):
        sd_ready = False
        if self.shutdownTimeCheck():
            sd_ready = True
        
        return sd_ready
    
    def shutdownTimeCheck(self):
        # shutdown times have a resulution of one minute, currentlt there is
        # no date option implimented.
        local_time = self.time_vars["CURRENT_LT"]
        hour, min = local_time[3], local_time[4]
        shutdown_hour = self.shutdown_vars["SHUTDOWN_HOUR"]
        shutdown_min = self.shutdown_vars["SHUTDOWN_MINUTE"]
        
        shutdown_active = False
        shutdow_enabled = self.shutdown_vars["SHUTDOWN_ENABLED"]
        if (hour, min) == (shutdown_hour, shutdown_min) and shutdow_enabled:
            shutdown_active = True
            
        self.shutdown_vars["SHUTDOWN_ACTIVE"] = shutdown_active
        
        return shutdown_active
    
    def airmassThresholdCheck(self):
        # check the airmass threashold depending on the tracking mode
        exceeded_threshold = True
        #if # make this editable 
        
        return False

    def getRainSensorState(self):
        # this function just reads the 'SENSOR_STATE'
        sensor_state = self.sensor_vars["SENSOR_STATE"]
        
        shutdown_active = False
        if sensor_state:
            shutdown_active = True
            
        self.shutdown_vars["SHUTDOWN_ACTIVE"] = shutdown_active
        
        return sensor_state
    
    def loadState(self, f):
        pass
    
    def saveState(self, f):
        pass
    
    def dumpVars(self):
        pass

if __name__ == "__main__":
    state = SystemStateObject()
