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

# gst-launch-0.10 -v v4l2src ! videoscale ! video/x-raw-yuv,width=640,height=480 ! videorate ! video/x-raw-yuv,framerate=25/1 !  ffmpegcolorspace ! ffenc_mpeg4 bitrate=1000000 ! rtpmp4vpay ! udpsink host=127.0.0.1 port=5000
# gst-launch -ve udpsrc port=5001 ! "application/x-rtp, media=(string)video, payload=(int)96, clock-rate=(int)90000, encoding-name=(string)MP4V-ES, profile-level-id=(string)1, payload=(int)96" ! rtpmp4vdepay ! "video/mpeg,width=640,height=480,framerate=25/1,mpegversion=4,systemstream=false" ! ffdec_mpeg4 ! queue ! xvimagesink

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
    self.host = "10.0.0.7"
    self.baseport = 5000
    self.bitrate = 90000 
    if (len(sys.argv) > 1):
      if len(sys.argv[1]) > 5 :
        self.host = str(sys.argv[1])
    print "host: " + str(self.host) + " bitrate: " + str(self.bitrate)
    self.caps_string = "video/x-raw-yuv, width=320, height=240,framerate=25/1"

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
      self.pipeline_array.append(gst.Pipeline("pipeline%s" % p_item))

      source = gst.element_factory_make("v4l2src","vsource" + str(p_item)) 
      source.set_property("device", self.video_src[p_item])

      scaler = gst.element_factory_make("videoscale", "vscale")

      caps1 = gst.Caps(self.caps_string)
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
    self.init_gtk()
    self.init_pipeline()
    # self.init_OSC()

    print "pipelines initialized, focus gtk window and press s for starting recording"
    self.window.connect("key-press-event",self.on_window_key_press_event)

    self.StartStop()

  def on_message(self, bus, message):
    t = message.type
    print str(bus.get_name()) + ": message received, type: " + str(t)
    if t == gst.MESSAGE_EOS:
      for p_item in range(1,self.number_of_streams):
        b = self.pipeline_array[p_item].get_bus()
        if b.get_name() == bus.get_name():
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

