#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       untitled.py

import sys
import os
import string

def readObjectDataFile(file):
    f = open(file, 'r')
    lines = f.readlines()

    objectData = []
    for line in lines:
        line = line.split(';')
        # sanitize the line for white-space
        n = 0
        for i in line:
            i = string.strip(i)
            line[n] = i
            n += 1
        
        name, dec, ra, epch = line
        
        dec = dec.split(',')
        n = 0
        for i in dec:
            if i.startswith('-'):
                i = string.strip(i, '-')
                i = -1 * float(i)
            else:
                i = float(i)
            
            if n < 2:
                dec[n] = int(i)
            else:
                dec[n] = i
            
            n += 1
        
        ra = ra.split(',')
        n = 0
        for i in ra:
            if i.startswith('-'):
                i = string.strip(i, '-')
                i = -1 * float(i)
            else:
                i = float(i)
            
            if n < 2:
                ra[n] = int(i)
            else:
                ra[n] = i
            
            n += 1
        
        dec = (dec[0], dec[1], dec[2])
        ra = (ra[0], ra[1], ra[2])
        epch = float(epch)
        
        objectData.append((name, dec, ra, epch))
    
    return objectData
    
def main():
    print readObjectDataFile('objects.dat')
    return 0

if __name__ == '__main__':
    main()

