#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  macrof.py

TEST_MACRO_FILE = "test_macro.dtm"

def readMacro(f=TEST_MACRO_FILE):
    f_lines = open(f, 'r')
    
    macro_header = {'name' : 'test_macro', 'mode' : 1, 'exec' : None}
    macro_exec   = {}
    
    exec_n = 1
    for line in f_lines:
        line = line.rstrip('\n').split(' ')
        cmd = line[0]
        
        if cmd == "macro":
            pass
            
        elif cmd == "exec":
            args = {}
            
            n = 0
            for token in line:
                if token.startswith('\\'):
                    token = token.lstrip('\\')
                    if token in ['hour', 'minute', 'second']:
                        value = int(float(line[n + 1]))
                        args[token] = value
                    elif token in ['duration']:
                        value = float(line[n + 1])
                        args[token] = value
                    elif token == 'action':
                        args[token] = line[n + 1]
            
                n += 1
            
            macro_exec[exec_n] = args
            exec_n += 1
            
    macro_header['exec'] = macro_exec
    
    return macro_header

def saveMacro(f):
    pass

def main():
    print readMacro()['exec']
    return 0

if __name__ == '__main__':
    main()

