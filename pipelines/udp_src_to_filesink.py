# by peter innerhofer
#
# streaming solution for "extended view stream" for the CoMeDia project

import sys, os
import pygst
#pygst.require("0.10")
import gst
import gstreamerpipeline

class UDPSrcToFileSink(gstreamerpipeline.Pipeline):
	"""
	TODO: pipeline not working
	
	"""
	
	def __init__(self,config):
		gstreamerpipeline.Pipeline.__init__(self,config)
		self.record_id = 0

	def create_pipeline(self,p_item):
		print "\n -- creating UDPSrcToFileSink Pipeline -- \n"
		print "config number: %s" % p_item

		self.number = p_item	
		self.record_id = 0
		self.pipeline = gst.Pipeline("pipeline%s" % p_item)

		self.source = gst.element_factory_make("udpsrc","vsource") 
		self.source.set_property("port", self.config.getint("UDP%s" % p_item,"port"))

		caps_string = self.config.get("Caps","CurrentRTP")
		print "caps : %s" % caps_string
		caps1 = gst.Caps(caps_string)
		filter1 = gst.element_factory_make("capsfilter", "filter1")
		filter1.set_property("caps", caps1)

		rtpmp4vdepay = gst.element_factory_make("rtpmp4vdepay", "rtpmp4vpay%s" % p_item)
		queuea = gst.element_factory_make("queue")
		avimux = gst.element_factory_make("avimux", "avimuxer_%s" % p_item)
		queueb = gst.element_factory_make("queue")

		self.sink = gst.element_factory_make("filesink", "vsink")
		print self.config.get("Recorder","filepath") + "recorded_camid_" + str(p_item) + "_nr" + str(self.record_id) + ".avi"
		self.sink.set_property("location", os.getcwd() + self.config.get("Recorder","filepath") + "recorded_camid_" + str(p_item) + "_nr" + str(self.record_id) + ".avi")

		# adding the pipleine elements and linking them together
		self.pipeline.add(self.source, filter1, rtpmp4vdepay, queuea, avimux, queueb, self.sink)
		gst.element_link_many(self.source, filter1,rtpmp4vdepay, queuea, avimux, queueb, self.sink)

		self.bus = (self.pipeline.get_bus())
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
