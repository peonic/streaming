#!/usr/bin/env python
# streaming for 270grad
# by peter innerhofer

import sys, os
import socket, time
import pygst
pygst.require("0.10")
import gst
import gtk, pygtk, gobject
import gstreamerpipeline

class FileSrcToV4l2Loopback(gstreamerpipeline.Pipeline):
	
	def __init__(self,config):
		gstreamerpipeline.Pipeline.__init__(self,config)
		
	def create_pipeline(self,p_item,filepath):
		self.pipeline = gst.element_factory_make("playbin2", "vsource")
		print "\n\n" + "file://" + str(os.getcwd()) + filepath
		self.pipeline.set_property("uri", "file://" + str(os.getcwd()) + filepath)      

		self.sink = gst.element_factory_make("v4l2loopback", "v4l2loopback%s" % p_item)
		self.sink.set_property("device",self.config.get("VideoSink","VideoSink%s" % p_item))

		self.pipeline.set_property("video-sink", self.sink)

		self.bus = self.pipeline.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect("message",self.on_message)

	def set_filepath(self,filepath):
		print "\n new filename set: " + "file://" + str(os.getcwd()) + filepath
		self.pipeline.set_property("uri","file://" + str(os.getcwd()) + filepath)
