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

  def __init__(self):
    print "childstream created"
    basestreamingclass.BaseStreaming.__init__(self)
    self.caps_app = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)MP4V-ES, profile-level-id=(string)1, config=(string)000001b001000001b58913000001000000012000c48d8800cd14043c1463000001b24c61766335322e37322e32, payload=(int)96, ssrc=(uint)2908696696, clock-base=(uint)1768976456, seqnum-base=(uint)6682"


  def init_pipeline(self):
    basestreamingclass.BaseStreaming.init_pipeline(self)
    print "init pipeline"
    # Create GStreamer Pipeline
    for p_item in range(self.number_of_streams):
      self.pipeline_array.append(gst.Pipeline("pipeline%s" % p_item))

      source = gst.element_factory_make("udpsrc","vsource") 
      source.set_property("port", self.baseport + p_item)

      caps1 = gst.Caps(self.caps_app)
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
    self.init_pipeline()
    # self.init_OSC()

    print "pipelines initialized, focus gtk window and press s for starting recording"

    self.StartStop()
    for p_item in range(self.number_of_streams):
      print self.pipeline_array[0].get_by_name("vsource").get_pad('src').get_property('caps')
      print "sink property:"
      print self.sink_array[p_item].get_pad('sink').get_property('caps')
    
    gobject.threads_init()
    self.mainloop = gobject.MainLoop()
    self.mainloop.run()
    print "exit"

#
# enter into a mainloop
#
#sys.path.append('')
m = ChildStreaming()
m.run()


