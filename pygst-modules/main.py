#!/usr/bin/env python
# by peter innerhofer
#
# streaming solution for "extended view stream" for the CoMeDia project

import sys, os
import ConfigParser
import socket, time
import oschandler, OSC
import pygst
pygst.require("0.10")
import gst
import gtk, pygtk, gobject
import gstreamerpipeline
import udp_src_to_filesink
import file_src_to_v4l2loopback
import video_src_udp_sink
import udp_src_to_v4l2loopback
import video_src_file_sink

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
    self.config = ConfigParser.ConfigParser()
    self.config.read("config.ini")
    # print self.config.sections()
    
    self.pipeline_array = []

  def init_OSC(self):    
    self.osc_server = oschandler.OSCHandler((self.config.get("OSC","ServerAddress"),self.config.getint("OSC","Port")))
    self.osc_server.addMsgHandler(self.config.get("OSC","StreamStart"),self.start_stop_stream)
    self.osc_server.addMsgHandler(self.config.get("OSC","CreatePipelineFromString"),self.create_pipeline_from_osc_string)
    self.osc_server.addMsgHandler(self.config.get("OSC","PrintCaps"),self.osc_print_caps)
    self.osc_server.start()

  def init_gtk(self):
    self.gtk_init = 1
    self.window = gtk.Window()
    self.window.connect("destroy", gtk.main_quit, "WM destroy")
    self.window.connect("key-press-event",self.on_window_key_press_event)
    self.window.show_all()

  def init_pipeline(self):
    # Create GStreamer Pipeline
    self.pipeline_array = []
    
    for p_item in range(self.config.getint("Common","NumberOfStreams")):
		print "stream init"
    #  self.create_pipeline(p_item)  

  def create_pipeline(self,p_item):
    print "parent create pipeline"

  def parse_pipeline(self,gst_pipeline_string):
    self.pipeline_array.append(gstreamerpipeline.Pipeline(self.config))
    self.pipeline_array[-1].create_pipeline_from_string(gst_pipeline_string)
    
  def create_pipeline_from_osc_string(self, addr, tags, data, source):
    print "\nrecieved data %s  \n" % data 
    for d in data:
      print d
    #self.parse_pipeline(data[0])
    
  def run(self):
    print "initializing Object"
    self.running = "false"
    self.init_pipeline()
    print self.config.get("Pipeline","VideoSrc2UdpSink")
    
    #self.parse_pipeline(self.config.get("Pipeline","VideoSrc2UdpSink"))
    
    #self.pipeline_array.append(udp_src_to_filesink.UDPSrcToFileSink(self.config))
    #self.pipeline_array[-1].create_pipeline(0)
    
    #self.pipeline_array.append(file_src_to_v4l2loopback.FileSrcToV4l2Loopback(self.config))
    #self.pipeline_array[-1].create_pipeline(0,"/videos/test.avi")
    
    #self.pipeline_array.append(video_src_udp_sink.VideoSrcToUDPSink(self.config))
    #self.pipeline_array[-1].create_pipeline(0)
    
    #self.pipeline_array.append(udp_src_to_v4l2loopback.UDPSrcToV4l2Loopback(self.config))
    #self.pipeline_array[-1].create_pipeline(0)
    
    self.pipeline_array.append(video_src_file_sink.VideoSrcToFileSink(self.config))
    self.pipeline_array[-1].create_pipeline(0)
    
    print "Pipeline('s) initialized"
    if self.config.getint("OSC","Init"):
	  self.init_OSC()
	
    self.ready()
    self.StartStop()
    
    if self.config.getint("GTK","Init"):
      print "GTK Window initialized"
      self.init_gtk()
      gtk.gdk.threads_init()
      gtk.main()
    else:
	  gobject.threads_init()
	  self.mainloop = gobject.MainLoop()
	  self.mainloop.run()
    print "exit"

  def start_stop_stream(self,addr, tags, data, source):
    print "received new osc msg from %s" % OSC.getUrlStr(source)
    print "with addr : %s" % addr
    print "typetags : %s" % tags
    print "the actual data is :%s" % data
    print "---"
    if 0 <= data[0] and data[0] <= 1:
      self.ready()
      self.StartStop()
   
  def StartStop(self):
    for p in self.pipeline_array:
      p.StartStop()
    
  def ready(self):
    for p in self.pipeline_array:
      p.ready()
      
  def OnQuit(self, widget):
    self.quit()

  def quit(self):
    for p in self.pipeline_array:
      p.stop()
      time.sleep(1)
      p.quit()
    if self.config.getint("OSC","init"):
      self.osc_server.close()
    if self.config.getint("GTK","Init"):
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
      
  def osc_print_caps(self,addr, tags, data, source):
	  self.pipeline_array[-1].print_caps()

try :
	print "\ncreating Streaming Server \n\npress Ctrl-C to exit\n"
	m = BaseStreaming()
	m.run()
except KeyboardInterrupt :
	m.quit()

