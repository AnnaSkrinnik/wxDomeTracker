from datetime import datetime

def calculateHourAngle(ra, lmst):
    rightAcc = datetime(2000, 1, 1, int(ra[0]), int(ra[1]), int(ra[2]), 0)
    lmst = datetime(2000, 1, 1, int(lmst[0]), int(lmst[1]), int(lmst[2]), 0)
 
    ha = lmst - ra
    
    return ha

ra = raw_input("right accention (hh,mm,ss): ")
lmst = raw_input("local mean siderial time (hh,mm,ss): ")

ra = ra.split(',')
lmst = lmst.split(',')

print calculateHourAngle(ra, lmst)
