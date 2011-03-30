#!/usr/bin/env python
# by peter innerhofer
#
# streaming solution for "extended view stream" for the CoMeDia project

import sys, os
import ConfigParser
import socket, time
import pygst
pygst.require("0.10")
import gst
import gtk, pygtk, gobject
import osc.oschandler, OSC
import pipelines.gstreamerpipeline
from pipelines.udp_src_to_filesink import UDPSrcToFileSink
from pipelines.file_src_to_v4l2loopback import FileSrcToV4l2Loopback
from pipelines.video_src_udp_sink import VideoSrcToUDPSink
from pipelines.udp_src_to_v4l2loopback import UDPSrcToV4l2Loopback
from pipelines.video_src_file_sink import VideoSrcToFileSink

class StreamingApplication:
	
	"""
	Streaming Application

	Class for handling Gstreamer Pipelines. 

	try: 
	!! osc_test.pd file!!

	Controlling the pipeline can be done with 3 diffrent methods. 
	* commandline input
	* keyboard input in the gtk window
	* send OSC messages
	!! Currently just OSC is implemented, see the osc_test.pd file !!

	OSC: port: 8000 messagestring: 
	"""

	def __init__(self):  
		self.config = ConfigParser.ConfigParser()
		self.config.read("config.ini")
		self.video_caps = ConfigParser.ConfigParser()
		self.video_caps.read("video.caps")
		
		# print self.config.sections()

		self.pipeline_array = []
		self.config_number = 0
		self.gtk_init = 0

	def init_OSC(self):    
		self.osc_server = osc.oschandler.OSCServer((self.config.get("OSC","ServerAddress"),self.config.getint("OSC","ServerPort")))
		self.osc_server.addMsgHandler(self.config.get("OSC","StreamStart"),self.stream_start_stop)
		self.osc_server.addMsgHandler(self.config.get("OSC","StreamReady"),self.stream_ready)
		self.osc_server.addMsgHandler(self.config.get("OSC","CreatePipelineFromString"),self.create_pipeline_from_osc_string)
		self.osc_server.addMsgHandler(self.config.get("OSC","CapsPrint"),self.osc_print_caps)
		#self.osc_server.addMsgHandler(self.config.get("OSC","CapsReceive"),self.osc_print_caps)
		self.osc_server.addMsgHandler(self.config.get("OSC","StreamFactoryCreate"),self.pipeline_factory)
		self.osc_server.addMsgHandler(self.config.get("OSC","StreamDelete"),self.delete_pipeline)
		self.osc_server.addMsgHandler(self.config.get("OSC","ConfigChangeNumber"),self.change_config_number)
		self.osc_server.addMsgHandler(self.config.get("OSC","CapsWriteToFile"),self.write_caps_to_file)
		self.osc_server.addMsgHandler(self.config.get("OSC","CapsReadFromFile"),self.read_caps_from_file)
		self.osc_server.start()
		
		self.osc_client = osc.oschandler.OSCClient((self.config.get("OSC","ClientAddress"),self.config.getint("OSC","ClientPort")))

	def read_caps_from_file(self,addr, tags, data, source):
		print "\nrecieved osc msg " + str(addr) + " data=%s  \n" % data[-1] 
		self.video_caps.read("video.caps")
		
	def write_caps_to_file(self,addr, tags, data, source):
		print "\nrecieved osc msg " + str(addr) + " data=%s  \n" % data[-1] 
		cfgfile = open("video.caps",'w')
		for p in self.pipeline_array:
			c = p.get_caps()
			print "\n caps of stream" + str(p.number) + ": " + c
			self.video_caps.set("CurrentCaps","CurentPipeline%s" % p.number,c)			
		self.video_caps.write(cfgfile)
	

	def factory(self, className, args):
		try:
			aClass = getattr(__import__(__name__),className)
			return aClass(args)
			# apply(aClass, args)
		except AttributeError:
			print "\n Error: Called Factory with ClassName that doesn't exist!\n  ClassName: %s\n" % className
			return -1

	def pipeline_factory(self,addr, tags, data, source):
		print "\nrecieved osc msg " + str(addr) + " data=%s  \n" % data[-1] 
		p = self.factory(data[-1], self.config)
		if p is not -1:
			self.pipeline_array.append(p)
			self.pipeline_array[-1].create_pipeline(self.config_number)      

	def parse_pipeline(self,gst_pipeline_string):
		self.pipeline_array.append(pipelines.gstreamerpipeline.Pipeline(self.config))
		self.pipeline_array[-1].create_pipeline_from_string(gst_pipeline_string)
    
	def create_pipeline_from_osc_string(self, addr, tags, data, source):
		print "\nrecieved osc msg " + str(addr) + " data=%s  \n" % data[-1] 
		for d in data:
			print d
			#self.parse_pipeline(data[0])

	def change_config_number(self, addr, tags, data, source):
		print "\nrecieved osc msg " + str(addr) + " data=%s  \n" % data[-1] 
		self.config_number = data[0]

	def stream_start_stop(self,addr, tags, data, source):
		print "\nrecieved osc msg " + str(addr) + " data=%s  \n" % data[-1] 
		self.StartStop(data[-1])

	def stream_ready(self,addr, tags, data, source):
		print "\nrecieved osc msg " + str(addr) + " data=%s  \n" % data[-1] 
		self.ready()

	def delete_pipeline(self,addr, tags, data, source):
		print "\nrecieved osc msg " + str(addr) + " data=%s  \n" % data[-1] 
		if data[-1] >= 0 and data[-1] < len(self.pipeline_array):
			p = self.pipeline_array.pop(data[-1])
			p.quit()
			print "nr of streams: " + str(len(self.pipeline_array))
		else:
			print "no pipelines objects"

	def osc_print_caps(self,addr, tags, data, source):
		for p in self.pipeline_array:
			c = p.get_caps()
			print "\n caps of stream" + str(p.number) + ": " + c
			
			"""
			
			cfgfile = open("config.ini",'w')
			self.config.write(cfgfile)
			self.config.read("config.ini")
			# print self.config.get("OSC","CurentPipeline%s" % p.number)
			"""
    
    
	def run(self):
		print "initializing Object"

		#self.parse_pipeline(self.config.get("Pipeline","VideoSrc2UdpSink"))

		#self.pipeline_array.append(udp_src_to_filesink.UDPSrcToFileSink(self.config))
		#self.pipeline_array[-1].create_pipeline(0)

		#self.pipeline_array.append(file_src_to_v4l2loopback.FileSrcToV4l2Loopback(self.config))
		#self.pipeline_array[-1].create_pipeline(0,"/videos/test.avi")

		#self.pipeline_array.append(video_src_udp_sink.VideoSrcToUDPSink(self.config))
		#self.pipeline_array[-1].create_pipeline(0)	

		#self.pipeline_array.append(udp_src_to_v4l2loopback.UDPSrcToV4l2Loopback(self.config))
		#self.pipeline_array[-1].create_pipeline(0)

		#self.pipeline_array.append(video_src_file_sink.VideoSrcToFileSink(self.config))
		#self.pipeline_array[-1].create_pipeline(0)

		print "Pipeline('s) initialized"
		self.init_OSC()

		gobject.threads_init()
		self.mainloop = gobject.MainLoop()
		self.mainloop.run()
		print "exit"
   
	def StartStopAll(self):
		for p in self.pipeline_array:
			p.StartStop()
  
	def StartStop(self, p_nr):
		if p_nr >= 0 and p_nr < len(self.pipeline_array):
			self.pipeline_array[p_nr].StartStop()
    
	def ready(self,p_nr):
		if p_nr >= 0 and p_nr < len(self.pipeline_array):
			self.pipeline_array[p_nr].ready()
   
	def readyAll(self):
		for p in self.pipeline_array:
			p.ready()
		  
	def quit(self):
		try:
			for p in self.pipeline_array:
				p.stop()
				time.sleep(1)
				p.quit()
		except NameError:
			print "NameError: somehow pipeline.quit() not working"
		self.osc_server.close()
		self.mainloop.quit()
      
	def init_gtk(self):
		self.gtk_init = 1
		self.window = gtk.Window()
		#self.window.connect("destroy", gtk.main_quit, "WM destroy")
		#self.window.connect("key-press-event",self.on_window_key_press_event)
		hbox = gtk.HBox()
		self.da = gtk.DrawingArea()
		hbox.pack_start(self.da)
		self.window.add(hbox)
		self.window.show_all()
		gtk.gdk.threads_init()
		print "GTK Window initialized"
		# self.sink = gst.element_factory_make("xvimagesink", "vsink")
		#self.sink.set_property("force-aspect-ratio", True)
		#self.sink.set_xwindow_id(self.da.window.xid)
				

try :
	print "\ncreating Streaming Server \n\npress Ctrl-C to exit\n"
	m = StreamingApplication()
	m.run()
except KeyboardInterrupt :
	m.quit()

