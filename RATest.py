#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  RATest.py
#  
#  Copyright 2014 Observatory <Observatory@MCCALL-PC>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import serial
import time
import io

CR_CHAR = chr(13)
CRLF_CHAR = chr(13)+chr(10)

def ReadSCL(ser):
    while True:

        c = ser.read(ser.inWaiting())
        
        if len(c) > 0:
            break
        else:
            time.sleep(0.05)

    return c

def main():
    s = serial.Serial('COM1', 
        baudrate=9600, 
        timeout=1,
        parity=serial.PARITY_NONE,
        bytesize=serial.EIGHTBITS,
        stopbits=serial.STOPBITS_ONE,
        xonxoff=1)
    
    cmd = "RS"
    
    time.sleep(0.1)
    s.write("QT{cr}HR{cr}{cmd}{crlf}".format(cmd=cmd, cr=CR_CHAR, crlf=CRLF_CHAR))
    time.sleep(0.1)
    
    
    #s.flush()
    time.sleep(0.05)
    #print s.readline()
    print ReadSCL(s)
    
    s.close()

if __name__ == '__main__':
    main()

