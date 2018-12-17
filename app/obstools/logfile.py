import string
from time import strftime
import os
import sys

class LoggingSystem:
    def __init__(self, path='log.txt'):
        self.path = path
        f = open(self.path)
        f.close()
    
    def getTimeStamp(self):
        return strftime("[%Y-%m-%d %H:%M:%S]: ")
    
    def writeToFile(self, text, ts=True):
        f = open(self.path, 'a')
        if ts:
            line = self.getTimeStamp() + str(text)
        else:
            line = str(text)
        f.write(line)
        f.close()
        
def main():
    log = LoggingSystem('log.txt')
    log.writeToFile('this is a log\n')
    log.writeToFile('this is a log 2\n')
    pass

if __name__ == '__main__':
    main()
