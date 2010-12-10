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
import basestreamingclass

class ChildStreaming(basestreamingclass.BaseStreaming):

  def init_pipeline(self):
    # Create GStreamer Pipeline
    self.pipeline_array = []
    self.sink_array = []
    self.bus_array = []
    for p_item in range(self.number_of_streams):
      self.pipeline_array.append(gst.element_factory_make("playbin2", "playbin%s" % p_item))
      self.pipeline_array[p_item].set_property("uri", "file://" + str(os.getcwd()) + self.file_path[0] + self.file_names[p_item])      

      self.sink_array.append(gst.element_factory_make("v4l2loopback", "v4l2loopback%s" % p_item))
      self.sink_array[p_item].set_property("device",self.video_sink_devs[p_item])

      self.pipeline_array[p_item].set_property("video-sink", self.sink_array[p_item])

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
      #self.record_id += 1
      print "stream stopped"
      #for p_item in range(self.number_of_streams):
        #print "will send EOS to src element: vsource" + str(p_item )
	#if self.pipeline_array[p_item].get_by_name("vsource" + str(p_item)).send_event(gst.event_new_eos()):
        #  print "EOS event sucessfully send"
        #else:
        #  print "EOS event NOT send, try to send it to pipeline"
        #  self.pipeline_array[p_item].send_event(gst.event_new_eos())

m = ChildStreaming()
m.run()

