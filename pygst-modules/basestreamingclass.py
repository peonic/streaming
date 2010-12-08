#!/usr/bin/env python
# streaming for 270grad
# by peter innerhofer
#
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
##### gst-lauch pipelines ######
#
# encoding:
# gst-launch -vvv v4l2src ! videoscale ! videorate ! video/x-raw-yuv, width=640, height=480, framerate=25/1 ! ffmpegcolorspace ! ffenc_mpeg4 ! rtpmp4vpay ! udpsink host=127.0.0.1 port=5000
#
# forwarding:
# gst-launch -vvv udpsrc port=5000 ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)MP4V-ES, profile-level-id=(string)1, config=(string)000001b001000001b58913000001000000012000c48d8800cd14043c1463000001b24c61766335322e37322e32, payload=(int)96, ssrc=(uint)903112079, clock-base=(uint)1095309658, seqnum-base=(uint)64180 ! rtpmp4vdepay ! ffdec_mpeg4 ! ffmpegcolorspace ! v4l2loopback
#
# Anzeige:
# gst-launch -vvv v4l2src device=/dev/video1 ! xvimagesink

import sys, os
import socket, time
from simpleOSC import *
import pygst
pygst.require("0.10")
import gst
import gtk, pygtk, gobject


class BaseStreaming:

  def __init__(self):
    self.number_of_streams = 1 # for the range so its from 0 to 11 = 12 streams

    # TODO: make a script with makes devices by id
    self.video_sink_devs = ["/dev/video1", "/dev/video5", "/dev/video6", "/dev/video7"]
    self.file_path = ["videos/", "videos/", "videos/", "videos/"]
    self.record_id = 0
    self.host = "10.0.0.7"
    self.baseport = 5000
    self.bitrate = 90000 
    if (len(sys.argv) > 1):
      if len(sys.argv[1]) > 5 :
        self.host = str(sys.argv[1])
        print "host arg inputed"
    print "host: " + str(self.host) + " bitrate: " + str(self.bitrate)

    self.caps_string1 = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)MP4V-ES, profile-level-id=(string)1, config=(string)000001b001000001b58913000001000000012000c48d8800cd0a041e1463000001b24c61766335322e37322e32, payload=(int)96, ssrc=(uint)3644377598, clock-base=(uint)861502242, seqnum-base=(uint)23879"

    print "caps: %s" % self.caps_string1
    self.caps_string2 = "video/mpeg, width=320, height=240,framerate=25/1,mpegversion=4,systemstream=false "
    self.caps_string3 = "video/x-raw-yuv, width=320, height=240,framerate=25/1"

  def init_OSC(self):    
    # osc
    initOSCServer('', 7780)
    # callback function, wenn recieving osc message
    setOSCHandler("/startstopstream", self.start_stop_stream)

  def init_gtk(self):
    self.window = gtk.Window()
    self.window.connect("destroy", gtk.main_quit, "WM destroy")
    self.window.connect("key-press-event",self.on_window_key_press_event)
    self.window.show_all()

  def init_pipeline(self):
    # Create GStreamer Pipeline
    self.pipeline_array = []
    self.sink_array = []
    self.bus_array = []
    for p_item in range(self.number_of_streams):
      self.pipeline_array.append(gst.Pipeline("pipeline%s" % p_item))

      source = gst.element_factory_make("udpsrc","udp_source") 
      source.set_property("port", self.baseport + p_item)

      caps1 = gst.Caps(self.caps_string1)
      filter1 = gst.element_factory_make("capsfilter", "filter1")
      filter1.set_property("caps", caps1)

      rtpmp4vdepay = gst.element_factory_make("rtpmp4vdepay", "rtpmp4vpay%s" % p_item)
      
      decoder = gst.element_factory_make("ffdec_mpeg4", "decoder%s" % p_item)

      conv = gst.element_factory_make("ffmpegcolorspace", "ffmpegcolorspace%s" % p_item)

      self.sink_array.append(gst.element_factory_make("v4l2loopback", "v4l2loopback%s" % p_item))
      self.sink_array[p_item].set_property("device",self.video_sink_devs[p_item])

      # adding the pipleine elements and linking them together
      self.pipeline_array[p_item].add(source, filter1, rtpmp4vdepay, decoder, conv, self.sink_array[p_item])
      gst.element_link_many(source, filter1,rtpmp4vdepay, decoder, conv, self.sink_array[p_item])

      self.bus_array.append(self.pipeline_array[p_item].get_bus())
      self.bus_array[p_item].add_signal_watch()
      self.bus_array[p_item].connect("message",self.on_message)

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
    #elif t == gst.MESSAGE_STATE_CHANGED:
    #  oldstate, newstate, pending = message.parse_state_changed()
    #  print "state changed: %s %s -> %s" % (oldstate, newstate, pending)
        

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
        print "getting state"
        #print self.pipeline_array[p_item].get_state()
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
    #gtk.main_quit()
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
    if 49 <= event.keyval and event.keyval <= 49 + self.number_of_streams:
      self.switch_display_stream(event.keyval % 49 )


