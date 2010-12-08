#!/usr/bin/env python
# -*- coding: utf-8 -*-

# streaming for 270grad
# by peter innerhofer

# constructs 4 stream, ether to hdd or udpsink

# keyboard commands: 
#   's' = start/stop
#   'f' = full-/unfullscreen
#   'q' = quit

# see the DrawingAreaFactory for arranig the video windows

# currently jpegenc is used so put this pipeline in script

##### mpeg4 enc ######

# gst-launch-0.10 -v v4l2src ! videoscale ! video/x-raw-yuv,width=640,height=480 ! videorate ! video/x-raw-yuv,framerate=25/1 !  ffmpegcolorspace ! ffenc_mpeg4 bitrate=1000000 ! udpsink host=127.0.0.1 port=5000
# gst-launch-0.10 -v udpsrc port=5000 caps='video/mpeg, width=(int)640, height=(int)480, framerate=(fraction)25/1, mpegversion=(int)4, systemstream=(boolean)false' ! queue ! tee name=t t. ! queue !  ffdec_mpeg4 ! queue ! xvimagesink t. ! queue ! muxer.  mpegtsmux name=muxer ! filesink location="test_mpegtsmux.ts"

import sys, os
import socket, time
from simpleOSC import *
import pygst
pygst.require("0.10")
import gst
import gobject
import pygtk, gtk

class Main:

  def __init__(self):
    self.number_of_streams = 1 # for the range so its from 0 to 11 = 12 streams

    self.videosink = "v4l2loopback"
    self.videosink_devs = ["/dev/video10", "/dev/video11"]
    self.videosink = "filesink"
    self.location_path = "/videos/"
    self.filename = "test" # 
    
    baseport = 5000
    
    # osc
    initOSCServer('', 7779)
    # callback function, wenn recieving osc message
    setOSCHandler("/startstopstream", self.start_stop_stream)

    #GUI
    self.window = gtk.Window()
    self.window.set_title("Video-Player")
    self.window.set_default_size(640, 480)
    self.window.connect("destroy", gtk.main_quit, "WM destroy")
    
    self.da = gtk.DrawingArea()
    self.vbox = gtk.VBox()
    self.vbox.pack_start(self.da)

    self.window.add(self.vbox)
    self.window.show_all()    

    # Create GStreamer Pipeline
    self.pipeline_array = []
    self.sink_array = []
    for p_item in range(self.number_of_streams):
      self.pipeline_array.append(gst.Pipeline("mypipeline%s" % p_item))

      source = gst.element_factory_make("udpsrc","udp_source") 
      source.set_property("port", baseport + p_item)

      queue = gst.element_factory_make("queue")
      caps = gst.Caps("video/mpeg, width=(int)640, height=(int)480, framerate=(fraction)25/1, mpegversion=(int)4, systemstream=(boolean)false")
      filter = gst.element_factory_make("capsfilter", "filter1")
      filter.set_property("caps", caps)

      conv = gst.element_factory_make("ffmpegcolorspace")

      decoder = gst.element_factory_make("ffdec_mpeg4", "ffenc_mpeg4_%s" % p_item)

      self.sink_array.append(gst.element_factory_make("xvimagesink", "xvimagesink%s" % p_item))

      # adding the pipleine elements and linking them together
      self.pipeline_array[p_item].add(source, queue, filter, decoder, conv, self.sink_array[p_item])
      gst.element_link_many(source, queue, filter, decoder, conv, self.sink_array[p_item])

    # setting keyboard events, setting fullscreen
    #self.window.fullscreen()
    self.sink_array[0].set_xwindow_id(self.da.window.xid)
    self.running = "true"
    self.is_fullscreen = "true"

    print "play"
    self.running = "true"
    for i in range(self.number_of_streams):
      self.pipeline_array[i].set_state(gst.STATE_PLAYING)
   
  def StartStop(self):
    if self.running == "false":
      print "play"
      self.running = "true"
      for i in range(self.number_of_streams):
        self.pipeline_array[i].set_state(gst.STATE_PLAYING)
    else:
      print "play"
      self.running = "false"
      for i in range(self.number_of_streams):
        self.pipeline_array[i].set_state(gst.STATE_READY)


Main()
gtk.gdk.threads_init()
gtk.main()
