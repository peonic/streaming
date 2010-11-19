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
#import pygtk, gtk

class Main:

  def __init__(self):
    self.number_of_streams = 1 # for the range so its from 0 to 11 = 12 streams
    self.recorded_stream_count = 0 # in filename

    self.videosink = "v4l2loopback"
    self.videosink_devs = ["/dev/video0", "/dev/video1", "/dev/video2"]
    
    baseport = 5000
    
    # osc
    initOSCServer('', 7779)
    # callback function, wenn recieving osc message
    setOSCHandler("/startstopstream", self.start_stop_stream)


    # Create GStreamer Pipeline
    self.pipeline_array = []
    self.sink_array = []
    for p_item in range(self.number_of_streams):
      self.pipeline_array.append(gst.Pipeline("mypipeline%s" % p_item))

      source = gst.element_factory_make("udpsrc","udp_source") 
      source.set_property("port", baseport + p_item)

      # caps = gst.Caps("video/mpeg, width=(int)640, height=(int)480, framerate=(fraction)25/1, mpegversion=(int)4, systemstream=(boolean)false")
      caps = gst.Caps("application/x-rtp, media=(string)video, payload=(int)96, clock-rate=(int)90000, encoding-name=(string)MP4V-ES, profile-level-id=(string)1, payload=(int)96") #config=(string)000001b001000001b58913000001000000012000c48d8800cd14043c1463000001b24c61766335322e37322e32,
      filter = gst.element_factory_make("capsfilter", "filter1")
      filter.set_property("caps", caps)

      rtpmp4vdepay = gst.element_factory_make("rtpmp4vdepay", "rtpmp4vpay%s" % p_item)
      queuea = gst.element_factory_make("queue")

      caps2 = gst.Caps("video/mpeg,width=320,height=240,framerate=25/1,mpegversion=4,systemstream=false")
      filter2 = gst.element_factory_make("capsfilter", "filter2")
      filter2.set_property("caps", caps2)
      
      decoder = gst.element_factory_make("ffdec_mpeg4", "decoder%s" % p_item)
      queueb = gst.element_factory_make("queue")

      self.sink_array.append(gst.element_factory_make("v4l2loopback", "v4l2loopback%s" % p_item))
      self.sink_array[p_item].set_property("device",self.videosink_devs[p_item])

      # adding the pipleine elements and linking them together
      self.pipeline_array[p_item].add(source, filter,rtpmp4vdepay, filter2, queuea, decoder, queueb, self.sink_array[p_item])
      gst.element_link_many(source, filter,rtpmp4vdepay, filter2, queuea, decoder, queueb, self.sink_array[p_item])

      self.pipeline_array[p_item].set_state(gst.STATE_PLAYING)

    # setting keyboard events, setting fullscreen
    #self.window.connect("key-press-event",self.on_window_key_press_event)
    # self.sink_array[0].set_xwindow_id(self.da.window.xid)
    #self.running = "false"
    #self.window.fullscreen()
    #self.is_fullscreen = "false"

  def on_window_key_press_event(self,window,event):
    print event.state
    print event.keyval
    if event.keyval == 115:
      self.StartStop()
    if event.keyval == 102:
      self.Fullscreen()
    if event.keyval == 113:
      self.OnQuit(self.window)
    if 49 <= event.keyval and event.keyval <= 49 + self.number_of_streams:
      self.switch_display_stream(event.keyval % 49 )

  # this function states all streams to STATE_NULL and only the selected one to STATE_PLAYING
  #def switch_display_stream(self,nr):
    #self.sink_array[nr].set_xwindow_id(self.da.window.xid)

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
      print "play"
      self.running = "true"
      for i in range(self.number_of_streams):
        self.recorded_stream_count += 1
        # self.sink_array[i].set_property("location", self.location_path + self.filename + "_stream" + str(i) + "_" + str(self.recorded_stream_count) + ".avi")
        self.sink_array[i].set_property("append",1)
        self.pipeline_array[i].set_state(gst.STATE_PLAYING)
    else:
      print "stop"
      self.running = "false"
      for i in range(self.number_of_streams):
        self.pipeline_array[i].set_state(gst.STATE_READY)
        # self.pipeline_array[i].set_state(gst.STATE_NULL)

  def OnQuit(self, widget):
    for i in range(self.number_of_streams):
      self.pipeline_array[i].set_state(gst.STATE_NULL)
    # gtk.main_quit()
    


Main()
loop = gobject.MainLoop()
loop.run()
#gtk.gdk.threads_init()
#gtk.main()
