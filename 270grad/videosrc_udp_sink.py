#!/usr/bin/env python
#
# streaming for 270grad
# by peter innerhofer

# builds n streams (default 4) from v4lsrc, encodes them (ffenc_mpeg4), and send them to a udpsink (default 127.0.0.1)

# command line input: 
#   's' = start/stop
#   'q' = quit

# OCS input:
#   message: /startstopstream, 0 or 1

# see notes.txt for encoder decision

##### mpeg4 enc ######

# gst-launch-0.10 -v v4l2src ! videoscale ! video/x-raw-yuv,width=640,height=480 ! videorate ! video/x-raw-yuv,framerate=25/1 !  ffmpegcolorspace ! ffenc_mpeg4 bitrate=1000000 ! udpsink host=127.0.0.1 port=5000
# gst-launch-0.10 -v udpsrc port=5000 caps='video/mpeg, width=(int)640, height=(int)480, framerate=(fraction)25/1, mpegversion=(int)4, systemstream=(boolean)false' ! queue ! tee name=t t. ! queue !  ffdec_mpeg4 ! queue ! xvimagesink t. ! queue ! muxer.  mpegtsmux name=muxer ! filesink location="test_mpegtsmux.ts"

import sys, os, threading
import socket, time
from simpleOSC import *
import pygst
pygst.require("0.10")
import gst
import gobject

class Main:

  def __init__(self):
    self.number_of_streams = 3 # for the range so its from 0 to 11 = 12 streams

    # TODO: make a script with makes devices by id
    self.video_src = ["/dev/video0", "/dev/video1", "/dev/video2", "/dev/video3"]
    host = "127.0.0.1"
    if (len(sys.argv) > 1):
      if len(sys.argv[1]) > 5 :
        host = str(sys.argv[1])
    print host
    baseport = 5000
    bitrate = 1000000
    
    # osc
    initOSCServer('', 7780)
    # callback function, wenn recieving osc message
    setOSCHandler("/startstopstream", self.start_stop_stream)

    #self.window = gtk.Window()
    #self.window.connect("destroy", gtk.main_quit, "WM destroy")
    #self.window.show_all()

    # Create GStreamer Pipeline
    self.pipeline_array = []
    self.sink_array = []
    for p_item in range(self.number_of_streams):
      self.pipeline_array.append(gst.Pipeline("mypipeline%s" % p_item))

      source = gst.element_factory_make("v4l2src","vsource") 
      source.set_property("device", self.video_src[p_item])

      scaler = gst.element_factory_make("videoscale", "vscale")
      #scaler.set_property("method", 1)

      caps1 = gst.Caps("video/x-raw-yuv, width=640, height=480,framerate=25/1")
      filter1 = gst.element_factory_make("capsfilter", "filter1")
      filter1.set_property("caps", caps1)

      rate = gst.element_factory_make("videorate", "vrate")

      conv = gst.element_factory_make("ffmpegcolorspace")

      encoder = gst.element_factory_make("ffenc_mpeg4", "ffenc_mpeg4_%s" % p_item)
      encoder.set_property("bitrate", bitrate)

      rtpmp4vpay = gst.element_factory_make("rtpmp4vpay", "rtpmp4vpay%s" % p_item)

      self.sink_array.append(gst.element_factory_make("udpsink", "udpsink%s" % p_item))
      self.sink_array[p_item].set_property("host", host)
      self.sink_array[p_item].set_property("port", baseport + p_item)

      # adding the pipleine elements and linking them together
      self.pipeline_array[p_item].add(source, scaler, rate, filter1, conv, encoder, rtpmp4vpay, self.sink_array[p_item])
      gst.element_link_many(source, scaler, rate, filter1, conv, encoder, rtpmp4vpay, self.sink_array[p_item])


  def run(self):
    print "ready"
    self.running = "false"

    # self.mainloop = gobject.MainLoop(is_running=True)
    for i in range(self.number_of_streams):
      self.pipeline_array[i].set_state(gst.STATE_PLAYING)

    # input_thread = InputThread(self)
    # input_thread.start()
    print "exit2"

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
        self.pipeline_array[i].set_state(gst.STATE_PLAYING)
    else:
      print "ready"
      self.running = "false"
      for i in range(self.number_of_streams):
        self.pipeline_array[i].set_state(gst.STATE_READY)

  def OnQuit(self, widget):
    for i in range(self.number_of_streams):
      self.pipeline_array[i].set_state(gst.STATE_NULL)
    # mainloop.quit()

#
# enter into a mainloop
#
m = Main()
m.run()
loop = gobject.MainLoop()
loop.run()

sys.exit()
#loop = gobject.MainLoop()
#gobject.threads_init()
#Main()
#

