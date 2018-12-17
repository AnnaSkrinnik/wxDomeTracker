#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

# The SYSINFO module displays system information in a single, integrated display
# to make the most of available screen space. The object blits text in cells and
# can update very quickly.

import wx
import math
import datetime

DISPLAY_PADDING = 12 # in screen units
FONT_SIZE = 12
TEXT_WRAP = False

class TextBuff:
    def __init__(self, parent):
        self.parent = parent
        self._text_lines = [] # main buffer for lines
    
    def clearBuffer(self):
        self._text_lines = []
        
    def writeLine(self, t_ln):
        if len(t_ln) > 0:
            self._text_lines.append(str(t_ln))
    
    def getLines(self, row=0, col=0, scroll_pos=0):
        l_wrap = []
        for l_text in self._text_lines:
            # open office algorithim for word wrapping with space culling
            l_text = l_text.split(' ')
            
            wrap_line = ''
            space_left = col
            for word in l_text:
                if (len(word) + 1) > space_left:
                    l_wrap.append(wrap_line)
                    # reset
                    space_left = col
                    wrap_line = '{0}'.format(word)
                else:
                    space_left = space_left - (len(word) + 1)
                    if wrap_line == '':
                        wrap_line = '{0}'.format(word)
                    else:
                        wrap_line = '{0} {1}'. format(wrap_line, word)
                
            l_wrap.append(wrap_line)
        
        # cull lines for display
        disp_lines = l_wrap[scroll_pos:]#[:row]
            
        return disp_lines
        
        # old, word clipping method
        #o_lines = []
        #for line in self._text_lines:
        #    if len(line) >= row: 
        #        if TEXT_WRAP:
        #            continue
                    #o_lines.append(line[:row] + '$')
        #        else:
        #            o_lines.append(line[:(row - 3)] + '~')
        #    elif len(line) < row:
        #        o_lines.append(line)
        #
        #return o_lines
    
    def __del__(self):
        del self._text_lines

class CoordDisplay(wx.Panel): 
    def __init__(self, parent):
        wx.Panel.__init__(self, parent) #, style=wx.SUNKEN_BORDER)
        self.SetBackgroundColour('#000000')
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetDoubleBuffered(True)
        
        self._text_buff = TextBuff(self)
        
        self.font_size = 12
        self.font_colour = "#FFFFFF"
        
        self.value = True
        self.elements = 3
        self.max_elements = 6
        self.minsize = (150, 150)
        
        self.cell_size = None
        self.cell_dims = None
        
        # various user-defined strings to display
        self.localtime = "Updating..."
        self.universaltime = "Updating..."
        self.siderialtime = "Updating..."
        self.juliandate = "Updating..."
        
        self.trg_name = "*NOT SPECIFIED*"
        self.trg_ra = "Not Available"
        self.trg_dec = "Not Available"
        self.trg_ha = " Not Available"
        self.trg_epoc = "Not Available"
        self.trg_alt = "Not Available"
        self.trg_azm = "Not Available"
        self.trg_ams = "Not Available"

        self.tel_mode =  "Virtual Telescope"
        self.tel_ra =  "Updating..."
        self.tel_dec =  "Updating..."
        self.tel_ha =  " Updating..."
        self.tel_alt =  "Updating..."
        self.tel_azm =  "Updating..."
        self.tel_ams =  "Updating..."

        self.argo_text = "Updating..."
        self.rain_sensor = "Updating..."
        self.hwc_text = "Updating..."

        # TIMER OBJECTS
        #self.tmrRedrawObjects = wx.Timer(self)
        #self.tmrCheckMove = wx.Timer(self)
        
        #self.Bind(wx.EVT_TIMER, self.Redraw, self.tmrRedrawObjects)
        
        # ENABLE GLOBAL TIME
        #self.tmrRedrawObjects.Start(150)
    
    def writeLine(self, s_ln):
        self._text_buff.writeLine(str(s_ln))
        self.Redraw()

    def SetSideralTimeText(self, t_st):
        self.siderialtime = t_st
    
    def SetLocalTimeText(self, t_lt):
        self.localtime = t_lt
    
    def SetUniversalTimeText(self, t_ut):
        self.universaltime = t_ut
    
    def SetJulianDateText(self, t_jd):
        self.juliandate = t_jd
    
    def SetTargetInfoText(self, l_targ):
        self.trg_name = l_targ[0]
        
        if len(self.trg_name) >= 18:
            self.trg_name = self.trg_name[:17] + '~'
        
        self.trg_ra = l_targ[1]
        self.trg_dec = l_targ[2]
        self.trg_ha = l_targ[3]
        self.trg_epoc = l_targ[4]
        self.trg_azm = l_targ[5]
        self.trg_alt = l_targ[6]
        self.trg_ams = l_targ[7]
        #self.trg_ext = l_targ[8]
    
    def SetTelescopeInfoText(self, l_tele):
        self.tel_ra = l_tele[0]
        self.tel_dec = l_tele[1]
        self.tel_ha = l_tele[2]
        self.tel_azm = l_tele[3]
        self.tel_alt = l_tele[4]
        self.tel_ams = l_tele[5]

    def SetArgoConnectionStatus(self, t_argo):
        self.argo_text = t_argo
    
    def SetRainSensorText(self, t_rs):
        self.rain_sensor = t_rs
    
    def SetHWCText(self, t_hwc):
        self.hwc_text = t_hwc
    
    def Value(self, state = 0):
        self.value = state
        
        return self.value

    def SetRAText(self, t_ra):
        self.txtRA = str(t_ra)
    
    def SetDecText(self, t_dec):
        self.txtDec = str(t_dec)
    
    def SetHAText(self, t_ha):
        self.txtHA = str(t_ha)
    
    def OnPaint(self, event):
        w, h = self.GetSize()
        dc = wx.PaintDC(self)
        
        if self.value:  
            self.SetForegroundColour('#008800')
        else:
            self.SetForegroundColour('#880000')
            
        # if cell size for text is known then draw data
        if self.cell_dims:
            self.DrawData(dc)
        else:
            font = wx.Font(self.font_size, wx.MODERN, wx.NORMAL, wx.BOLD)
            #font.SetPointSize(10)
            dc.SetFont(font)
            self.cell_size = dc.GetTextExtent('0') # text dims for monospace
            self.cell_dims = (w / self.cell_size[0], h / self.cell_size[1])
    
    def GetFontSize(self):
        return self.font_size

    def SetFontSize(self, size):
        self.font_size = size 
        self.cell_dims = None # reset
            
    def OnSize(self, event):
        self.cell_dims = None # cell dims change with resize, so clear them 
        self.Refresh()
        
    def DrawData(self, dc):
        w, h = self.GetSize()

        dc.SetPen(wx.Pen('#2D2D2D')) 
        dc.SetBrush(wx.Brush('#2D2D2D'))
        log_bp_x = (self.cell_size[0] * 37) + DISPLAY_PADDING
        dc.DrawRectangle(0, 0, log_bp_x, h)
        
        dc.SetTextForeground('#FFFFFF')
        font =  wx.Font(self.font_size, wx.MODERN, wx.NORMAL, wx.NORMAL)
        #font.SetPointSize(10)
        dc.SetFont(font)
        
        # pretty decorations
        dc.GradientFillLinear((0, 0, log_bp_x, 32), '#2D2D2D', '#646464', wx.NORTH)
        dc.GradientFillLinear((log_bp_x, 0, w, 32), '#000000', '#646464', wx.NORTH)
        
        #title_text = 'wxDomeTracker 4.0.1'
        #text_size = dc.GetTextExtent(title_text)
        #dc.DrawText(title_text, (w / 2.0) - (text_size[0] / 2.0), 2)
        
        ruler = '='*36

        texts = ["Time Information", 
            ruler,
            "LOCAL TIME:      {0}".format(self.localtime),
            "UNIVERSAL TIME:  {0}".format(self.universaltime),
            "SIDERIAL TIME:   {0}".format(self.siderialtime),
            "JULIAN DATE:     {0}".format(self.juliandate),
            "",
            "Telescope Telemetry", 
            ruler,
            "POINTING MODE:    {0}".format(self.tel_mode),
            "RIGHT ASCENSION:  {0}".format(self.tel_ra),
            "DECLINATION:      {0}".format(self.tel_dec),
            "HOUR ANGLE:      {0}".format(self.tel_ha),
            "AZIMUTH (DEG):    {0}".format(self.tel_azm),
            "ALTITUDE (DEG):   {0}".format(self.tel_alt),
            "AIRMASS:          {0}".format(self.tel_ams),
            "",
            "Target Object Details", 
            ruler,
            "TARGET NAME:      {0}".format(self.trg_name),
            "RIGHT ASCENSION:  {0}".format(self.trg_ra),
            "DECLINATION:      {0}".format(self.trg_dec),
            "HOUR ANGLE:      {0}".format(self.trg_ha),
            "EPOCH:            {0}".format(self.trg_epoc),
            "AZIMUTH (DEG):    {0}".format(self.trg_azm),
            "ALTITUDE (DEG):   {0}".format(self.trg_alt),
            "AIRMASS:          {0}".format(self.trg_ams),
           "",
            "System Status and Warnings", 
            ruler,
            "ARGO NAVIS:       {0}".format(self.argo_text),
            #"PC INTERFACE:     {0}".format(self.hwc_text),
            "RAIN SENSOR:      {0}".format(self.rain_sensor)]
        
        h_row = dc.GetTextExtent('0')[1] #+ DISPLAY_PADDING
        bp = DISPLAY_PADDING
        #self.SetMinSize((len(ruler) + (2 * bp), 512))
        n = 0
        for i in range(len(texts)):                
            text = texts[i]
            text_size = dc.GetTextExtent(text)
            h_pos = bp + (h_row * i)
            dc.DrawText(text, DISPLAY_PADDING, h_pos)
            n += 1
        
        # draw log output
        n_c, n_r = self.cell_dims
        len_log = len(self._text_buff.getLines(n_r, n_c - 38))
        
        if len_log >= n_r:
            scroll_pos = len_log - n_r + 1
            s_logs = self._text_buff.getLines(n_r, n_c - 38, scroll_pos)
        else:
            s_logs = self._text_buff.getLines(n_r, n_c - 38)
            
        #log_bp_x = (self.cell_size[0] * 37) + DISPLAY_PADDING
        #h_pos = DISPLAY_PADDING
        #dc.DrawText('System Messages', log_bp_x, h_pos)
        #h_pos = DISPLAY_PADDING + self.cell_size[1]
        #dc.DrawText('='*(n_c-38), log_bp_x, h_pos)

        if s_logs:
            for i in range(len(s_logs)):
                s_line = s_logs[i]
                log_bp_x = (self.cell_size[0] * 38) + DISPLAY_PADDING
                h_pos = (h_row * i) + DISPLAY_PADDING
                dc.DrawText(s_line, log_bp_x, h_pos)
        
    def Redraw(self, evt=None):
        self.Refresh()
            
class LineChartExample(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(600, 400))

        panel = wx.Panel(self, -1)
        panel.SetBackgroundColour('BLACK')

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.linechart = CoordDisplay(panel)
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
