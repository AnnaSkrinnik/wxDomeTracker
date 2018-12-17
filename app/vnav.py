#!/usr/bin/python

# linechart.py

import wx
import math
import datetime

DISPLAY_PADDING = 64 # in screen units

class VNavWin(wx.Panel): 
    def __init__(self, parent):
        wx.Panel.__init__(self, parent) #, style=wx.SUNKEN_BORDER)
        self.SetBackgroundColour('BLACK')
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetDoubleBuffered(True)
        
        self.value = True
        self.elements = 4
        self.max_elements = 6
        
        self.txtRA = "RA: Updating..."
        self.txtDec = "DEC: Updating..." 
        self.txtHA = "HA: Updating..."
        self.txtSiderial = "LMST: Updating..."
        
        self.SetMinSize((450, 250))
        #self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))

        # TIMER OBJECTS
        self.tmrRedrawObjects = wx.Timer(self)
        self.tmrCheckMove = wx.Timer(self)
        
        # ENABLE GLOBAL TIME
        #self.tmrRedrawObjects.Start(150)
    
    def Value(self, state = 0):
        self.value = state
        
        return self.value

    def SetRAText(self, t_ra):
        self.txtRA = "RA: {0}".format(str(t_ra))
    
    def SetDecText(self, t_dec):
        self.txtDec = "DEC: {0}".format(str(t_dec))
    
    def SetHAText(self, t_ha):
        self.txtHA = "HA: {0}".format(str(t_ha))
    
    def SetLMSTText(self, t_lmst):
        self.txtSiderial = "LMST: {0}".format(str(t_lmst))
    
    def OnPaint(self, event):
        w, h = self.GetSize()
        dc = wx.PaintDC(self)
        
        if self.value:  
            self.SetForegroundColour('#008800')
        else:
            self.SetForegroundColour('#880000')
        
        self.DrawData(dc)
        
    def OnSize(self, event):
        self.Refresh()
        
    def DrawData(self, dc):
        w, h = self.GetSize()
        
        dc.SetTextForeground('#FF0000')
        font =  dc.GetFont()
        font.SetPointSize(100)
        dc.SetFont(font)
        
        pen = wx.Pen('#FFFFFF', 20, wx.SOLID)
        dc.SetPen(pen)
        dc.DrawLine(0, h / 2., w, h / 2.)
        dc.DrawLine(w / 2., 0, w / 2., h)
        
        #h_row = dc.GetTextExtent('A')[1] #+ DISPLAY_PADDING
        #bp = (h / 2.0) - ((h_row * self.elements) / 2.0)

        #texts = [self.txtRA, self.txtHA, self.txtDec, self.txtSiderial] #, self.txtDec]
        
        #for i in range(self.elements):
        #    text = texts[i]
        #    text_size = dc.GetTextExtent(text)
        #    h_pos = bp + (h_row * i)
        #    w_pos = (w / 2.0) - (text_size[0] / 2.0)
        #    dc.DrawText(text, w_pos, h_pos)
        
    def Redraw(self, evt=None):
        self.Refresh()
            
class LineChartExample(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(600, 400))

        panel = wx.Panel(self, -1)
        panel.SetBackgroundColour('BLACK')

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.linechart = VNavWin(panel)
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
