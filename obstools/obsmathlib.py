#      obsmathlib.py
#      
#      Copyright 2011 Matthew Cutone matthew.cutone@gmail.com
#      
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#      
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#      
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#      MA 02110-1301, USA.

from math import sin, cos, tan, pi, asin, acos, sqrt, atan
import time
import datetime

LATITUDE = 43.775
LONGITUDE = -79.5

def HoursToRightAscension(Hours):
    # convert RA in decimal hours to hh:mm:ss
    RAinHours = Hours
    
    hhRA = int(RAinHours)
    mmRA = int((RAinHours-hhRA) * 60)
    ssRA = (((RAinHours-hhRA) * 60) - (int((RAinHours - hhRA) * 60))) * 60
    
    RightAscension = (hhRA, mmRA, ssRA)
    
    return RightAscension

def DegreesToRightAscension(degrees):
    # convert RA in degrees to hh:mm:ss
    RAinHours = degrees / 15.0
    
    hhRA = int(RAinHours)
    mmRA = int((RAinHours-hhRA) * 60)
    ssRA = (((RAinHours-hhRA) * 60) - (int((RAinHours - hhRA) * 60))) * 60
    
    RightAscension = (hhRA, mmRA, ssRA)
    
    return RightAscension

def DegreesToDeclination(degrees):
    # convert declination in degrees to deg, min, sec
    ddDEC = int(degrees)
    mmDEC = int((degrees - ddDEC) * 60)
    ssDEC = (((degrees - ddDEC) * 60) - (int((degrees - ddDEC) * 60))) * 60
    Declination = (ddDEC, mmDEC, ssDEC)
    
    return Declination

def RightAscensionToDegrees(hours, minutes, seconds):
    # convert RA in hour, min, sec to degrees
    RightAscensionDegrees = (hours + ((minutes * 60) + seconds) / 3600.0) * 15.0
    
    return RightAscensionDegrees

def RightAscensionToHours(hours, minutes, seconds):
    # convert RA in degrees to hours
    RightAscensionDegrees = (hours + ((minutes * 60) + seconds) / 3600.0)
    
    return RightAscensionDegrees

def DeclinationToDegrees(degrees, minutes, seconds):
    # convert declination in degrees to degrees
    DeclinationDegrees = degrees + ((minutes * 60) + seconds) / 3600.0
    
    return DeclinationDegrees

def degToRad(deg):
    # Conversion function for degrees to radians
    rad = deg * (pi / 180.0)
    
    return rad

def radToDeg(rad):
    # Conversion function for radians to degrees
    deg = rad * (180.0 / pi)
    
    return deg

def calculateHourAngle(RA, currentLMST):
    # The calculateHourAngle() function returns the value of the current   
    # Hour Angle, based on the current Local Mean Sidereal Time and the 
    # Right Ascension of the object being observed.                    
    # The function simply reads out the hh/mm/ss for both and converts   
    # to an hour only unit of time.  HA=LMST-RA is calcuated, and the     
    # Hour angle is returned to where it was called from.                 
    
    LMST = currentLMST
    RAinHours = RA[0] + ((RA[1] * 60.) + RA[2]) / 3600.
    LMSTinHours = LMST[0] + ((LMST[1] * 60.) + LMST[2]) / 3600.
    HA = LMSTinHours - RAinHours
    
    return HA

def calculateAirmass(currentRA, currentDEC, currentLMST):
    # As a rule, observations should not be done when looking through     
    # an airmass that is >2.  This makes the observations rather           
    # crappy, images are use    less.  This function returns the airmass       
    # given the altitude of the object, so that a tolerance can be set. 
    # The program will exit if the object is at an airmass of >2           

    altitude = calculateAltitude(currentRA, currentDEC, currentLMST)
    airmass = 1. / (cos(degToRad(90.0 - altitude)))
    
    #airmass=Math.acos((90.0-altitude)*DEG_TO_RAD)*   //complex formula
    #     (1.-0.0012*(Math.pow(Math.acos((90.0-altitude)*DEG_TO_RAD),2)-1))
    
    return airmass

def calculateAltitude(currentRA, currentDEC, currentLMST): 
    HA = calculateHourAngle(currentRA, currentLMST)
    
    if HA < -12: HA = HA + 24
    if HA >= 12: HA = HA - 24
    
    HA = HA * 15.0 #this changes HA from HOURS into DEGREES
    DECinDEG = currentDEC[0] + ((currentDEC[1] * 60) + currentDEC[2]) / 3600.

    sin_alt = sin(degToRad(LATITUDE)) * sin(degToRad(DECinDEG)) \
        + cos(degToRad(LATITUDE)) * cos(degToRad(DECinDEG)) * cos(degToRad(HA))
    altitude = radToDeg(asin(sin_alt))
    
    return altitude

def calculateAzimuth(currentRA, currentDEC, altitude, LMST):
    # Compute the azimuth given declination, right ascension, altitude and LMST. 
    LMSTinHOURS = LMST[0] + ((LMST[1] * 60) + LMST[2]) / 3600. #LMST in hours
    RA = currentRA[0] + ((currentRA[1] * 60) + currentRA[2]) / 3600. #RA in hours

    HA = LMSTinHOURS - RA
    if HA < -12: 
        HA = HA + 24
    if HA >= 12: 
        HA = HA - 24
    
    HA = HA * 15.0   # //HA in degrees
    DEC = currentDEC[0] + ((currentDEC[1] * 60) + currentDEC[2]) / 3600. #DEC in degrees
    altitude = degToRad(altitude)
    #altitude = degToRad(calculateAltitude(currentDEC, currentRA, LMST))
    
    cos_az = (sin(degToRad(DEC)) - (sin(altitude) * sin(degToRad(LATITUDE)))) / (cos(altitude) * cos(degToRad(LATITUDE)))
    azimuth = radToDeg(acos(cos_az))
    
    if sin(degToRad(HA)) < 0: 
        azimuth = azimuth + 0
    else: 
        azimuth = 360 - azimuth
    
    return azimuth

def checkCoords(RA, DEC):
    # The checkCoords() function returns a boolean variable.  It's purpose 
    # is to check and see if the coordinates that will be used in the     
    # program are real corrdinates.  i.e. RA<0 is impossible               
    # It validates the values of RA and DEC, and returns a boolean 'true'  
    # or 'false' accordingly                                               
    
    hhRA, mmRA, ssRA = RA
    ddDEC, mmDEC, ssDEC = DEC
    valid = 0
    if(hhRA >= 0) and (hhRA <= 23) and (ddDEC >= -90) and (ddDEC <= 90):
        if(mmRA >= 0) and (mmRA <= 59) and (mmDEC >= 0) and (mmDEC <= 59):
            if(ssRA >= 0) and (ssRA <= 59) and (ssDEC >= 0) and (ssDEC <= 59):
                valid = 1
                
    return valid

def epochConvert(currentRA, currentDEC, userEpoch):
    # The program stars are all hardwired into the program.  The coordinates   
    # are of the J2000.0 epoch (see program summary for list of program stars 
    # and their coordinates).  The epochConvert() routine uses the J2000.0   
    # coordinates and the current year to calculate the current epoch's    
    # coordinates.  This is a useful routine to keep the program independent  
    # from user input.                                                      
    #                                                                        
    # The formulae used for this routine were taken from:                    
    # "Observational Astronomy: 2nd Edition" by Birney, Gonzalez, and Oesper 
    # published: Cambridge University Press, 2006, pg 67
    
    year = time.localtime()[0]
    month = time.localtime()[1]
    
    interval = year - userEpoch
    
    if month > 6: 
        interval = interval + 0.5
    
    m = 46.1244 + (0.000279 * interval)
    n = 20.0431 - (0.000085 * interval)

    RAinDEG = (currentRA[0] + ((currentRA[1] * 60) + currentRA[2]) / 3600.) * 15. #RA in degrees
    DECinDEG = currentDEC[0] + ((currentDEC[1] * 60) + currentDEC[2]) / 3600. #DEC in degrees

    deltaA = (m + n * sin(degToRad(RAinDEG)) * tan(degToRad(DECinDEG)))
    deltaD = n * cos(degToRad(RAinDEG))

    RAinHOURS = (RAinDEG + (interval * deltaA) / 3600.) / 15.
    DECinDEG = DECinDEG + (interval * deltaD) / 3600.

    #NEW RA - i.e. converted to userEpoch   
    hhRA = int(RAinHOURS)
    mmRA = int((RAinHOURS - hhRA) * 60)
    ssRA = (((RAinHOURS - hhRA) * 60) - (int((RAinHOURS - hhRA) * 60))) * 60
    RAreturn = (hhRA, mmRA, ssRA)

    #NEW DEC - i.e. converted to userEpoch
    ddDEC = int(DECinDEG)
    mmDEC = int((DECinDEG - ddDEC) * 60)
    ssDEC = (((DECinDEG - ddDEC) * 60) - (int((DECinDEG - ddDEC) * 60))) * 60
    DECreturn = (ddDEC, mmDEC, ssDEC)
    
    return RAreturn, DECreturn, (userEpoch + interval)

def convertDateTimeJD(date, time):
    year, month, day = date
    hour, minute, second = time
    
    a = (14 - month) / 12.0
    y = (year + 4800) - a
    m = (month + (12 * a)) - 3

    JDN = day + (((153 * m) + 2) / 5.0) + (365 * y) + (y / 4.0) - (y / 100.0) + (y / 400.0) - 32045
    JD = JDN + ((hour - 12) / 24.0) + (minute / 1440.0) + (second / 86400.0)
    
    return JD

def calculateLMST():
    # Calculates Local Mean Siderial Time, accurate in comparison to the old
    # YorkTime program.
    
    G = {2010 : 6.63681, 
         2011 : 6.62089, 
         2012 : 6.60497, 
         2013 : 6.65478, 
         2014 : 6.63886}
    
    #STEPS TO LMST FROM: Observational Astronomy author, D.scott Birney, ed. 2, pg#26
    #step1 //current GMT/UT
    currentTime = time.gmtime()
    
    year = currentTime[0]
    month = currentTime[1]
    day = currentTime[2]
    hour = currentTime[3]
    min = currentTime[4]
    sec = currentTime[5]
    N = currentTime[7]

    #step2 - convert solar interval since 0h UT to sidereal interval
    interval = (hour + (min / 60.) + (sec / 3600.)) #* 1.00273791 <-- what is this, works better without
    
    #step3 - calculate GMST at time of interest
    GMST = 6.60497 + (0.0657098244 * N) + (1.00273791 * interval)
    # removed G constant 

    # calculate Julian Day number at 0h UT
    L = (year - 2001) / 4
    JDnot = 2451544.5 + 365 * (year - 2000) + N + L
    
    # calculate exact Julian Day i.e. including interval since 0h
    JD = JDnot + (interval / 24)
    
    #step4 - account for longitude
    if GMST > 24: 
        GMST = GMST - 24
        
    ST = GMST + (LONGITUDE / 15.)
    
    if ST > 24: 
        ST = ST - 24
    elif ST < 0: 
        ST = ST + 24

    hour = int(ST)
    min = int(((ST - hour) * 60))
    sec = int((((ST - hour) * 60 - min) * 60))
    LMST = (hour, min, sec)
    
    return LMST

def main():
    
    X, Y, Z = HeliocentricEquatorialCoordinates('Saturn')
    xe, ye, ze = HeliocentricEquatorialCoordinates('Earth')
        
    xp = X + xe
    yp = Y + ye
    zp = Z + ze
    
    RA = atan((yp / xp))
    DEC = atan(zp / sqrt(xp**2 + yp**2))
    
    print RA, DEC
    
    return 0

if __name__ == "__main__":
    main()
