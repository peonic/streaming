#!/usr/bin/env python
# -*- coding: utf-8 -*-

# streaming for maschinenhalle
# by peter innerhofer

# shows all 12 streams simultaniously (needs a lot of cpu!)

# keyboard commands: 
#   's' = start/stop
#   'f' = full-/unfullscreen
#   'q' = quit

# see the DrawingAreaFactory for arranig the video windows

# currently jpegenc is used so put this pipeline in script

#####  jpegenc ######## 
# gst-launch v4l2src device=/dev/video1 ! queue ! videoscale ! videorate ! video/x-raw-yuv,framerate=20/1 ! videocrop top=0 left=100 right=100 bottom=0 ! videoscale ! video/x-raw-yuv,width=220,height=240! ffmpegcolorspace ! jpegenc quality=80 ! udpsink host=192.168.10.5 port=5000
# decoding:
# gst-launch-0.10 udpsrc port=5000 ! jpegdec !  xvimagesink

import sys, os
import pygst
pygst.require("0.10")
import gst
import pygtk, gtk, gobject

class DrawingAreaFactory:
  def __init__(self):
    self.__drawing_areas = []

  def create(self):
    vbox = gtk.VBox()
    for i in range(0,2):
      hbox = self.create_row()
      hbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(red=0, green=0, blue=0, pixel=0))
      vbox.pack_start(hbox)
    return vbox

  def create_row(self):
    hbox = gtk.HBox()
    for i in range(0,6):
      da = gtk.DrawingArea()
      da.set_size_request(200,100)
      self.__drawing_areas.append(da)
      hbox.pack_start(da)
    return hbox

  def get_drawing_areas(self):
    return self.__drawing_areas

class Main:

  def __init__(self):
    self.number_of_streams = 12 # for the range so its from 0 to 11 = 12 streams

    #GUI
    self.window = gtk.Window()
    self.window.set_title("Video-Player")
    self.window.set_default_size(960, 900)
    self.window.connect("destroy", gtk.main_quit, "WM destroy")
    
    self.daf = DrawingAreaFactory()
    self.vbox = self.daf.create()
    #self.vbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(red=0, green=0, blue=0, pixel=0))
    self.das = self.daf.get_drawing_areas()

    self.window.add(self.vbox)
    self.window.show_all()    

    # Create GStreamer Pipeline
    self.pipeline_array = []
    self.sink_array = []
    for p_item in range(self.number_of_streams):
      self.pipeline_array.append(gst.Pipeline("mypipeline%s" % p_item))

      #scaler = gst.element_factory_make("videoscale", "vscale")
      #scaler.set_property("method", 1)
      decoder = gst.element_factory_make("jpegdec")

      #source = gst.element_factory_make("v4l2src","vsource") 
      #source.set_property("device", "/dev/video0")

      # source element udp, port addr from 5000 - 5011
      source = gst.element_factory_make("udpsrc")
      source.set_property("port", 5000 + p_item)
    
      #caps = gst.Caps("video/x-raw-rgb, width=200, height=100")
      #filter = gst.element_factory_make("capsfilter", "filter")
      #filter.set_property("caps", caps)

      #conv = gst.element_factory_make("ffmpegcolorspace")

      queuea = gst.element_factory_make("queue", "queuea")
      #queueb = gst.element_factory_make("queue", "queueb")

      self.sink_array.append(gst.element_factory_make("xvimagesink", "avsink"))

      # adding the pipleine elements and linking them together
      #self.pipeline_array[p_item].add(source, queuea, scaler, filter, conv, self.sink_array[p_item])
      #gst.element_link_many(source, queuea, scaler, filter, conv, self.sink_array[p_item])
      self.pipeline_array[p_item].add(source, queuea, decoder, self.sink_array[p_item])
      gst.element_link_many(source, queuea, decoder, self.sink_array[p_item])
      
      # connect window id's with sinks
      self.sink_array[p_item].set_property("force-aspect-ratio", True)
      self.sink_array[p_item].set_xwindow_id(self.das[p_item].window.xid)

    # setting keyboard events, setting fullscreen
    self.window.connect("key-press-event",self.on_window_key_press_event)
    self.window.fullscreen()
    self.running = "false"
    self.is_fullscreen = "true"

  def on_window_key_press_event(self,window,event):
    print event.state
    print event.keyval
    #print range(48,58).index(event.keyval)
    if event.keyval == 115:
      self.StartStop()
    if event.keyval == 102:
      self.Fullscreen()
    if event.keyval == 113:
      self.OnQuit(self.window)
    if event.keyval < 48 and event.keyval > 58:
      print event.keyval % 48
      self.ToggleDark(event.keyval % 48)

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

  def Fullscreen(self):
    if self.is_fullscreen == "true":
      self.is_fullscreen = "false"
      self.window.unfullscreen()
    else:
      self.is_fullscreen = "true"
      self.window.fullscreen()

  def ToggleDark(key):
    print "toggle %i" % key
    self.pipeline_array[key].set_state(gst.STATE_NULL)

  def OnQuit(self, widget):
    gtk.main_quit()

Main()
gtk.gdk.threads_init()
gtk.main()
