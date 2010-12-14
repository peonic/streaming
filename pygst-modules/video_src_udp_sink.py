#!/usr/bin/env python
#
# streaming for 270grad
# by peter innerhofer

# builds n streams (default 4) from v4lsrc, encodes them (ffenc_mpeg4), and send them to a udpsink (default 127.0.0.1)

# command line input: 
#   's' = start/stops
#   'q' = quit

# OCS input:
#   message: /startstopstream, 0 or 1

# see notes.txt for encoder decision

##### mpeg4 enc ######

# gst-launch-0.10 -v v4l2src ! videoscale ! video/x-raw-yuv,width=640,height=480 ! videorate ! video/x-raw-yuv,framerate=25/1 !  ffmpegcolorspace ! ffenc_mpeg4 bitrate=1000000 ! rtpmp4vpay ! udpsink host=127.0.0.1 port=5000
# gst-launch -ve udpsrc port=5001 ! "application/x-rtp, media=(string)video, payload=(int)96, clock-rate=(int)90000, encoding-name=(string)MP4V-ES, profile-level-id=(string)1, payload=(int)96" ! rtpmp4vdepay ! "video/mpeg,width=640,height=480,framerate=25/1,mpegversion=4,systemstream=false" ! ffdec_mpeg4 ! queue ! xvimagesink

import sys, os
import socket, time
from simpleOSC import *
import pygst
pygst.require("0.10")
import gst
import gtk, pygtk, gobject
import basestreamingclass

class ChildStreaming(basestreamingclass.BaseStreaming):

  def __init__(self):
    print "childstream created"
    basestreamingclass.BaseStreaming.__init__(self)

  def init_pipeline(self):
    basestreamingclass.BaseStreaming.init_pipeline(self)
    print "init pipeline"

    for p_item in range(self.number_of_streams):
      self.pipeline_array.append(gst.Pipeline("pipeline%s" % p_item))

      source = gst.element_factory_make("v4l2src","vsource" + str(p_item)) 
      source.set_property("device", self.video_src[p_item])

      scaler = gst.element_factory_make("videoscale", "vscale")

      caps1 = gst.Caps(self.caps_raw_fullsize)
      filter1 = gst.element_factory_make("capsfilter", "filter")
      filter1.set_property("caps", caps1)

      rate = gst.element_factory_make("videorate", "vrate")

      conv = gst.element_factory_make("ffmpegcolorspace")

      encoder = gst.element_factory_make("ffenc_mpeg4", "ffenc_mpeg4_%s" % p_item)
      encoder.set_property("bitrate", self.bitrate)

      rtpmp4vpay = gst.element_factory_make("rtpmp4vpay", "rtpmp4vpay%s" % p_item)

      self.sink_array.append(gst.element_factory_make("udpsink", "udpsink%s" % p_item))
      self.sink_array[p_item].set_property("host", self.host)
      self.sink_array[p_item].set_property("port", self.baseport + p_item)

      # adding the pipleine elements and linking them together
      self.pipeline_array[p_item].add(source, scaler, rate, filter1, conv, encoder, rtpmp4vpay, self.sink_array[p_item])
      gst.element_link_many(source, scaler, rate, filter1, conv, encoder, rtpmp4vpay, self.sink_array[p_item])

      self.bus_array.append(self.pipeline_array[p_item].get_bus())
      self.bus_array[p_item].add_signal_watch()
      self.bus_array[p_item].connect("message",self.on_message)

  def run(self):
    print "initializing"
    self.running = "false"
    # init gtk for keyboard input
    #self.init_gtk()
    self.init_pipeline()
    # self.init_OSC()

    print "pipelines initialized, focus gtk window and press s for starting recording"
    # self.window.connect("key-press-event",self.on_window_key_press_event)

    self.StartStop()
    for p_item in range(1,self.number_of_streams):
      print "sink property:"
      print self.sink_array[p_item].get_pad('sink').get_property('caps')

    gobject.threads_init()
    self.mainloop = gobject.MainLoop()
    self.mainloop.run()
    print "exit"

m = ChildStreaming()
m.run()

