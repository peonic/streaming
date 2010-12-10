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
import basestreamingclass

class ChildStreaming(basestreamingclass.BaseStreaming):


  def create_pipeline(self,p_item):
    self.pipeline_array.append(gst.Pipeline("pipeline%s" % p_item))

    source = gst.element_factory_make("v4l2src","vsource" + str(p_item)) 
    source.set_property("device", self.video_src[p_item])

    scaler = gst.element_factory_make("videoscale", "vscale")

    caps1 = gst.Caps(self.caps_string)
    filter1 = gst.element_factory_make("capsfilter", "filter")
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
    print "initializing"
    self.running = "false"
    # init gtk for keyboard input
    self.init_gtk()
    self.init_pipeline()
    # self.init_OSC()

    print "pipelines initialized, focus on gtk window and press s for stop/start recording (important to get valid files), press q for quit"
    self.window.connect("key-press-event",self.on_window_key_press_event)

    print "pipelines will start automatically"
    self.StartStop()

  def StartStop(self):
    if self.running == "false":
      self.running = "true"
      for p_item in range(self.number_of_streams):
        print "set pipeline %s to state:play" % p_item
        self.sink_array[p_item].set_property("location", self.file_path[p_item] + "recorded_camid_" + str(p_item) + "_nr" + str(self.record_id) + ".avi")
        self.pipeline_array[p_item].set_state(gst.STATE_PLAYING)
    else:
      self.running = "false"
      self.record_id += 1
      print "stop button pressed"
      for p_item in range(self.number_of_streams):
        print "will send EOS to src element: vsource" + str(p_item ) + " device: " + self.video_src[p_item]
	if self.pipeline_array[p_item].get_by_name("vsource" + str(p_item)).send_event(gst.event_new_eos()):
          print "EOS event sucessfully send"
        else:
          print "EOS event NOT send, try to send it to pipeline"
          self.pipeline_array[p_item].send_event(gst.event_new_eos())


m = ChildStreaming()
m.run()
