# streaming for 270grad
# by peter innerhofer

import sys, os
import time
import gst, pygst
import gstreamerpipeline

class UDPSrcToV4l2Loopback(gstreamerpipeline.Pipeline):
	
	"""
	Gstreamer Pipeline for receiving an udp rtp payloaded stream and sending
	it to a v4l2 loopback device. 
	
	be sure to have the v4l2loopback kernel module loaded. see Install.txt for 
	details.
	
	!!!just works if the correct caps are provided!!!! TODO: provide them automatically
	
	test at the commandline:
	encoding:
	% gst-launch -v v4l2src ! videoscale ! video/x-raw-yuv,width=640,height=480 ! videorate ! video/x-raw-yuv,framerate=25/1 !  ffmpegcolorspace ! ffenc_mpeg4 bitrate=200000 ! rtpmp4vpay ! udpsink host=127.0.0.1 port=5000
	
	forwarding:
	% gst-launch -v udpsrc port=5000 ! "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)MP4V-ES, profile-level-id=(string)1, config=(string)000001b001000001b58913000001000000012000c48d8800cd14043c1463000001b24c61766335322e37322e32, payload=(int)96, ssrc=(uint)3139664022, clock-base=(uint)4173634897, seqnum-base=(uint)58918" ! rtpmp4vdepay ! ffdec_mpeg4 ! queue ! ffmpegcolorspace ! "video/x-raw-yuv,format=(fourcc)YUY2" !  v4l2sink device=/dev/video1
	
	displaying:
	% gst-launch -vvv v4l2src device=/dev/video1 ! xvimagesink 	
	"""

	def __init__(self,config):
		gstreamerpipeline.Pipeline.__init__(self,config)
		self.config = config
				
	def create_pipeline(self,p_item):
		print "\n -- creating UDPSrcToV4l2Loopback Pipeline -- \n"
		print "UDPAddr: host: " + self.config.get("UDP%s" % p_item, "host") + " port: "+ self.config.get("UDP%s" % p_item, "port")
		print "Video Sink: " + self.config.get("VideoSink","VideoSink%s" % p_item)

		self.number = p_item	
		self.pipeline = gst.Pipeline("pipeline%s" % p_item)

		self.source = gst.element_factory_make("udpsrc","vsource") 
		self.source.set_property("port", self.config.getint("UDP%s" % p_item,"port"))

		print "caps which are used: " + str(self.config.get("Caps","CurrentRTP"))
		caps1 = gst.Caps(self.config.get("Caps","CurrentRTP"))
		filter1 = gst.element_factory_make("capsfilter", "filter1")
		filter1.set_property("caps", caps1)

		rtpmp4vdepay = gst.element_factory_make("rtpmp4vdepay", "rtpmp4vpay%s" % p_item)
		decoder = gst.element_factory_make("ffdec_mpeg4", "decoder%s" % p_item)
		queue = gst.element_factory_make("queue","queue")
		conv = gst.element_factory_make("ffmpegcolorspace", "ffmpegcolorspace%s" % p_item)
		
		caps2 = gst.Caps(self.config.get("Caps","YUY2"))
		filter2 = gst.element_factory_make("capsfilter", "filter2")
		filter2.set_property("caps", caps2)

		self.sink = gst.element_factory_make("v4l2sink", "v4l2sink%s" % p_item)
		self.sink.set_property("device",self.config.get("VideoSink","VideoSink%s" % p_item))

		# adding the pipleine elements and linking them together
		# filter2 is needed because output of ffdec_mpeg4 is in I420 colorspace
		self.pipeline.add(self.source, filter1, rtpmp4vdepay, decoder, queue, conv, filter2, self.sink)
		gst.element_link_many(self.source, filter1,rtpmp4vdepay, decoder, queue, conv, filter2, self.sink)

		self.bus = self.pipeline.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect("message",self.on_message)
