#!/usr/bin/env python
# by peter innerhofer
#
# streaming solution for "extended view stream" for the CoMeDia project

# Description: 
# builds n streams (default 4) from v4l2src, encodes them with xvid (ffenc_mpeg4), and send them via udp to a host (default 127.0.0.1 port=5000)
# second pipeline will recieve the stream, decode it, and forward it to a v4l2loopback device
# 
# command line input: 
#   's' = start/stop
#   'q' = quit
#
# IMPORTANT: load v4l2loopback kernel module
#   sudo modprobe v4l2loopback devices=10 
#
# OCS input:
#   message: /startstopstream, 0 or 1
#
# see notes.txt for encoder decision
#

import sys, os
import socket, time
from simpleOSC import *
import pygst
pygst.require("0.10")
import gst
import gtk, pygtk, gobject


class BaseStreaming:
  """
  Base Streaming Class:

  Template Class for Gstreamer application. Basic functions for controlling, message handling 
  pipeline parsing and viewing.

  Controlling the pipeline can be done with 3 diffrent methods. 
    * commandline input
    * keyboard input in the gtk window
    * send OSC messages

  until now only basic controll function are implemented:
    's' for start/stop (OSC message '1' or '0')
    'q' for quit
    'f' for fullscreen (only gtk applications)

  OSC: port: 7780 messagestring: /startstopstream
  TODO: close udp socket!!!!

  Message Handling:
  it is very important that basic message handling functions are implemented, 
  specially for writing files on hdd. a multiplexer (z.b avimux) or the filesink need
  a EOS (EndOfStream) message for closing the files properly.

  pipeline can be parsed as they are in commandline 
  """

  def __init__(self):
    # all common init's:
    self.number_of_streams = 1
    self.gtk_init = 0
    self.osc_baseport = 7780
    self.osc_message_string = "/startstopstream"

    # for pipes with video sources and video sinks
    self.video_src = ["/dev/video0", "/dev/video1", "/dev/video2", "/dev/video3"]
    self.video_sink_devs = ["/dev/video1", "/dev/video5", "/dev/video6", "/dev/video7"]

    # for pipelines with recorder & player
    self.file_path = ["videos/", "videos/", "videos/", "videos/"]
    self.file_names = ["recorded_camid_0_nr0.avi", "recorded_camid_1_nr0.avi", "recorded_camid_2_nr0.avi", "recorded_camid_3_nr0.avi"]
    self.record_id = 0

    # for pipelines with udp sinks
    self.host = "127.0.0.1"
    self.baseport = 5000
    if (len(sys.argv) > 1):
      if len(sys.argv[1]) > 5 :
        self.host = str(sys.argv[1])
        print "host arg inputed"
    print "host: " + str(self.host)

    # for pipelines with mpgeg encoding and decoding
    self.bitrate = 90000 

    #self.caps_app = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)MP4V-ES, profile-level-id=(string)1, config=(string)000001b001000001b58913000001000000012000c48d8800cd0a041e1463000001b24c61766335322e37322e32, payload=(int)96, ssrc=(uint)3644377598, clock-base=(uint)861502242, seqnum-base=(uint)23879"
    self.caps_mpeg4 = "video/mpeg, width=320, height=240,framerate=25/1,mpegversion=4,systemstream=false "
    self.caps_raw_fullsize = "video/x-raw-yuv, width=640, height=480,framerate=25/1"
    self.caps_raw_halfsize = "video/x-raw-yuv, width=320, height=240,framerate=25/1"

    print "parrent created"

  def init_OSC(self):    
    initOSCServer('', self.osc_baseport)
    # callback function, wenn recieving osc message
    setOSCHandler(self.osc_message_string, self.start_stop_stream)

  def init_gtk(self):
    self.gtk_init = 1
    self.window = gtk.Window()
    self.window.connect("destroy", gtk.main_quit, "WM destroy")
    self.window.connect("key-press-event",self.on_window_key_press_event)
    self.window.show_all()
    gtk.gdk.threads_init()
    gtk.main()

  def init_pipeline(self):
    # Create GStreamer Pipeline
    self.pipeline_array = []
    self.sink_array = []
    self.bus_array = []
    for p_item in range(self.number_of_streams):
      self.create_pipeline(p_item)  

  def create_pipeline(self,p_item):
    print "parent create pipeline"

  def parse_pipeline(self,gst_pipeline_string):
    self.pipeline_array.append(gst.parse_launch(gst_pipeline_string))
    self.bus_array.append(self.pipeline_array[-1].get_bus())
    self.bus_array[-1].add_signal_watch()
    self.bus_array[-1].connect("message",self.on_message)

  def run(self):

    print "initializing"
    self.running = "false"
    # init gtk for keyboard input
    # self.init_gtk()
    # self.init_pipeline()
    # self.init_OSC()
    
    gobject.threads_init()
    self.mainloop = gobject.MainLoop()
    self.mainloop.run()
    print "exit"

  def on_message(self, bus, message):
    t = message.type
    # print str(bus.get_name()) + ": message received, type: " + str(t)
    if t == gst.MESSAGE_EOS:
      print "received EnOffStream(EOS) signal from bus %s" % bus.get_name()
      for p_item in range(1,self.number_of_streams):
        b = self.pipeline_array[p_item].get_bus()
        print "received EnOffStream(EOS) signal, current pipeline bus %s" % b.get_name()
        if b.get_name() == bus.get_name():
          print "received EnOffStream(EOS) signal, pipeline %s will stop" % p_item
          self.pipeline_array[p_item].set_state(gst.STATE_NULL)
    elif t == gst.MESSAGE_ERROR:
      err, debug = message.parse_error()
      print "Error: %s" % err, debug
      for p_item in range(1,self.number_of_streams):
        self.pipeline_array[p_item].set_state(gst.STATE_NULL)
    elif t == gst.MESSAGE_WARNING:
      err, debug = message.parse_warning()
      print "Warning: %s" % err, debug

  def start_stop_stream(self,addr, tags, data, source):
    print "---"
    print "received new osc msg from %s" % getUrlStr(source)
    print "with addr : %s" % addr
    print "typetags : %s" % tags
    print "the actual data is :%s" % data
    print "---"
    if 0 <= data[0] and data[0] <= 1:
      self.StartStop()
   
  def StartStop(self):
    if self.running == "false":
      self.running = "true"
      for p_item in range(self.number_of_streams):
        print "set pipeline %s to play" % p_item
        self.pipeline_array[p_item].set_state(gst.STATE_PLAYING)
        print "state: %s" % self.pipeline_array[p_item].get_state()
        print "caps : %s" % self.sink_array[p_item].get_pad('sink').get_property('caps')
    else:
      self.running = "false"
      self.record_id += 1
      print "stream stopped"
      for p_item in range(self.number_of_streams):
        print "will send EOS to src element: vsource" + str(p_item )
	if self.pipeline_array[p_item].get_by_name("vsource" + str(p_item)).send_event(gst.event_new_eos()):
          print "EOS event sucessfully send"
        else:
          print "EOS event NOT send, try to send it to pipeline"
          self.pipeline_array[p_item].send_event(gst.event_new_eos())

  def OnQuit(self, widget):
    for p_item in range(self.number_of_streams):
      if self.pipeline_array[p_item].get_state() == gst.STATE_PLAYING:
        self.pipeline_array[p_item].set_state(gst.STATE_NULL)
      self.bus_array[p_item].remove_signal_watch()
    if self.gtk_init:
      gtk.main_quit()
    else:
      self.mainloop.quit()

  def on_window_key_press_event(self,window,event):
    print event.state
    print event.keyval
    if event.keyval == 115:
      self.StartStop()
    if event.keyval == 102:
      self.Fullscreen()
    if event.keyval == 113:
      self.OnQuit(self.window)


