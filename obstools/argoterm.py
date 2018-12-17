import serial
import os
import sys
import string
import time

class ArgoInterface:
    def __init__(self, port=0, baudrate=38400, timeout=10, echo=False):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        
        self.serial = serial.Serial(0, baudrate=38400, timeout=5)
    
    def echoCommand(self, command):
        self.serial.write(command)
        self.serial.write('\n')
        data = ""
        
        # loop for reading all the bytes in the buffer
        reading = True
        use = False
        while reading:
            recv = self.serial.read(1)
            if recv == '\n': use = True
            if recv != '%':
                if use:
                    data = data + str(recv)
            else:
                reading = False
        
        data = string.strip(data, '\n')
        self.serial.flush()
        
        return data
    
    def getRAD(self, mode=0):
        modes = {0 : 'rad -d', 1 : 'rad -r', 2 : 'rad -s'}
        try:
            rad = self.echoCommand(modes[mode])
            
            if mode == 2:
                ra, dec = rad.split(' ')
                
                dec = dec.split(':')
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
                
                ra = ra.split(':')
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
                
                ra = (ra[0], ra[1], ra[2])
                dec = (dec[0], dec[1], dec[2])
            
            return (ra, dec)
            
        except:
            
            return ((0,0,0), (0,0,0))

    def getDateTime(self, type=0):
        # 0 - local
        # 1 - UTC
        
        if type == 0:
            command = 'date -l'
        elif type == 1:
            command = 'date -u'
        
        dateTime = self.echoCommand(command)
        
        return dateTime

    def getJulianDate(self):
        jd = self.echoCommand('date -j')
        return jd
    
    def closeConnection(self):
        self.serial.close()
        
        return 1

    def openConnection(self):
        self.serial.open()
        
        return 1
                
def main():
    argo = ArgoInterface(0)
    while 1:
        time.sleep(1.5)
        print argo.getRAD(2)
        #print argo.getDateTime(1)

    argo.closeConnection()
    
if __name__ == "__main__":
    main()
