# -*- coding: iso-8859-15 -*-
# generated by wxGlade 0.6.3 on Sun Jun  5 12:23:04 2011

import wx
import serial
import time

import Queue
import execf

DEFAULT_REPEAT_INTERVAL = 100

NORMALIZE_DATA = 0x00
NORMALIZE_CONTROL = 0x0B
POWER_OFF = 0x80
MOVE_LEFT = 0x20
MOVE_RIGHT = 0x10
DOME_CLOSE = 0x40
DOME_OPEN = 0x08 # Control
DOME_PULSE = 0x80

TELESCOPE_NORTH = 0x01
TELESCOPE_SOUTH = 0x04
TELESCOPE_EAST  = 0x02
TELESCOPE_WEST  = 0x08

FOCUS_IN = 0x2
FOCUS_OUT = 0xE

SENSE_ZERO_AZMTH = 0x20
SENSE_RAIN = 0x40

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode

# end wxGlade

class ObsControlPanel(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: ObsControlPanel.__init__
        kwds["style"] = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX #|wx.STAY_ON_TOP #|wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        self.parent = args[0]

        self.joy = wx.Joystick()
        self.joy.SetCapture(self)
        
        self.state = -1
        self._slewrate = 1
        
        self.m_east = 0
        self.m_west = 0
        self.m_north = 0
        self.m_south = 0
        
        self.remote = False
        
        self._slewtbl_ra = {1: 0.05, 2: 0.1, 3: 0.25, 4: 4.2, 5: 8.5}
        self._slewtbl_dec = {1: 0.05, 2: 0.1, 3: 0.25, 4: 5.2, 5: 8.5}
        self._slewstr = {1: "TRACK", 2: "GUIDE", 3: "SLEW", 4: "WARP", 5: "LUDACRIS"}
        
        self.fraDomeFunctions_staticbox = wx.StaticBox(self, -1, "Dome Shutter")
        self.fraTelescopeMotionControls_staticbox = wx.StaticBox(self, -1, "Telescope Movement")
        self.fraFocus_staticbox = wx.StaticBox(self, -1, "Telescope Focus")
        self.fraMovementControls_staticbox = wx.StaticBox(self, -1, "Dome Rotation")
        self.fraSlewRate = wx.StaticBox(self, -1, "Slew Rate")
        self.cmdDomeCCW = wx.Button(self, -1, "CCW")
        self.cmdDomeCW = wx.Button(self, -1, "CW")
        self.cmdOpenDome = wx.Button(self, -1, "Open")
        self.cmdCloseDome = wx.Button(self, -1, "Close")
        self.cmdMoveTelescopeNorth = wx.Button(self, -1, "North")
        self.cmdMoveTelescopeWest = wx.Button(self, -1, "West")
        self.cmdMoveTelescopeEast = wx.Button(self, -1, "East")
        self.cmdMoveTelescopeSouth = wx.Button(self, -1, "South")
        self.cmdFocusIn = wx.Button(self, -1, "In")
        self.cmdFocusOut = wx.Button(self, -1, "Out")
        self.cmdEnableRemote = wx.ToggleButton(self, -1, "Remote Enable")
        self.cmdEnableTracking = wx.ToggleButton(self, -1, "Track Sky")
        self.cmdClose = wx.Button(self, -1, "&Close")
        
        #self.lblSlewText = wx.StaticText(self, -1, "<SLEW_TEXT_HERE>")
        
        self.sldSlewSpeed = wx.Slider(self, -1, value=4, minValue=1, maxValue=5, style=wx.SL_VERTICAL | wx.SL_RIGHT | wx.SL_LABELS | wx.SL_AUTOTICKS)

        self.__set_properties()
        self.__do_layout()
        
        self.parent.StateObject.gui_vars["GUI_CTRL_COUNT"] += 1

        # control timers
        self.tmrRotateCCW = wx.Timer(self)
        self.tmrRotateCW = wx.Timer(self)
        self.tmrFocusIn = wx.Timer(self)
        self.tmrFocusOut = wx.Timer(self)
        self.tmrMoveNorth = wx.Timer(self)
        self.tmrMoveSouth = wx.Timer(self)
        self.tmrMoveEast = wx.Timer(self)
        self.tmrMoveWest = wx.Timer(self)
        self.tmrOpenDome = wx.Timer(self)
        self.tmrCloseDome = wx.Timer(self)
        self.tmrPollHandPaddle = wx.Timer(self)
        self.tmrCheckRAMotion = wx.Timer(self)
        self.tmrCheckDecMotion = wx.Timer(self)
        
        # please stop that !!! <<<<<<<<<<<
        
        #
        #   SERIAL COMM. TESTING
        #
        
        #self._RACtrl = serial.Serial('COM5', baudrate=9600, timeout=1, writeTimeout=1)
        #self._RACtrl.write('PR5\r\n'); time.sleep(0.015)
        #self._RACtrl.write('AC3\r\n'); time.sleep(0.015)
        #self._RACtrl.write('DE3\r\n'); time.sleep(0.015)
        #self._RACtrl.write('AM3\r\n'); time.sleep(0.015)
        #self._RACtrl.write('VE8\r\n'); time.sleep(0.015)
        #self._RACtrl.write('MT1\r\n'); time.sleep(0.015)
        
        self.ra_conf_dat = {}
        
        self.ra_qin = Queue.Queue()
        self.ra_qout = Queue.Queue()
        self.ra_qerr = Queue.Queue()
        
        self._RACtrl = execf.SerialCommRA('COM10', 9600, self.ra_qin, self.ra_qout, self.ra_qerr)
        self._RACtrl.daemon = True
        self._RACtrl.start()

        self.dec_qin = Queue.Queue()
        self.dec_qout = Queue.Queue()
        self.dec_qerr = Queue.Queue()

        self._DECCtrl = execf.SerialCommDec('COM11', 9600, self.dec_qin, self.dec_qout, self.dec_qerr)
        self._DECCtrl.daemon = True
        self._DECCtrl.start()

        self.dc_qin = Queue.Queue(maxsize=1)
        self.dc_qout = Queue.Queue(maxsize=1)
        self.dc_qerr = Queue.Queue(maxsize=1)
        
        self._DomeCtrl = execf.DomeControlInterface('COM3', 9600,
            self.dc_qin, self.dc_qout, self.dc_qerr)
        self._DomeCtrl.daemon = True
        self._DomeCtrl.start()

        self.hp_qin = Queue.Queue(maxsize=1)
        self.hp_qout = Queue.Queue(maxsize=1)
        self.hp_qerr = Queue.Queue(maxsize=1)
        
        self._HandPaddleCtrl = execf.HandPaddleInterface('COM15', 9600, 
            self.hp_qin, self.hp_qout, self.hp_qerr)
        self._HandPaddleCtrl.daemon = True
        self._HandPaddleCtrl.start()
        
        # hardware timers
        self.tmrReadOut = wx.Timer(self)
        
        # server timer
        self.tmrServer = wx.Timer(self)
        
        # keyboard event bindings
        self.Bind(wx.EVT_JOY_BUTTON_DOWN, self.onJoyBtnDn)
        self.Bind(wx.EVT_JOY_BUTTON_UP, self.onJoyBtnUp)
        
        # move dome counter-clockwise events
        self.cmdDomeCCW.Bind(wx.EVT_LEFT_DOWN, self.OnMoveCCWDown)
        self.cmdDomeCCW.Bind(wx.EVT_LEFT_UP, self.OnMoveCCWUp)
        
        # move dome counter-clockwise events
        self.cmdDomeCW.Bind(wx.EVT_LEFT_DOWN, self.OnMoveCWDown)
        self.cmdDomeCW.Bind(wx.EVT_LEFT_UP, self.OnMoveCWUp)

        # focus in events
        self.cmdFocusIn.Bind(wx.EVT_LEFT_DOWN, self.OnFocusInDown)
        self.cmdFocusIn.Bind(wx.EVT_LEFT_UP, self.OnFocusInUp)
        
        # focus out events
        self.cmdFocusOut.Bind(wx.EVT_LEFT_DOWN, self.OnFocusOutDown)
        self.cmdFocusOut.Bind(wx.EVT_LEFT_UP, self.OnFocusOutUp)
        
        # move telescope north
        self.cmdMoveTelescopeNorth.Bind(wx.EVT_LEFT_DOWN, self.OnMoveNorthDown)
        self.cmdMoveTelescopeNorth.Bind(wx.EVT_LEFT_UP, self.OnMoveNorthUp)

        # move telescope south
        self.cmdMoveTelescopeSouth.Bind(wx.EVT_LEFT_DOWN, self.OnMoveSouthDown)
        self.cmdMoveTelescopeSouth.Bind(wx.EVT_LEFT_UP, self.OnMoveSouthUp)

        # move telescope east
        self.cmdMoveTelescopeEast.Bind(wx.EVT_LEFT_DOWN, self.OnMoveEastDown)
        self.cmdMoveTelescopeEast.Bind(wx.EVT_LEFT_UP, self.OnMoveEastUp)

        # move telescope west
        self.cmdMoveTelescopeWest.Bind(wx.EVT_LEFT_DOWN, self.OnMoveWestDown)
        self.cmdMoveTelescopeWest.Bind(wx.EVT_LEFT_UP, self.OnMoveWestUp)

        # open dome
        self.cmdOpenDome.Bind(wx.EVT_LEFT_DOWN, self.OnOpenDomeDown)
        self.cmdOpenDome.Bind(wx.EVT_LEFT_UP, self.OnOpenDomeUp)

        # close dome
        self.cmdCloseDome.Bind(wx.EVT_LEFT_DOWN, self.OnCloseDomeDown)
        self.cmdCloseDome.Bind(wx.EVT_LEFT_UP, self.OnCloseDomeUp)

        # purge box
        self.cmdEnableTracking.Bind(wx.EVT_TOGGLEBUTTON, self.OnEnableTracking)
        self.cmdEnableRemote.Bind(wx.EVT_TOGGLEBUTTON, self.OnEnableRemote)
                
        # Timer event bindings
        self.Bind(wx.EVT_TIMER, self.RotateDomeCCW, self.tmrRotateCCW)
        self.Bind(wx.EVT_TIMER, self.RotateDomeCW, self.tmrRotateCW)
        self.Bind(wx.EVT_TIMER, self.FocusIn, self.tmrFocusIn)
        self.Bind(wx.EVT_TIMER, self.FocusOut, self.tmrFocusOut)
        self.Bind(wx.EVT_TIMER, self.MoveNorth, self.tmrMoveNorth)
        self.Bind(wx.EVT_TIMER, self.MoveSouth, self.tmrMoveSouth)
        self.Bind(wx.EVT_TIMER, self.MoveEast, self.tmrMoveEast)
        self.Bind(wx.EVT_TIMER, self.MoveWest, self.tmrMoveWest)
        self.Bind(wx.EVT_TIMER, self.OpenDome, self.tmrOpenDome)
        self.Bind(wx.EVT_TIMER, self.CloseDome, self.tmrCloseDome)
        self.Bind(wx.EVT_TIMER, self.PollHandPaddle, self.tmrPollHandPaddle)
        self.Bind(wx.EVT_TIMER, self.CheckDecMotion, self.tmrCheckDecMotion)
        self.Bind(wx.EVT_TIMER, self.CheckRAMotion, self.tmrCheckRAMotion)
        self.Bind(wx.EVT_BUTTON, self.OnClose, self.cmdClose)
        #self.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.UpdateSlewRate, self.sldSlewSpeed)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPress)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        # end wxGlade
        
        self.tmrPollHandPaddle.Start(DEFAULT_REPEAT_INTERVAL) # poll handpaddle
        self.UpdateSlewRate()

    def __set_properties(self):
        # begin wxGlade: ObsControlPanel.__set_properties
        self.SetTitle("Observatory Control Panel")
        self.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_BTNFACE))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ObsControlPanel.__do_layout
        szrObservatoryControlPanel = wx.BoxSizer(wx.VERTICAL)
        grdExtraControls = wx.GridSizer(1, 3, 5, 5)
        szrAllControls = wx.BoxSizer(wx.HORIZONTAL)
        szrTelescopeControlPanel = wx.BoxSizer(wx.VERTICAL)
        fraFocus = wx.StaticBoxSizer(self.fraFocus_staticbox, wx.HORIZONTAL)
        fraTelescopeMotionControls = wx.StaticBoxSizer(self.fraTelescopeMotionControls_staticbox, wx.VERTICAL)
        grdEastWest = wx.GridSizer(1, 2, 0, 5)
        szrDomeControlPanel = wx.BoxSizer(wx.VERTICAL)
        fraDomeFunctions = wx.StaticBoxSizer(self.fraDomeFunctions_staticbox, wx.VERTICAL)
        grdCommandButtons = wx.GridSizer(2, 2, 5, 5)
        fraMovementControls = wx.StaticBoxSizer(self.fraMovementControls_staticbox, wx.VERTICAL)
        grdMoveButtons = wx.GridSizer(1, 2, 5, 5)
        grdMoveButtons.Add(self.cmdDomeCCW, 0, wx.EXPAND, 0)
        grdMoveButtons.Add(self.cmdDomeCW, 0, wx.EXPAND, 0)
        fraMovementControls.Add(grdMoveButtons, 1, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
        szrDomeControlPanel.Add(fraMovementControls, 1, wx.ALL, 5)
        grdCommandButtons.Add(self.cmdOpenDome, 0, wx.EXPAND, 0)
        grdCommandButtons.Add(self.cmdCloseDome, 0, wx.EXPAND, 0)
        fraDomeFunctions.Add(grdCommandButtons, 1, wx.ALL, 5)
        szrDomeControlPanel.Add(fraDomeFunctions, 0, wx.LEFT|wx.RIGHT, 5)
        szrAllControls.Add(szrDomeControlPanel, 1, wx.EXPAND, 0)
        fraTelescopeMotionControls.Add(self.cmdMoveTelescopeNorth, 0, wx.TOP|wx.ALIGN_CENTER_HORIZONTAL, 5)
        grdEastWest.Add(self.cmdMoveTelescopeWest, 0, 0, 0)
        grdEastWest.Add(self.cmdMoveTelescopeEast, 0, wx.ALIGN_RIGHT, 0)
        fraTelescopeMotionControls.Add(grdEastWest, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)
        fraTelescopeMotionControls.Add(self.cmdMoveTelescopeSouth, 0, wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 5)
        szrTelescopeControlPanel.Add(fraTelescopeMotionControls, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        fraFocus.Add(self.cmdFocusIn, 1, wx.ALL|wx.EXPAND, 5)
        fraFocus.Add(self.cmdFocusOut, 1, wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 5)
        szrTelescopeControlPanel.Add(fraFocus, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        szrAllControls.Add(szrTelescopeControlPanel, 0, wx.EXPAND, 0)
        szrObservatoryControlPanel.Add(szrAllControls, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        
        fraSlewRate = wx.StaticBoxSizer(self.fraSlewRate, wx.VERTICAL)
        fraSlewRate.Add(self.sldSlewSpeed, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        #fraSlewRate.Add(self.lblSlewText, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL, 5)
        szrAllControls.Add(fraSlewRate, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        
        grdExtraControls.Add(self.cmdEnableRemote, 0, wx.EXPAND, 0)
        grdExtraControls.Add(self.cmdEnableTracking, 0, wx.EXPAND, 0)
        grdExtraControls.Add(self.cmdClose, 0, wx.EXPAND|wx.ALIGN_RIGHT, 0)
        szrObservatoryControlPanel.Add(grdExtraControls, 0, wx.ALL|wx.ALIGN_RIGHT, 10)
        self.SetSizer(szrObservatoryControlPanel)
        szrObservatoryControlPanel.Fit(self)
        self.Center()
        self.Layout()
        # end wxGlade
        
    def UpdateSlewRate(self, event=None):
        #self.lblSlewText.SetLabel(self._slewstr[self.sldSlewSpeed.GetValue()])
        
        if event: event.Skip()
        
    def onJoyBtnDn(self, event=None):
        j_state = self.joy.GetButtonState()
        
        if j_state == 1: # ccw
            self.state = 1
            self.tmrRotateCCW.Start(DEFAULT_REPEAT_INTERVAL)
            self.parent.setSystemStatus("Dome CCW")
            if self.parent.pstack.ProcessTypeRunning('MACRO_RECORDING'):
                self.parent.startEventRecorder("DOME_CCW")
        elif j_state == 4: # cw
            self.state = 4
            self.tmrRotateCW.Start(DEFAULT_REPEAT_INTERVAL)
            self.parent.setSystemStatus("Dome CW")
            if self.parent.pstack.ProcessTypeRunning('MACRO_RECORDING'):
                self.parent.startEventRecorder("DOME_CW")
        else:
            pass
        
        event.Skip()

    def onJoyBtnUp(self, event=None):
        if self.state == 1:
            self.tmrRotateCCW.Stop()
            self.state = -1
        elif self.state == 4:
            self.tmrRotateCW.Stop()
            self.state = -1
            
        if self.parent.pstack.ProcessTypeRunning('MACRO_RECORDING'):
            if self.parent.StateObject.macros_vars["MACRO_EVENT_RECORD"]:
                self.parent.stopEventRecorder()
            else:
                self.parent.setSystemStatus(False)
            
        self.parent.hwc.resetDataRange()
        
        event.Skip()

    # ==========================================================================
    # Interface lock-outs
    # ==========================================================================

        self.cmdDomeCCW = wx.Button(self, -1, "CCW")
        self.cmdDomeCW = wx.Button(self, -1, "CW")
        self.cmdOpenDome = wx.Button(self, -1, "Open")
        self.cmdCloseDome = wx.Button(self, -1, "Close")
        self.cmdMoveTelescopeNorth = wx.Button(self, -1, "North")
        self.cmdMoveTelescopeWest = wx.Button(self, -1, "West")
        self.cmdMoveTelescopeEast = wx.Button(self, -1, "East")
        self.cmdMoveTelescopeSouth = wx.Button(self, -1, "South")
        self.cmdFocusIn = wx.Button(self, -1, "In")
        self.cmdFocusOut = wx.Button(self, -1, "Out")
        self.cmdEnableRemote = wx.ToggleButton(self, -1, "Remote Enable")
        self.cmdEnableTracking = wx.ToggleButton(self, -1, "Track Sky")
        self.cmdClose = wx.Button(self, -1, "&Close")
    
    def lockUI(self, locked=True, all_ctrls=False):
        if locked == True:
            self.cmdMoveTelescopeNorth.Enable(0)
            self.cmdMoveTelescopeWest.Enable(0)
            self.cmdMoveTelescopeEast.Enable(0)
            self.cmdMoveTelescopeSouth.Enable(0)
            self.sldSlewSpeed.Enable(0)
            
        elif locked == False:
            self.cmdMoveTelescopeNorth.Enable(1)
            self.cmdMoveTelescopeWest.Enable(1)
            self.cmdMoveTelescopeEast.Enable(1)
            self.cmdMoveTelescopeSouth.Enable(1)
            self.sldSlewSpeed.Enable(1)
        
        return locked
        
    def lockDomeMotion(self, locked=1): # 1 = locked, 0 = unlocked
        if locked == 1:
            self.cmdDomeCCW.Enable(0)
            self.cmdDomeCW.Enable(0)
        elif locked == 0:
            self.cmdDomeCCW.Enable(1)
            self.cmdDomeCW.Enable(1)
        
        return locked
        
    def lockDomeShutter(self, locked=1): # 1 = locked, 0 = unlocked
        if locked == 1:
            self.cmdOpenDome.Enable(0)
            self.cmdCloseDome.Enable(0)
        elif locked == 0:
            self.cmdOpenDome.Enable(1)
            self.cmdCloseDome.Enable(1)
        
        return locked
    
    def PollHandPaddle(self, event=None):
        if self.remote == True:
            if self.hp_qin.empty():
                self.hp_qin.put('?')
            
            if not self.hp_qout.empty():
                slew_rate, direction = self.hp_qout.get()
                
                if direction == '1':
                    self.OnMoveNorthDown()
                    
                elif direction == '2':
                    self.OnMoveEastDown()
                    
                elif direction == '3':
                    self.OnMoveSouthDown()
                    
                elif direction == '4':
                    self.OnMoveWestDown()
                    
                elif direction == '0':
                    if self.m_north == 1:
                        self.OnMoveNorthUp()
                    elif self.m_east == 1:
                        self.OnMoveEastUp()
                    elif self.m_south == 1:
                        self.OnMoveSouthUp()
                    elif self.m_west == 1:
                        self.OnMoveWestUp()
                    else:
                        pass
                
                if slew_rate == '0':
                    self.sldSlewSpeed.SetValue(3)
                elif slew_rate == '2':
                    self.sldSlewSpeed.SetValue(4)
                elif slew_rate == '1':
                    self.sldSlewSpeed.SetValue(5)
                else:
                    self.sldSlewSpeed.SetValue(3)
                
                
        event.Skip()

    # ==========================================================================
    # Keyboard events
    # ==========================================================================
    
    #def OnKeyDown(self, event):
        #keycode = event.GetKeyCode()
        #if keycode == wx.WXK_LEFT:
            ##self.parent.hwc.setData(MOVE_LEFT)
            #self.tmrRotateCW.Start(DEFAULT_REPEAT_INTERVAL)
            #self.parent.setSystemStatus("Dome CCW")
            #if self.parent.pstack.ProcessTypeRunning('MACRO_RECORDING'):
                #self.parent.startEventRecorder("DOME_CCW")
        #elif keycode == wx.WXK_RIGHT:
            ##self.parent.hwc.setData(MOVE_RIGHT)
            #self.tmrRotateCW.Start(DEFAULT_REPEAT_INTERVAL)
            #self.parent.setSystemStatus("Dome CCW")
            #if self.parent.pstack.ProcessTypeRunning('MACRO_RECORDING'):
                #self.parent.startEventRecorder("DOME_CCW")
        
        ##event.Skip()
    
    #def OnKeyUp(self, event):
        #self.parent.hwc.resetDataRange()
        
        #event.Skip()
            
    # ==========================================================================
    # Mouse button hold down events
    # ==========================================================================

    def OnOpenDomeDown(self, event=None):
        self.dc_qin.put("SHUTTER_OPEN")
        self.tmrOpenDome.Start(DEFAULT_REPEAT_INTERVAL)
        event.Skip()

    def OnOpenDomeUp(self, event=None):
        self.dc_qin.put("SHUTTER_STOP")
        self.tmrOpenDome.Stop()
        #self.parent.hwc.resetControlRange()
        event.Skip()

    def OnCloseDomeDown(self, event=None):
        self.dc_qin.put("SHUTTER_CLOSE")
        self.tmrCloseDome.Start(DEFAULT_REPEAT_INTERVAL)
        event.Skip()

    def OnCloseDomeUp(self, event=None):
        self.dc_qin.put("SHUTTER_STOP")
        self.tmrCloseDome.Stop()
        #self.parent.hwc.resetDataRange()
        event.Skip()

    def OnMoveCCWDown(self, event=None):
        #self.tmrRotateCCW.Start(DEFAULT_REPEAT_INTERVAL)
        self.parent.setSystemStatus("Dome CCW")
        if self.parent.pstack.ProcessTypeRunning('MACRO_RECORDING'):
            self.parent.startEventRecorder("DOME_CCW")
        
        self.dc_qin.put("DOME_CCW")
        
        event.Skip()

    #def OnKeyCCWDown(self, event):
        #keycode = event.GetKeyCode()
        #if keycode == wx.WXK_SPACE:
            #self.tmrRotateCW.Start(DEFAULT_REPEAT_INTERVAL)
            #self.parent.setSystemStatus("Dome CCW")
            #if self.parent.pstack.ProcessTypeRunning('MACRO_RECORDING'):
                #self.parent.startEventRecorder("DOME_CCW")
                
        #event.Skip()

    def OnMoveCCWUp(self, event=None):
        self.tmrRotateCCW.Stop()
        if self.parent.pstack.ProcessTypeRunning('MACRO_RECORDING'):
            if self.parent.StateObject.macros_vars["MACRO_EVENT_RECORD"]:
                self.parent.stopEventRecorder()
            else:
                self.parent.setSystemStatus(False)
            
        #self.parent.hwc.resetDataRange()
        self.dc_qin.put("DOME_STOP")

        event.Skip()

    def OnMoveCWDown(self, event=None):
        #self.tmrRotateCCW.Start(DEFAULT_REPEAT_INTERVAL)
        self.parent.setSystemStatus("Dome CW")
        if self.parent.pstack.ProcessTypeRunning('MACRO_RECORDING'):
            self.parent.startEventRecorder("DOME_CW")
        
        self.dc_qin.put("DOME_CW")
        
        event.Skip()

    #def OnKeyCWDown(self, event):
        #keycode = event.GetKeyCode()
        #if keycode == wx.WXK_SPACE:
            #self.tmrRotateCW.Start(DEFAULT_REPEAT_INTERVAL)
            #self.parent.setSystemStatus("Dome CW")
            #if self.parent.pstack.ProcessTypeRunning('MACRO_RECORDING'):
                #self.parent.startEventRecorder("DOME_CW")
        
    def OnMoveCWUp(self, event=None):
        self.tmrRotateCW.Stop()
        if self.parent.pstack.ProcessTypeRunning('MACRO_RECORDING'):
            if self.parent.StateObject.macros_vars["MACRO_EVENT_RECORD"]:
                self.parent.stopEventRecorder()
            else:
                self.parent.setSystemStatus(False)

        #self.parent.hwc.resetDataRange()
        self.dc_qin.put("DOME_STOP")
        
        event.Skip()

    def OnFocusInDown(self, event=None):
        self.tmrFocusIn.Start(DEFAULT_REPEAT_INTERVAL)
        event.Skip()

    def OnFocusInUp(self, event=None):
        self.tmrFocusIn.Stop()
        self.parent.hwc.resetControlRange()
        event.Skip()

    def OnFocusOutDown(self, event=None):
        self.tmrFocusOut.Start(DEFAULT_REPEAT_INTERVAL)
        event.Skip()

    def OnFocusOutUp(self, event=None):
        self.tmrFocusOut.Stop()
        self.parent.hwc.resetControlRange()
        event.Skip()

    def OnMoveNorthDown(self, event=None):
        if self.m_north == 0:
            self.dec_qin.put(("SPEED", self._slewtbl_dec[self.sldSlewSpeed.GetValue()]))
            self.dec_qin.put(("DI_NORTH", None))
            self.dec_qin.put(("MOVE", None))
            self.m_north = 1
        
        if event: event.Skip()

    def OnMoveNorthUp(self, event=None):
        self.dec_qin.put(("STOP", None))
        if not self.remote: self.lockUI(True)
            
        self.tmrCheckDecMotion.Start(200)
        self.m_north = 0
        
        if event: event.Skip()

    def OnMoveSouthDown(self, event=None):
        if self.m_south == 0:
            self.dec_qin.put(("SPEED", self._slewtbl_dec[self.sldSlewSpeed.GetValue()]))
            self.dec_qin.put(("DI_SOUTH", None))
            self.dec_qin.put(("MOVE", None))
            self.m_south = 1
        
        if event: event.Skip()

    def OnMoveSouthUp(self, event=None):
        self.dec_qin.put(("STOP", None))
        if not self.remote: self.lockUI(True)
        self.tmrCheckDecMotion.Start(200)
        self.m_south = 0
        
        if event: event.Skip()
        
    def OnMoveEastDown(self, event=None):
        if self.m_east == 0:
            self.ra_qin.put(("SPEED", self._slewtbl_ra[self.sldSlewSpeed.GetValue()]))
            self.ra_qin.put(("DI_EAST", None))
            self.ra_qin.put(("MOVE", None))
            self.m_east = 1
        
        if event: event.Skip()

    def OnMoveEastUp(self, event=None):
        self.ra_qin.put(("STOP", None))
        if not self.remote: self.lockUI(True)
        self.tmrCheckRAMotion.Start(200)
        self.m_east = 0
        
        if event: event.Skip()

    def OnMoveWestDown(self, event=None):
        if self.m_west == 0:
            self.ra_qin.put(("SPEED", self._slewtbl_ra[self.sldSlewSpeed.GetValue()]))
            self.ra_qin.put(("DI_WEST", None))
            self.ra_qin.put(("MOVE", None))
            self.m_west = 1
        
        if event: event.Skip()

    def OnMoveWestUp(self, event=None):
        self.ra_qin.put(("STOP", None))
        if not self.remote: self.lockUI(True)
        self.tmrCheckRAMotion.Start(200)
        self.m_west = 0
        
        if event: event.Skip()
    
    def StopTracking(self):
        self.ra_qin.put(("STOP_TRACK", None))
        self.cmdEnableTracking.SetValue(False)
        
    def OnEnableTracking(self, event=None):
        if self.cmdEnableTracking.GetValue() == True:
            self.ra_qin.put(("START_TRACK", None))
        if self.cmdEnableTracking.GetValue() == False:
            self.ra_qin.put(("STOP_TRACK", None))
            
        if event: event.Skip()
        
    def OnEnableRemote(self, event=None):
        if self.cmdEnableRemote.GetValue() == True:
            self.remote = True
            self.lockUI(True)
        if self.cmdEnableRemote.GetValue() == False:
            self.remote = False
            self.lockUI(False)
            
        if event: event.Skip()

    def OnKeyPress(self, event=None):
        event.Skip()

    # ==========================================================================
    # Timer Callbacks
    # ==========================================================================
    
    def CheckRAMotion(self, event=None):
        if not self.ra_qout.empty():
            if self.ra_qout.get() == 1:
                self.tmrCheckRAMotion.Stop()
                self.m_east = self.m_west = 0
                if not self.remote: self.lockUI(False)

    def CheckDecMotion(self, event=None):
        if not self.dec_qout.empty():
            if self.dec_qout.get() == 1:
                self.tmrCheckDecMotion.Stop()
                self.m_north = self.m_south = 0
                if not self.remote: self.lockUI(False)
            
    def OpenDome(self, event):
        self.parent.hwc.setControl(DOME_OPEN)

    def CloseDome(self, event):
        self.parent.hwc.setData(DOME_CLOSE)
        
    def RotateDomeCCW(self, event):
        self.parent.hwc.setData(MOVE_LEFT)

    def RotateDomeCW(self, event):
        #self.parent.hwc.setData(MOVE_RIGHT)
        pass

    def FocusIn(self, event):
        self.parent.hwc.setControl(FOCUS_IN)
        #print "Focus IN cannot be implimented on this hardware!"

    def FocusOut(self, event):
        self.parent.hwc.setControl(FOCUS_OUT)
        #print "Focus OUT cannot be implimented on this hardware!"

    def MoveNorth(self, event):
        self.parent.hwc.setData(TELESCOPE_NORTH)

    def MoveSouth(self, event):
        self.parent.hwc.setData(TELESCOPE_SOUTH)

    def MoveEast(self, event):
        self.parent.hwc.setData(TELESCOPE_EAST)

    def MoveWest(self, event):
        self.parent.hwc.setData(TELESCOPE_WEST)

    def Purge(self, event):
        self.parent.hwc.resetControlRange()
        self.parent.hwc.resetDataRange()
            
    def OnClose(self, event): # wxGlade: ObsControlPanel.<event_handler>
        #self.parent.StateObject.gui_vars["GUI_CTRL_COUNT"] -= 1
        self.Hide()
