#!/usr/bin/python

# linechart.py

import wx
import math
from obstools import obsmathlib
import datetime

COLOUR_TABLE = { 0 : '#FFBFBF', 1 : '#FFD280', 2 : '#FFFF80', 3 : '#FFFFBF',
                 4 : '#FFFFFF', 5 : '#BFE0FF' }

CROSS_HAIR_SIZE = 16
CROSS_HAIR_COLOUR = '#00FF00'
DEFAULT_FONT_SIZE = 10
EPOCH = 2000.0

GRADIENT_TOP = '#000000'
GRADIENT_BOTTOM = '#000030'

#1.41   M0  Red
#0.82   K0  Orange
#0.59   G0  Yellow
#0.31   F0  Yellowish
#0.00   A0  White
#-0.29  B0  Blue 

class SkyChart(wx.Panel): 
    def __init__(self, parent):
        wx.Panel.__init__(self, parent) #, style=wx.SUNKEN_BORDER)
        self.SetBackgroundColour('WHITE')
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetDoubleBuffered(True)
        self.telescopePosition = (0, 0)
        self.domePosition = 0

        self.direction = 0
        self.showgrid = True
        self.minorAxis = False
        self.drawTargetPath = False
        self.magnitudeCutOff = -5.0
        
        # map tranformation factors
        self.transformXY = (0, 0)
        self.origin = (0, 0) 
        self.zoomLevel = 1
        self.mouseMovePos = (0, 0)
        
        # dragging stuff
        #self.oldPos = (0, 0)
        #self.newPos = (0, 0)
        #self.dragging = False
        
        self.objects = None
        self.target = None
        self.names = None
        self.SetMinSize((450, 250))
        #self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))

        # TIMER OBJECTS
        self.tmrRedrawObjects = wx.Timer(self)
        self.tmrCheckMove = wx.Timer(self)
        
        self.Bind(wx.EVT_MOTION, self.OnMouseMoving)
        #self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        #self.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        self.Bind(wx.EVT_TIMER, self.ShiftImage, self.tmrCheckMove)
        self.Bind(wx.EVT_TIMER, self.Redraw, self.tmrRedrawObjects)
        
        # ENABLE GLOBAL TIMERS
        # self.tmrRedrawObjects.Start(30000)
    
    def ShiftImage(self, evt):
        w, h = self.GetSize()
        hScale = h / 90.0
        wScale = w / 360.0
        displacement = (self.newPos[0] - self.oldPos[0], self.newPos[1] - self.oldPos[1])
        
        dx = (displacement[0])
        dy = (displacement[1])
        
        #if dx > 359:
        #    dx = dx - 360
        #elif dx < 0:
        #    dx = dx + 360        

        self.transformXY = (dx, dy)
        self.oldPos = self.newPos
    
    #def OnMouseLeftDown(self, evt):
        #pos = evt.GetPositionTuple()
        #self.dragStart = pos
        #if self.dragging == False:
            #self.tmrCheckMove.Start(25)

    #def OnMouseLeftUp(self, evt):
        #self.dragging = False
        #self.tmrCheckMove.Stop()
        #pos = evt.GetPositionTuple()
     
    def SetUserNames(self, names):
        self.names = names
    
    def DrawStarPath(self, dc):
        w, h = self.GetSize()    
        hScale = h / 90.
        wScale = w / 360.
        
        if self.target:
            dc.SetPen(wx.Pen('#0ab1ff'))
            trajectoryData = []
            
            target = self.objects[self.target]
            hh, mm, ss = obsmathlib.calculateLMST()
            startTime = datetime.datetime(year=2000, month=1, day=1, hour=hh, minute=mm, second=ss)            
            resolution = datetime.timedelta(minutes=10)
            
            n = 0
            for hour in range(6 * 6):
                year = startTime.year
                month = startTime.month
                day = startTime.day
                hour = startTime.hour
                minute = startTime.minute
                second = startTime.second

                targetRA = obsmathlib.HoursToRightAscension(target[7])
                targetDec = obsmathlib.DegreesToDeclination(target[8])
                targetAlt = obsmathlib.calculateAltitude(targetRA, targetDec, (hour, minute, second))
                targetAzmth = obsmathlib.calculateAzimuth(targetRA, targetDec, targetAlt, (hour, minute, second))
                
                AZMTH, ALT = self.TransformAltAzmthCoordinate(targetAzmth, targetAlt, wScale, hScale)

                #if (n % 6) == 0 and n != 0:
                #    dc.SetBrush(wx.Brush('#0ab1ff', wx.TRANSPARENT))
                #    dc.DrawCircle(AZMTH, ALT, 3)                    
                #    timeString = '%02d' % hour + ':' + '%02d' % minute + ':' + '%02d' % second
                #    textExt = dc.GetTextExtent(timeString)
                    
                #    if textExt[0] + AZMTH > w:    
                #        dc.DrawText(timeString, (AZMTH - textExt[0]) - 2, ALT - 2)
                #    else:
                #        dc.DrawText(timeString, AZMTH + 2, ALT - 2)
                        
                #n += 1
                
                trajectoryData.append((AZMTH, ALT))
                startTime = startTime + resolution

            dc.SetBrush(wx.Brush('#0ab1ff', wx.TRANSPARENT))
            dc.DrawCircle(AZMTH, ALT, 3)                    
            timeString = '%02d' % hour + ':' + '%02d' % minute + ':' + '%02d' % second
            textExt = dc.GetTextExtent(timeString)
            
            if textExt[0] + AZMTH > w:    
                dc.DrawText(timeString, (AZMTH - textExt[0]) - 2, ALT - 2)
            else:
                dc.DrawText(timeString, AZMTH + 2, ALT - 2)
                            
            dc.DrawSpline(trajectoryData)
    
    def OnMouseMoving(self, evt):
        w, h = self.GetSize()
        hScale = h / 90.0
        wScale = w / 360.0
        
        pos = evt.GetPositionTuple()
        self.mouseMovePos = (pos[0]/wScale, 90 - pos[1]/hScale)
            
        #if evt.LeftIsDown() and evt.Dragging():
            #self.dragging = True
            #pos = evt.GetPositionTuple()
            #self.newPos = pos
            #self.Redraw()
    
    def SetTelescopePosition(self, data, LMST):
        telRA, telDec = data
        telAlt = obsmathlib.calculateAltitude(telRA, telDec, LMST)
        telAz = obsmathlib.calculateAzimuth(telRA, telDec, telAlt, LMST)
        self.telescopePosition = (telAz, telAlt)
    
    def SetTarget(self, targetID):
        self.target = targetID
    
    def SetObjects(self, data):
        self.objects = data
        
    def TransformAltAzmthCoordinate(self, azmth, alt, xscale, yscale):
        direction = { 0 : 0, 1 : 90, 2 : 180, 3 : -90 }
        azmth = azmth + direction[self.direction]
        
        #azmth = azmth + self.transformXY[0]
        
        if azmth > 360:
            azmth = azmth - 360
        elif azmth < 0:
            azmth = azmth + 360
        
        azmth = (azmth * xscale) * self.zoomLevel
        alt = (alt * yscale) * self.zoomLevel
        
        return (azmth, alt)
        
    def ZoomIn(self):
        if self.zoomLevel < 5:
            self.zoomLevel += 1

    def ZoomOut(self):
        if self.zoomLevel > 0:
            self.zoomLevel -= 1
    
    def RotateCCW(self):
        newDir = self.direction - 1
        
        if newDir < 0:
            self.direction = 3
        else:
            self.direction -= 1
    
        self.Refresh()

    def RotateCW(self):
        newDir = self.direction + 1
        
        if newDir > 3:
            self.direction = 0
        else:
            self.direction += 1
        
        self.Refresh()
    
    def SetData(self, data):
        self.objects = data
        self.Refresh()

    def OnPaint(self, event):
        w, h = self.GetSize()
        hScale = h / 195.
        wScale = h / 195.
        dc = wx.PaintDC(self)
        dc.SetDeviceOrigin((w / 2.0), (h / 2.0))
        dc.SetAxisOrientation(True, True)
        dc.SetPen(wx.Pen('WHITE'))
        #dc.SetUserScale(3.3, 3.3)
        #dc.DrawRectangle(0, 0, w, h)
        #dc.GradientFillLinear((0, 0, w, h), GRADIENT_BOTTOM, GRADIENT_TOP, wx.SOUTH)
        #if self.showgrid:
        #    self.DrawGrid(dc)
        #    self.DrawAxis(dc)
        #self.DrawTitle(dc)
        #if self.target:
        #   pass
            #self.DrawStarPath(dc)
        #self.DrawData()
        
        dc.SetBrush(wx.Brush('BLACK', wx.TRANSPARENT))
        dc.SetPen(wx.Pen('BLACK'))
        
        dc.DrawCircle(0, 0, 90*hScale)
        dc.DrawCircle(0, 0, 60*hScale)
        dc.DrawCircle(0, 0, 30*hScale)
        dc.DrawLine(-92*hScale,0,92*hScale,0)
        dc.DrawLine(0,-92*hScale,0,92*hScale)

        font =  dc.GetFont()
        font.SetPointSize(DEFAULT_FONT_SIZE)
        dc.SetTextForeground('BLACK')
        dc.SetFont(font)
        
        dc.DrawText(str(60), 30*hScale, 0)
        dc.DrawText(str(30), 60*hScale, 0)
        dc.DrawText(str(0), 90*hScale, 0)
    
    def PolarToRectCoord(self, r, t):
        x = r * math.cos(t)
        y = r * math.sin(t)
        
        return x, y
        
    def OnSize(self, event):
        self.Refresh()
         
    def DrawAxis(self, dc):
        w, h = self.GetSize()
        dc.SetPen(wx.Pen('#0080FF'))
        
        font =  dc.GetFont()
        font.SetPointSize(DEFAULT_FONT_SIZE)
        dc.SetTextForeground('#0065C8')
        dc.SetFont(font)
        
        axisAzExt = dc.GetTextExtent("AZIMUTH")
        axisAlExt = dc.GetTextExtent("ALTITUDE")
        axisAzTick = dc.GetTextExtent("000")
        axisAlTick = dc.GetTextExtent("00")
                
        dc.DrawText("AZIMUTH", (w / 2.0) - (axisAzExt[0] / 2.0), axisAzTick[1] + axisAzExt[1])
        dc.DrawRotatedText("ALTITUDE", axisAlTick[0] + axisAlExt[1], (h / 2.0) + (axisAlExt[0] / 2.0), 270)
        
        font =  dc.GetFont()
        font.SetPointSize(DEFAULT_FONT_SIZE)
        dc.SetTextForeground('#0080FF')
        dc.SetFont(font)

        hScale = h / 90.
        wScale = w / 360.
        
        shift = { 0 : 0, 1 : 270, 2 : 180, 3 : 90 }
        
        for i in range(10, 100, 10):
            dc.DrawText(str(i), 1, (i*hScale)-1)
        
        for i in range(20, 360, 20):
            deltaX = i + shift[self.direction]
            if deltaX > 359:
                deltaX = deltaX - 360
            
            if deltaX < 0:
                deltaX = deltaX + 360
            
            dc.DrawText(str(deltaX), (i*wScale) + 1, axisAzTick[1])
                        
    def DrawDomeBrackets(self, dc):
        w, h = self.GetSize()
        direction = { 0 : 0, 1 : 90, 2 : 180, 3 : -90 }
        
        hScale = h / 90.
        wScale = w / 360.
        
        dc.SetPen(wx.Pen('#00FF00'))
        
        upperBound = 60
        lowerBound = 15

        domeAzmth = self.domePosition + direction[self.direction]
        
        if domeAzmth > 359:
            domeAzmth = domeAzmth - 360
        
        if domeAzmth < 0:
            domeAzmth = domeAzmth + 360
        
        # top dome indicator
        dc.DrawLine((domeAzmth * wScale) - CROSS_HAIR_SIZE, upperBound*hScale, (domeAzmth * wScale) + CROSS_HAIR_SIZE, upperBound*hScale)
        dc.DrawLine((domeAzmth * wScale), upperBound*hScale - 32, (domeAzmth * wScale), upperBound*hScale) 
        
        # bottom dome indicator
        dc.DrawLine((domeAzmth * wScale) - CROSS_HAIR_SIZE, lowerBound*hScale, (domeAzmth * wScale) + CROSS_HAIR_SIZE, lowerBound*hScale)
        dc.DrawLine((domeAzmth * wScale), lowerBound*hScale + 32, (domeAzmth * wScale), lowerBound*hScale)

    def DrawGrid(self, dc):
        w, h = self.GetSize()        
        hScale = h / 90.0
        wScale = w / 360.0

        # minor grid lines
        if self.minorAxis:
            dc.SetPen(wx.Pen('#000060', 1, wx.DOT))
            for i in range(1, 90, 1):
                if (i % 10) != 0:
                    dc.DrawLine(0, i*hScale, w, i*hScale)

            for i in range(2, 360, 2):
                if (i % 20) != 0:
                    dc.DrawLine(i*wScale, 0, i*wScale, h)
        
        dc.SetPen(wx.Pen('#0000b0', 1, wx.DOT))
        # major grid lines
        for i in range(10, 90, 10):
            dc.DrawLine(0, i*hScale, w, i*hScale)

        for i in range(20, 360, 20):
            dc.DrawLine(i*wScale, 0, i*wScale, h)
                
    def DrawData(self):
        w, h = self.GetSize()
        
        dc = wx.PaintDC(self)
        #dc.SetDeviceOrigin(0, h)
        originX = self.transformXY[0]
        self.origin = (self.origin[0] - originX, h)
        dc.SetDeviceOrigin(self.origin[0], h)
        dc.SetAxisOrientation(True, True)

        hScale = h / 90.
        wScale = w / 360.
        
        direction = { 0 : 0, 1 : 90, 2 : 180, 3 : -90 }
        tx, ty = self.telescopePosition
        
        if self.objects != None:
            for key in self.objects.keys():
                i = self.objects[key]
                name = str(i[self.names[key]])
                
                if self.names[key] == 0: # starID
                    name = "HYG " + name
                elif self.names[key] == 1: # HIP
                    name = "HIP " + name
                elif self.names[key] == 2: # HD
                    name = "HD " + name
                elif self.names[key] == 3: # Gliese
                    name = "Gliese " + name
                elif self.names[key] == 4: # Proper
                    pass                
                
                RA = obsmathlib.HoursToRightAscension(float(i[7]))
                DEC = obsmathlib.DegreesToDeclination(float(i[8]))
                epoch = EPOCH
                colourIdx = i[16]
                
                LMST = obsmathlib.calculateLMST()
                RA, DEC, UE = obsmathlib.epochConvert(RA, DEC, 2000.0)
                ALT = obsmathlib.calculateAltitude(RA, DEC, LMST)
                AZMTH = obsmathlib.calculateAzimuth(RA, DEC, ALT, LMST)
                
                AZMTH, ALT = self.TransformAltAzmthCoordinate(AZMTH, ALT, wScale, hScale)

                if colourIdx >= 1.41:
                    colour = COLOUR_TABLE[0]
                elif colourIdx < 1.41 and colourIdx >= 0.82:
                    colour = COLOUR_TABLE[1]
                elif colourIdx < 0.82 and colourIdx >= 0.59:
                    colour = COLOUR_TABLE[2]
                elif colourIdx < 0.59 and colourIdx >= 0.31:
                    colour = COLOUR_TABLE[3]
                elif colourIdx < 0.31 and colourIdx >= 0.0:
                    colour = COLOUR_TABLE[4]
                elif colourIdx < 0.0 and colourIdx >= -0.29:
                    colour = COLOUR_TABLE[5]
                elif colourIdx < -0.29:
                    colour = COLOUR_TABLE[6]
                
                dc.SetBrush(wx.Brush(colour))
                dc.SetPen(wx.Pen(colour))
                dc.DrawCircle(AZMTH, ALT, 2)

                mouseX, mouseY = self.mouseMovePos
                mouseY = h - mouseY
                                
                #if self.target == key:
                    ## Draw Bounding Box
                    #BB_SCALE = 2
                    
                    #dc.SetPen(wx.Pen('#00FF00'))
                    #dc.DrawLines(((5 + AZMTH, 10 + ALT), (10 + AZMTH, 10 + ALT), (10 + AZMTH, 5 + ALT)))
                    #dc.DrawLines(((10 + AZMTH, -5 + ALT), (10 + AZMTH, -10 + ALT), (5 + AZMTH, -10 + ALT)))    
                    #dc.DrawLines(((-5 + AZMTH, -10 + ALT), (-10 + AZMTH, -10 + ALT), (-10 + AZMTH, -5 + ALT)))    
                    #dc.DrawLines(((-10 + AZMTH, 5 + ALT), (-10 + AZMTH, 10 + ALT), (-5 + AZMTH, 10 + ALT)))
                    
                    #font = dc.GetFont()
                    #font.SetFamily(wx.FONTFAMILY_MODERN)
                    #font.SetPointSize(DEFAULT_FONT_SIZE)
                    #dc.SetFont(font)
                    ##dc.SetTextForeground('#000000')
                    ##dc.DrawText("Target: " + name, AZMTH + 13, ALT - 11)
                    #dc.SetTextForeground('#00FF00')
                    #textExt = dc.GetTextExtent(name)
                    
                    #if textExt[0] + AZMTH > w:    
                        #dc.DrawText(name, (AZMTH - textExt[0]) - 12, ALT - 10)
                    #else:
                        #dc.DrawText(name, AZMTH + 12, ALT - 10)
                    
                #else:
                    ##distToMouse = math.sqrt((AZMTH - mouseX) ** 2 + (ALT - mouseY) ** 2)
                    ##if distToMouse < 15:
                font = dc.GetFont()
                font.SetFamily(wx.FONTFAMILY_MODERN)
                font.SetPointSize(DEFAULT_FONT_SIZE)
                dc.SetFont(font)
                    #dc.SetTextForeground('#000000')
                    #dc.DrawText(name, AZMTH + 6, ALT - 1)
                dc.SetTextForeground('#ffffff')
                textExt = dc.GetTextExtent(name)
                
                if textExt[0] + AZMTH + 5 > w:    
                    dc.DrawText(name, (AZMTH - textExt[0]) - 5, ALT)
                else:
                    dc.DrawText(name, AZMTH + 5, ALT)
        
        dc.SetBrush(wx.Brush('#00FF00', wx.TRANSPARENT))
        dc.SetPen(wx.Pen(CROSS_HAIR_COLOUR))
        
        telPositionAzmth = self.telescopePosition[0] + direction[self.direction]
        
        if telPositionAzmth > 359:
            telPositionAzmth = telPositionAzmth - 360
        
        if telPositionAzmth < 0:
            telPositionAzmth = telPositionAzmth + 360
        
        #dc.SetLogicalFunction(wx.XOR)
        dc.DrawLine((telPositionAzmth * wScale) - CROSS_HAIR_SIZE, self.telescopePosition[1]*hScale, 
            (telPositionAzmth * wScale) + CROSS_HAIR_SIZE, self.telescopePosition[1]*hScale)
        dc.DrawLine((telPositionAzmth * wScale), self.telescopePosition[1]*hScale - CROSS_HAIR_SIZE, 
            (telPositionAzmth * wScale), self.telescopePosition[1]*hScale + CROSS_HAIR_SIZE)
        
    def Redraw(self):
        self.Refresh()
        
    def ReadObjectDatabaseFile(self, f):
        file = open(f, 'r')
        lines = file.readlines()
        # StarID,Hip,HD,HR,Gliese,BayerFlamsteed,ProperName,RA,Dec,Distance,Mag,AbsMag,Spectrum,ColorIndex
        objectDictionary = {}
        
        for line in lines:
            line = line.rstrip('\n')
            if not line.startswith('#'):
                if len(line) != 0:
                    line = line.split(',')
                    
                    HYG_ID = int(line[0])
                    
                    if line[1] != '':
                        CatHip = int(line[1])
                    else:
                        CatHip = None
                    if line[2] != '':
                        CatHD = int(line[2])
                    else:
                        CatHD = None 
                                                
                    properName = line[6]
                    RA = obsmathlib.HoursToRightAscension(float(line[7]))
                    DEC = obsmathlib.DegreesToDeclination(float(line[8]))
                    dist = float(line[9])
                    mag = float(line[13])
                    absMag = float(line[14])
                    spectrum = line[14]
                    colourIdx = line[16]
                    epoch = 2000.0
                    
                    if colourIdx != '':
                        colourIdx = float(line[16])
                    else:
                        colourIdx = 0.0
                    
                    objectDictionary[HYG_ID] = (CatHip, CatHD, 
                        properName, RA, DEC, dist, mag, absMag, spectrum, 
                        colourIdx, epoch)
        
        return objectDictionary
            
class LineChartExample(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(600, 400))

        panel = wx.Panel(self, -1)
        panel.SetBackgroundColour('BLACK')

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.linechart = SkyChart(panel)
        hbox.Add(self.linechart, 1, wx.EXPAND | wx.ALL, 0)
        panel.SetSizer(hbox)

        self.Centre()
        self.Show(True)

def main():
    app = wx.App()
    LineChartExample(None, -1, 'Sky Chart')
    app.MainLoop()

if __name__ == "__main__":
    main()
