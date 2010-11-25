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

import sys, os
import socket, time
from simpleOSC import *
import pygst
pygst.require("0.10")
import gst
import gtk, pygtk, gobject


class Main:

  def __init__(self):
    self.number_of_streams = 1 # for the range so its from 0 to 11 = 12 streams

    # TODO: make a script with makes devices by id
    self.video_src = ["/dev/video0", "/dev/video1", "/dev/video2", "/dev/video3"]
    self.file_path = ["videos/", "videos/", "videos/", "videos/"]
    self.record_id = 0
    host = "127.0.0.1"
    if (len(sys.argv) > 1):
      if len(sys.argv[1]) > 5 :
        host = str(sys.argv[1])
    print host
    baseport = 5000
    bitrate = 1000000 

  def init_OSC(self):    
    # osc
    initOSCServer('', 7780)
    # callback function, wenn recieving osc message
    setOSCHandler("/startstopstream", self.start_stop_stream)

  def init_gtk(self):
    self.window = gtk.Window()
    self.window.connect("destroy", gtk.main_quit, "WM destroy")
    self.window.show_all()

  def init_pipeline(self):
    # Create GStreamer Pipeline
    self.pipeline_array = []
    self.sink_array = []
    self.bus_array = []
    for p_item in range(self.number_of_streams):
      self.pipeline_array.append(gst.Pipeline("mypipeline%s" % p_item))

      source = gst.element_factory_make("v4l2src","vsource" + str(p_item)) 
      source.set_property("device", self.video_src[p_item])

      scaler = gst.element_factory_make("videoscale", "vscale")
      #scaler.set_property("method", 1)

      caps1 = gst.Caps("video/x-raw-yuv, width=640, height=480,framerate=25/1")
      filter1 = gst.element_factory_make("capsfilter", "filter1")
      filter1.set_property("caps", caps1)

      rate = gst.element_factory_make("videorate", "vrate")

      conv = gst.element_factory_make("ffmpegcolorspace")

      avimux = gst.element_factory_make("avimux", "avimuxer_%s" % p_item)
      queueb = gst.element_factory_make("queue")

      self.sink_array.append(gst.element_factory_make("filesink", "filesink%s" % p_item))
      self.sink_array[p_item].set_property("location", self.file_path[p_item] + "recorded_camid_" + str(p_item) + "_nr" + str(self.record_id) + ".avi")

      # adding the pipleine elements and linking them together
      self.pipeline_array[p_item].add(source, scaler, rate, filter1, conv, avimux, self.sink_array[p_item])
      gst.element_link_many(source, scaler, rate, filter1, conv, avimux, self.sink_array[p_item])

      self.bus_array.append(self.pipeline_array[p_item].get_bus())
      self.bus_array[p_item].add_signal_watch()
      self.bus_array[p_item].connect("message",self.on_message)

  def run(self):
    print "ready"
    self.running = "true"
    self.init_gtk()
    self.init_pipeline()
    self.init_OSC()

    # self.mainloop = gobject.MainLoop(is_running=True)
    for p_item in range(self.number_of_streams):
      print "set pipeline %s to play" % p_item
      self.pipeline_array[p_item].set_state(gst.STATE_PLAYING)

    print "stream started"
    self.window.connect("key-press-event",self.on_window_key_press_event)

  def on_message(self, bus, message):
    t = message.type
    print str(bus.get_name()) + ": message received, type: " + str(t)
    if t == gst.MESSAGE_EOS:
      for p_item in range(1,self.number_of_streams):
        b = self.pipeline_array[p_item].get_bus()
        if b.get_name() == bus.get_name():
          self.pipeline_array[p_item].set_state(gst.STATE_NULL)
    elif t == gst.MESSAGE_ERROR:
      for p_item in range(1,self.number_of_streams):
        self.pipeline_array[p_item].set_state(gst.STATE_NULL)
        

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
        self.sink_array[p_item].set_property("location", self.file_path[p_item] + "recorded_camid_" + str(p_item) + "_nr" + str(self.record_id) + ".avi")
        self.pipeline_array[p_item].set_state(gst.STATE_PLAYING)
    else:
      self.running = "false"
      self.record_id += 1
      print "stream stopped"
      for p_item in range(self.number_of_streams):
        print "will send EOS to src element: vsource" + str(p_item ) + " device: " + self.video_src[p_item]
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
    gtk.main_quit()

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


#
# enter into a mainloop
#

m = Main()
m.run()

gtk.gdk.threads_init()
gtk.main()

# loop = gobject.MainLoop()
# loop.run()

# sys.exit()
#loop = gobject.MainLoop()
#gobject.threads_init()
#Main()
#
