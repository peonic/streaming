#!/usr/bin/env python
# by peter innerhofer
#
# streaming solution for "extended view stream" for the CoMeDia project

import sys, os
import socket, time
import pygst
#pygst.require("0.10")
import gst
import gtk, pygtk, gobject

class Pipeline:

	"""
	Base Pipeline Class:

	controlls the pipeline
	"""

	def __init__(self,config=0):
		self.config = config
		self.running = "false"
		self.number = 0;
		self.pipeline = []
		self.sink = []
		self.bus = []
		self.source = None
		
	def number(self, number):
		self.number = number

	def create_pipeline(self,p_item):
		print "should create pipeline"
		
		self.create_pipeline_from_string("v4l2src name=vsource ! videoscale ! video/x-raw-yuv,width=640,height=480 ! videorate ! video/x-raw-yuv,framerate=25/1 !  ffmpegcolorspace ! ffenc_mpeg4 bitrate=200000 ! rtpmp4vpay ! udpsink host=127.0.0.1 port=5000 name=vsink")
		# self.create_parsed_pipeline("udpsrc port=5000 name=vsource ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)MP4V-ES, profile-level-id=(string)1, config=(string)000001b001000001b58913000001000000012000c48d8800cd14043c1463000001b24c61766335322e37322e32, payload=(int)96 ! rtpmp4vdepay ! ffdec_mpeg4 ! ffmpegcolorspace ! v4l2loopback name=vsink")
		# self.create_parsed_pipeline("udpsrc port=5000 name=vsource ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)MP4V-ES, profile-level-id=(string)1, config=(string)000001b001000001b58913000001000000012000c48d8800cd14043c1463000001b24c61766335322e37322e32, payload=(int)96, ssrc=(uint)2499744084, clock-base=(uint)3815682964, seqnum-base=(uint)31664 ! rtpmp4vdepay ! ffdec_mpeg4 ! ffmpegcolorspace ! v4l2loopback name=vsink")
		
	def create_pipeline_from_string(self,gst_pipeline_string):
		self.pipeline = gst.parse_launch(gst_pipeline_string)
		self.bus = self.pipeline.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect("message",self.on_message)
		print " try to get the sink"
		self.sink = self.pipeline.get_by_name("vsink")
		print "sinks name %s" % self.sink.get_name()
		self.source = self.pipeline.get_by_name("vsource")
		#vsource = self.pipeline.get_by_name("vsource").get	
		

	def StartStop(self):
		if self.running == "false":
			self.start()
		else:
			self.stop()

	def start(self):
		if self.running == "false":
			self.running = "true"
		print "Start Pipeline"
		self.pipeline.set_state(gst.STATE_PLAYING)
		#print "state: %s" % str(self.pipeline.get_state())
		#print "caps : %s" % str(self.sink.get_pad('sink').get_property('caps'))

	def stop(self):
		if self.running == "true":
			self.running = "false"
		print "Send EnOffStream(EOS) to source element"
		try:
			if self.source.send_event(gst.event_new_eos()):
				print "EOS event sucessfully send"
			else:
				print "EOS event NOT send, try to send it to pipeline"
				self.pipeline.send_event(gst.event_new_eos())
		except NameError:
			print "Error: Pipeline: source not specified"

	def ready(self):
		if self.running == "false":
			print "set pipeline to state ready"
			self.pipeline.set_state(gst.STATE_READY)
			#print "state: %s" % str(self.pipeline.get_state())

	def on_message(self, bus, message):
		t = message.type
		# print str(bus.get_name()) + ": message received, type: " + str(t)
		if t == gst.MESSAGE_EOS:
			print "received EnOffStream(EOS) signal from bus %s" % bus.get_name()
			self.pipeline.set_state(gst.STATE_NULL)
			self.running = "false"
		elif t == gst.MESSAGE_ERROR:
			err, debug = message.parse_error()
			print "Error: %s" % err, debug
			self.pipeline.set_state(gst.STATE_NULL)
			self.running = "false"
		elif t == gst.MESSAGE_WARNING:
			err, debug = message.parse_warning()
			print "Warning: %s" % err, debug
			self.running = "false"

	def print_caps(self):
		print "\n caps of stream%s: %s" % self.number, str(self.sink.get_pad('sink').get_property('caps'))
	
	def get_caps(self):
		return str(self.sink.get_pad('sink').get_property('caps'))

	def quit(self):
		try: 
			self.bus.remove_signal_watch()
			print "pipeline destroyed"
		except NoneType:
			print "Error: Pipeline: bus not specified, pipeline destroyed"
