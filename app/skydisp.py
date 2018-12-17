#!/usr/bin/python

# linechart.py

import wx
import math
import datetime

COLOUR_TABLE = { 0 : '#FFBFBF', 1 : '#FFD280', 2 : '#FFFF80', 3 : '#FFFFBF',
                 4 : '#FFFFFF', 5 : '#BFE0FF' }
                 
OBJECT_TEST_LIST = {1000: ('Betelguese', 180.0, 45.0, 4), 1001: ('Rigel', 230.0, 60.0, 3)}

CROSS_HAIR_SIZE = 16
CROSS_HAIR_COLOUR = '#00FF00'
DEFAULT_FONT_SIZE = 10
EPOCH = 2000.0

GRADIENT_TOP = '#000000'
#GRADIENT_BOTTOM = '#000000'
GRADIENT_BOTTOM = '#000042'

#1.41   M0  Red
#0.82   K0  Orange
#0.59   G0  Yellow
#0.31   F0  Yellowish
#0.00   A0  White
#-0.29  B0  Blue 

class SkyChart(wx.Panel): 
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.SUNKEN_BORDER)
        self.SetBackgroundColour('BLACK')
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetDoubleBuffered(True)
        
        self.showgrid = True
        self.minorAxis = False
        self.drawTargetPath = False
        self.mouseMovePos = (0,0)
        self.telescopePosition = (234, 50)
        
        self.bright_stars_visible = False
                
        self.objects = OBJECT_TEST_LIST
        self.target = 1000
        self.names = None
        self.nearest_object = None
        self.SetSize((450, 250))
        self.SetMinSize((450, 250))
        #self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))

        # TIMER OBJECTS
        self.tmrRedrawObjects = wx.Timer(self)
        self.tmrCheckMove = wx.Timer(self)
        
        self.Bind(wx.EVT_MOTION, self.OnMouseMoving)
        self.Bind(wx.EVT_TIMER, self.Redraw, self.tmrRedrawObjects)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        
        # ENABLE GLOBAL TIME
        self.tmrRedrawObjects.Start(150)
        
    #def OnMouseLeftDown(self, evt):
        #pos = evt.GetPositionTuple()
        #self.dragStart = pos
        #if self.dragging == False:
            #self.tmrCheckMove.Start(25)

    def OnMouseLeftUp(self, evt):
        if self.nearest_object:
            self.target = self.nearest_object
        
    def OnMouseMoving(self, evt):
        w, h = self.GetSize()
        hScale = h / 90.0
        wScale = w / 360.0
        
        pos = evt.GetPositionTuple()
        self.mouseMovePos = (pos[0], pos[1])
            
    def SetTarget(self, targetID):
        self.target = targetID
    
    def SetObjects(self, data):
        self.objects = data
    
    def SetTelescopePosition(self, azmth, alt):
        self.telescopePosition = (azmth, alt)
                    
    def SetData(self, data):
        self.objects = data
        self.Refresh()

    def OnPaint(self, event):
        w, h = self.GetSize()
        dc = wx.PaintDC(self)
        dc.SetDeviceOrigin(0, h)
        dc.SetAxisOrientation(True, True)
        dc.SetPen(wx.Pen('BLACK'))
        #dc.SetUserScale(3.3, 3.3)
        #dc.DrawRectangle(0, 0, w, h)
        dc.GradientFillLinear((0, 0, w, h), GRADIENT_BOTTOM, GRADIENT_TOP, wx.SOUTH)
        if self.showgrid:
            self.DrawGrid(dc)
            self.DrawAxis(dc)
        #if self.target:
        #   pass
            #self.DrawStarPath(dc)
        #self.DrawDomeBrackets(dc)
        self.DrawData(dc)
        
    def OnSize(self, event):
        self.Refresh()
         
    def DrawAxis(self, dc):
        w, h = self.GetSize()
        dc.SetPen(wx.Pen('#0080FF'))
        
        font =  dc.GetFont()
        font.SetPointSize(DEFAULT_FONT_SIZE)
        #dc.SetTextForeground('#0065C8')
        dc.SetTextForeground('#999999')
        dc.SetFont(font)
        
        axisAzExt = dc.GetTextExtent("AZIMUTH")
        axisAlExt = dc.GetTextExtent("ALTITUDE")
        axisAzTick = dc.GetTextExtent("000")
        axisAlTick = dc.GetTextExtent("00")
                
        dc.DrawText("AZIMUTH", (w / 2.0) - (axisAzExt[0] / 2.0), axisAzTick[1] + axisAzExt[1] + 6)
        dc.DrawRotatedText("ALTITUDE", axisAlExt[1], (h / 2.0) - (axisAlExt[1] * 2.0), 270)
        
        font =  dc.GetFont()
        font.SetPointSize(DEFAULT_FONT_SIZE)
        dc.SetTextForeground('#FFFFFF')
        dc.SetFont(font)

        hScale = h / 90.
        wScale = w / 360.
        
        shift = { 0 : 0, 1 : 270, 2 : 180, 3 : 90 }
        
        for i in range(10, 100, 10):
            dc.DrawText(str(i), 1, (i*hScale) - 1)
        
        for i in range(0, 360, 20):
            dc.DrawText(str(i), (i*wScale) + 2, axisAzTick[0])
                    
        #points = {0 : ["E", "S", "W"], 
            #1 : ["N", "E", "S"],
            #2 : ["W", "N", "E"],
            #3 : ["S", "W", "N"]}
            
        ## draw cardinal points
        
        #dirLabels = points[self.direction]

        #font =  dc.GetFont()
        #font.SetFamily(wx.FONTFAMILY_MODERN)
        #font.SetPointSize(14)
        #dc.SetFont(font)
        
        #n = 0
        #for i in range(90, 360, 90):
            #dc.DrawLabel(dirLabels[n], ((i*wScale)-5, h-10, 20, 20), wx.ALIGN_TOP)
            #n += 1
    
    def DrawGrid(self, dc):
        w, h = self.GetSize()        
        hScale = h / 90.0
        wScale = w / 360.0

        # minor grid lines
        if self.minorAxis:
            #dc.SetPen(wx.Pen('#000060', 1, wx.DOT))
            dc.SetPen(wx.Pen('#000060', 1, wx.DOT))
            for i in range(1, 90, 1):
                if (i % 10) != 0:
                    dc.DrawLine(0, i*hScale, w, i*hScale)

            for i in range(2, 360, 2):
                if (i % 20) != 0:
                    dc.DrawLine(i*wScale, 0, i*wScale, h)
        
        #dc.SetPen(wx.Pen('#000060', 1, wx.DOT))
        dc.SetPen(wx.Pen('#666666', 1, wx.DOT))
        # major grid lines
        for i in range(10, 90, 10):
            dc.DrawLine(0, i*hScale, w, i*hScale)

        for i in range(20, 360, 20):
            dc.DrawLine(i*wScale, 0, i*wScale, h)
        
        dc.SetPen(wx.Pen('#008000', 1, wx.LONG_DASH))
        #dc.DrawLine(0, 12*hScale, w, 12*hScale)
        dc.DrawLine(0, 57*hScale, w, 57*hScale)
        #font = dc.GetFont()
        #font.SetFamily(wx.FONTFAMILY_MODERN)
        #font.SetPointSize(DEFAULT_FONT_SIZE)
        #dc.SetFont(font)
        #dc.SetTextForeground('#FF0000')
        #dc.DrawText("Lower Observational Limit", 3*hScale, 12*hScale - 1)
        #dc.DrawText("Leaf Boundry",57*hScale - 1, 5)
            
        #for i in range(90, 360, 90):
        #    dc.DrawLine(i*wScale, 0, i*wScale, h)
    
    def StereographicTransform(self, lat, lon, c_lat, c_lon):
        w, h = self.GetSize()

        k = 2 / (1 + math.sin(c_lat) * math.sin(lat) + math.cos(c_lat) * math.cos(lat) * math.cos(lon - c_lon))
        x = k * math.cos(lat) * math.sin(lon - c_lon)
        y = k * (math.cos(c_lat) * math.sin(lat) - math.sin(c_lat) * math.cos(lat) * math.cos(lon - c_lon))
        
        return x, y
        
    def DrawData(self, dc):
        w, h = self.GetSize()

        hScale = h / 90.
        wScale = w / 360.
        
        #for i in range(45):
        #    x_pos, y_pos = self.StereographicTransform(i, 0, 0.0, 0.0)
        #    #print x_pos * wScale, y_pos * hScale
        #    dc.DrawCircle(x_pos * wScale, y_pos * hScale, 2)
        
        if self.objects != None:
            for key in self.objects.keys():
                name, x_pos, y_pos, colour_idx = self.objects[key]

                if colour_idx >= 1.41:
                    colour = COLOUR_TABLE[0]
                elif colour_idx < 1.41 and colour_idx >= 0.82:
                    colour = COLOUR_TABLE[0]
                elif colour_idx < 0.82 and colour_idx >= 0.59:
                    colour = COLOUR_TABLE[1]
                elif colour_idx < 0.59 and colour_idx >= 0.31:
                    colour = COLOUR_TABLE[2]
                elif colour_idx < 0.31 and colour_idx >= 0.0:
                    colour = COLOUR_TABLE[3]
                elif colour_idx < 0.0 and colour_idx >= -0.29:
                    colour = COLOUR_TABLE[4]
                elif colour_idx < -0.29:
                    colour = COLOUR_TABLE[5]
                    
                dc.SetBrush(wx.Brush(colour))
                dc.SetPen(wx.Pen(colour))
                
                x_pos = x_pos * wScale
                y_pos = y_pos * hScale
                
                x_mouse, y_mouse = self.mouseMovePos
                y_mouse = h - y_mouse
                
                x_mouse = x_mouse / wScale
                y_mouse = y_mouse / hScale
                
                dc.DrawCircle(x_pos, y_pos, 2)
                
                if self.target == key:
                    # Draw Bounding Box
                    BB_SCALE = 2
                    
                    dc.SetPen(wx.Pen('#00FF00'))
                    dc.SetBrush(wx.Brush('#00FF00', wx.TRANSPARENT))
                    dc.DrawRectangle(x_pos - 8, y_pos - 8, 16, 16)
                    
                    font = dc.GetFont()
                    font.SetFamily(wx.FONTFAMILY_MODERN)
                    font.SetPointSize(DEFAULT_FONT_SIZE)
                    dc.SetFont(font)
                    #dc.SetTextForeground('#000000')
                    #dc.DrawText("Target: " + name, AZMTH + 13, ALT - 11)
                    dc.SetTextForeground('#00FF00')
                    textExt = dc.GetTextExtent(name)
                    
                    if textExt[0] + x_pos > w:    
                        dc.DrawText(name, (x_pos - textExt[0]) - 12, y_pos - 10)
                    else:
                        dc.DrawText(name, x_pos + 12, y_pos - 10)
                    
                else:
                    distToMouse = math.sqrt((x_pos / wScale - x_mouse) ** 2 + (y_pos / hScale - y_mouse) ** 2)
                    if distToMouse < 4:
                        self.nearest_object = key
                        font = dc.GetFont()
                        font.SetFamily(wx.FONTFAMILY_MODERN)
                        font.SetPointSize(DEFAULT_FONT_SIZE)
                        dc.SetFont(font)
                            #dc.SetTextForeground('#000000')
                            #dc.DrawText(name, AZMTH + 6, ALT - 1)
                        dc.SetTextForeground('#ffffff')
                        textExt = dc.GetTextExtent(name)
                        
                        if textExt[0] + x_pos + 5 > w:    
                            dc.DrawText(name, (x_pos - textExt[0]) - 5, y_pos)
                        else:
                            dc.DrawText(name, x_pos + 5, y_pos)
        
        dc.SetBrush(wx.Brush('#00FF00', wx.TRANSPARENT))
        dc.SetPen(wx.Pen(CROSS_HAIR_COLOUR))
            
        dc.DrawCircle(self.telescopePosition[0]*wScale , self.telescopePosition[1]*hScale, 16)
        dc.DrawCircle(self.telescopePosition[0]*wScale, self.telescopePosition[1]*hScale, 4)
        
    def Redraw(self, evt):
        self.Refresh()
        
    def ReadObjectDatabaseFile(self, f):
        file = open(f, 'r')
        lines = file.readlines()
        objectDictionary = {}
        
        for line in lines:
            line = line.rstrip('\n')
            if not line.startswith('#'):
                if len(line) != 0:
                    line = line.split(',')
                    
                    id = int(float(line[0]))
                    name = line[1]
                    x_pos = int(float(line[2]))
                    y_pos = int(float(line[3]))
                    colour = int(float(line[4]))
                    
                    objectDictionary[id] = (name, x_pos, y_pos, colour)
        
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
