# by peter innerhofer
#
# streaming solution for "extended view stream" for the CoMeDia project

#import sys, os
#import socket, time
import pygst
#pygst.require("0.10")
import gst
#import gtk, pygtk, gobject
import gstreamerpipeline

class UDPSrcToFileSink(gstreamerpipeline.Pipeline):
	
	def __init__(self,config):
		gstreamerpipeline.Pipeline.__init__(self,config)
		self.record_id = 0

	def create_pipeline(self,p_item):
		self.record_id = 0
		self.pipeline = gst.Pipeline("pipeline%s" % p_item)

		self.source = gst.element_factory_make("udpsrc","vsource") 
		self.source.set_property("port", self.config.getint("UDP%s" % p_item,"port") )

		caps1 = gst.Caps(self.config.get("Caps","RTPConfigString"))
		filter1 = gst.element_factory_make("capsfilter", "filter1")
		filter1.set_property("caps", caps1)

		rtpmp4vdepay = gst.element_factory_make("rtpmp4vdepay", "rtpmp4vpay%s" % p_item)

		avimux = gst.element_factory_make("avimux", "avimuxer_%s" % p_item)
		queueb = gst.element_factory_make("queue")

		self.sink = gst.element_factory_make("filesink", "vsink")
		print self.config.get("Recorder","filepath") + "recorded_camid_" + str(p_item) + "_nr" + str(self.record_id) + ".avi"
		self.sink.set_property("location", self.config.get("Recorder","filepath") + "recorded_camid_" + str(p_item) + "_nr" + str(self.record_id) + ".avi")

		# adding the pipleine elements and linking them together
		self.pipeline.add(self.source, filter1, rtpmp4vdepay, avimux, queueb, self.sink)
		gst.element_link_many(self.source, filter1,rtpmp4vdepay, avimux, queueb, self.sink)

		self.bus = (self.pipeline.get_bus())
		self.bus.add_signal_watch()
		self.bus.connect("message",self.on_message)

	def start(self):
		print "should increase record_id and should change file Path!"
		#
		# change record id!
		gstreamerpipeline.Pipeline.start(self)
