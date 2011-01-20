# streaming for 270grad
# by peter innerhofer

import sys, os
import time
import gst, pygst
import gstreamerpipeline

class VideoSrcToFileSink(gstreamerpipeline.Pipeline):
	
	"""
	Gstreamer Pipeline for recording to File.
	
	important to send end of stream (-e) otherwise file will not be closed
	properly
	
	commandline test:
	gst-launch-0.10 -ve v4l2src ! videoscale ! video/x-raw-yuv,width=640,height=480 ! videorate ! video/x-raw-yuv,framerate=25/1 !  ffmpegcolorspace ! ffenc_mpeg4 bitrate=1000000 ! avimux ! filesink location=test.avi	
	"""

	def __init__(self,config):
		gstreamerpipeline.Pipeline.__init__(self,config)
		self.record_id = 0

	def create_pipeline(self,p_item):
		self.pipeline = gst.Pipeline("pipeline%s" % p_item)

		self.source = gst.element_factory_make("v4l2src","vsource") 
		self.source.set_property("device", self.config.get("VideoSrc","VideoSrc%s" % p_item))

		scaler = gst.element_factory_make("videoscale", "vscale")

		caps1 = gst.Caps(self.config.get("Caps","RawFullsize"))
		filter1 = gst.element_factory_make("capsfilter", "filter")
		filter1.set_property("caps", caps1)

		rate = gst.element_factory_make("videorate", "vrate")
		conv = gst.element_factory_make("ffmpegcolorspace")

		avimux = gst.element_factory_make("avimux", "avimuxer_%s" % p_item)
		queueb = gst.element_factory_make("queue")

		self.sink = gst.element_factory_make("filesink", "filesink%s" % p_item)   
		self.sink.set_property("location", self.config.get("Recorder","filepath") + "recorded_camid_" + str(p_item) + "_nr" + str(self.record_id) + ".avi")

		# adding the pipleine elements and linking them together
		self.pipeline.add(self.source, scaler, rate, filter1, conv, avimux, self.sink)
		gst.element_link_many(self.source, scaler, rate, filter1, conv, avimux, self.sink)

		self.bus = self.pipeline.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect("message",self.on_message)
		
		
	def start(self):
		print "should increase record_id and should change file Path!"
		#
		# change record id!
		gstreamerpipeline.Pipeline.start(self)

