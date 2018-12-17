#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

# DomeTracker Process (dtproc) module deals with managing processes running within
# the program. These processes are not executed in this file but rather used to
# flag if a process is running or not. Processes can be pushed into the stack
# and executed when the time is appropriate.
#
# This module is important since processes running in dome tracker can be 
# managed in a centralized location. The eliminates the need for a bunch of 
# variables flagging if a process is running or not (or if it is clear to). It 
# also behaves as a queue for process execution. Execution is carried out by a 
# function in the main-loop somewhere, usually hooked to a timer. Simply, you 
# push your process into the stack when it's been executed. When it's done you
# pop it out of the stack.
#
# STATUS KEY:     0 = Waiting, 1 = Running
# PRIORITY KEY:   0 = Run Now, 1 = High Priority, 2 = Low Priority
#
# Some processes have rules regrading which processes can run concurrently. The 
# exclusion rules are defined by the process type.
#

import sys
import os

# Rules for various actions, these processes cannot be executed concurrently
PROCESS_RULES = {'USER_DOME_OPEN'  : ['USER_DOME_CLOSE'],
                 'USER_DOME_CLOSE' : ['USER_DOME_OPEN'],
                 'USER_DOME_CCW'   : ['USER_DOME_CW'],
                 'USER_DOME_CW'    : ['USER_DOME_CCW'],
                 'MACRO_RECORDING' : ['MACRO_RUNNING', 'DOME_TRACKING'],
                 'MACRO_RUNNING'   : ['MACRO_RECORDING', 'DOME_TRACKING'],
                 'MACRO_DOME_CCW'  : ['USER_DOME_CCW', 'USER_DOME_CW'],
                 'MACRO_DOME_CW'   : ['USER_DOME_CCW', 'USER_DOME_CW'],
                 'DOME_TRACKING'   : ['MACRO_RECORDING', 'MACRO_RUNNING'],
                 'DOME_MOTION'     : [''],
                 'SYSTEM_SHUTDOWN' : ['DOME_MOTION']
                 }

MODULE_LONG_NAME = "Process Manager"
MODULE_VERSION = "0.1.0"
MODULE_AUTHOR = "Matthew Cutone"
MODULE_COPYRIGHT = "2012"

def GetVersionStrings():
    return MODULE_LONG_NAME, MODULE_VERSION, MODULE_AUTHOR, MODULE_COPYRIGHT

class ProcessStack:
    def __init__(self, parent):
        self.parent = parent
        self._process_queue = {} # this is a dictionary, the key is the PID

    def PushProcess(self, priority=0, type=None, name='', status=0, thread=None):
        new_pid = 0
        if self._process_queue != {}:
            new_pid = max(self._process_queue.keys()) + 1
        
        self._process_queue[new_pid] = [priority, type, name, status, thread]
        
        return new_pid
    
    def PopProcess(self, pid):
        del self._process_queue[pid]
        
        return 1

    def ClearProcessQueue(self, priority=-1):
        self._process_queue = {}

    def PopProcessType(self, name):
        for pid in self._process_queue.keys():
            p_type = self._process_queue[pid][1]
            if (name == p_type):
                del self._process_queue[pid]
            else:
                continue
        
        return 1
    
    def GetProcess(self, pid):
        try:
            proc = self._process_queue[pid]
        except KeyError:
            proc = None
            
        return proc
    
    def FindProcessID(self, name=''):
        p_running = self.GetRunningProcesses()
        p_found = []
        for pid in p_running:
            p_name = self._process_queue[pid][1]
            if (p_name == name):
                 p_found.append(pid)
            else:
                continue
        
        return p_found
                
    def ProcessTypeRunning(self, type):
        running = False
        p_types = self.GetRunningProcessTypes()
        
        if type in p_types:
            running = True
            
        return running

    def ProcessReady(self, pid):
        # determine if a process is able to run
        ready = True
        c_type = self._process_queue[pid][1]
        for p_type in self.GetRunningProcessTypes():
            if p_type in PROCESS_RULES[c_type]:
                ready = False
            
        return ready

    def GetProcessStatus(self, pid):
        p_data = self._process_queue[pid]
        
        return p_data[3]
    
    def SetProcessStatus(self, pid, status=1):
        p_data = self._process_queue[pid]
        p_data[3] = status
        
        self._process_queue[pid] = p_data
        
        return status

    def GetRunningProcesses(self):
        p_run = []
        for pid in self._process_queue.keys():
            p_data = self._process_queue[pid]
            if p_data[3] == 1: # if status 'running'
                p_run.append(pid)

        return p_run
        
    def GetRunningProcessTypes(self):
        p_types = []
        for pid in self._process_queue.keys():
            p_data = self._process_queue[pid]
            if p_data[3] == 1: # if status 'running'
                p_types.append(p_data[1])

        return p_types
                
    def GetNextProcess(self):
        hp_pid, lp_pid = [], []
        for pid in self._process_queue.keys():
            p_data = self._process_queue[pid]
            if p_data[0] == 1: 
                hp_pid.append(pid)
            elif p_data[0] == 2: 
                lp_pid.append(pid)
                
        # only use low priority processes when the 
        # high priority queue is empty
        
        if (len(hp_pid) > 0):
            next_pid = min(hp_pid)
        elif ((len(lp_pid) > 0) and (len(hp_pid) == 0)):
            next_pid = min(lp_pid)
        else:
            next_pid = None # there are no processes
        
        return next_pid

# use the main() function to test the class above

def main():
    pstack = ProcessStack(None)
    print pstack.PushProcess(2, 'SYSTEM_SHUTDOWN', 'Check system time', 1, None)
    #print pstack.PushProcess(1, 'CLOSE_DOME', 'Close dome shutter', 0, None)
    #print pstack.PushProcess(2, 'CHECK_TIME', 'Check system time', 0, None)
    #print pstack.PushProcess(1, 'OPEN_DOME', 'Open dome shutter', 0, None)
    #pstack.SetProcessStatus(3, 1)
    #print pstack.PushProcess(2, 'CLOSE_DOME', 'Close dome shutter', 0, None)
    #print pstack._process_queue
    
    #print pstack.ProcessReady(pstack.GetNextProcess())
    #print pstack.GetRunningProcesses()
    print pstack.ProcessTypeRunning('SYSTEM_SHUTDOWN')
    
    return 0
    
if __name__ == "__main__":
    main()
