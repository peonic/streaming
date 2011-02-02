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
	gst-launch-0.10 -ve v4l2src ! videoscale ! videorate ! video/x-raw-yuv,width=640,height=480,framerate=25/1 ! ffmpegcolorspace ! ffenc_mpeg4 bitrate=1000000 ! avimux ! filesink location=test.avi
	"""

	def __init__(self,config):
		gstreamerpipeline.Pipeline.__init__(self,config)
		self.record_id = 0

	def create_pipeline(self,p_item):
		print "\n -- creating VideoSrcToFileSink Pipeline -- \n"
		print "Pipeline Modell: \n" + "gst-launch -ve v4l2src ! videoscale ! video/x-raw-yuv,width=640,height=480 ! videorate ! video/x-raw-yuv,framerate=25/1 !  ffmpegcolorspace ! ffenc_mpeg4 bitrate=1000000 ! avimux ! filesink location=test.avi"
		print "ConfigNumber: %s" % p_item
		print "VideoSrcDev: %s" % self.config.get("VideoSrc","VideoSrc%s" % p_item)
		self.number = p_item
		
		self.pipeline = gst.Pipeline("pipeline%s" % p_item)

		self.source = gst.element_factory_make("v4l2src","vsource") 
		self.source.set_property("device", self.config.get("VideoSrc","VideoSrc%s" % p_item))

		scaler = gst.element_factory_make("videoscale", "vscale")

		caps1 = gst.Caps(self.config.get("Caps","RawFullsize"))
		filter1 = gst.element_factory_make("capsfilter", "filter")
		filter1.set_property("caps", caps1)

		rate = gst.element_factory_make("videorate", "vrate")
		conv = gst.element_factory_make("ffmpegcolorspace")
		
		encoder = gst.element_factory_make("ffenc_mpeg4", "ffenc_mpeg4")
		encoder.set_property("bitrate",self.config.getint("Encoder","Bitrate"))
		
		self.sink = gst.element_factory_make("avimux", "avimuxer")
		queue = gst.element_factory_make("queue")

		filesink = gst.element_factory_make("filesink", "filesink")   
		print "Filepath: " + os.getcwd() + self.config.get("Recorder","filepath") + "recorded_camid_" + str(p_item) + "_nr" + str(self.record_id) + ".avi"
		filesink.set_property("location", os.getcwd() + self.config.get("Recorder","filepath") + "recorded_camid_" + str(p_item) + "_nr" + str(self.record_id) + ".avi")

		# adding the pipleine elements and linking them together
		self.pipeline.add(self.source, scaler, rate, filter1, conv, encoder, self.sink, queue, filesink)
		gst.element_link_many(self.source, scaler, rate, filter1, conv, encoder, self.sink, queue, filesink)

		self.bus = self.pipeline.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect("message",self.on_message)
		
		
	def start(self):
		if self.running == "false":
			print "increasing record_id and change output file"
			self.record_id += 1
			print self.config.get("Recorder","filepath") + "recorded_camid_" + str(self.number) + "_nr" + str(self.record_id) + ".avi"
			self.sink.set_property("location", os.getcwd() + self.config.get("Recorder","filepath") + "recorded_camid_" + str(self.number) + "_nr" + str(self.record_id) + ".avi")
			gstreamerpipeline.Pipeline.start(self)
		else:
			print "pipeline running, cant change filepath"
