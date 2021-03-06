# streaming for 270grad
# by peter innerhofer

import sys, os
import socket, time
import gst, pygst
import gstreamerpipeline

class VideoSrcToUDPSink(gstreamerpipeline.Pipeline):

	""" 
	Gstreamer Pipeline which stream's a video from v4l2src and streams
	it to a udp socket. The stream is encoded with mpeg4's divx. see in 
	the config file to change bitrate
		
	TODO: a elegant way to write caps to a file, because the caps always
	changing, especially when changing the bitrate
		
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

	def create_pipeline(self,p_item):
		print "\n -- creating VideoSrcToUDPSink Pipeline -- \n"
		print "Video Src Dev: " + self.config.get("VideoSrc", "VideoSrc%s" % p_item)
		print "UDPAddr: host: " + self.config.get("UDP%s" % p_item, "host") + " port: "+ self.config.get("UDP%s" % p_item, "port")
		
		self.number = p_item
		
		self.pipeline = gst.Pipeline("pipeline%s" % p_item)

		self.source = gst.element_factory_make("v4l2src","vsource") 
		self.source.set_property("device", self.config.get("VideoSrc", "VideoSrc%s" % p_item))

		scaler = gst.element_factory_make("videoscale", "vscale")

		caps1 = gst.Caps(self.config.get("Caps","RawHalfsize"))
		filter1 = gst.element_factory_make("capsfilter", "filter")
		filter1.set_property("caps", caps1)

		rate = gst.element_factory_make("videorate", "vrate")
		conv = gst.element_factory_make("ffmpegcolorspace")

		encoder = gst.element_factory_make("ffenc_mpeg4", "ffenc_mpeg4_%s" % p_item)
		encoder.set_property("bitrate", self.config.getint("Encoder","Bitrate"))

		rtpmp4vpay = gst.element_factory_make("rtpmp4vpay", "rtpmp4vpay%s" % p_item)

		self.sink = gst.element_factory_make("udpsink", "udpsink%s" % p_item)
		self.sink.set_property("host", self.config.get("UDP%s" % p_item, "host"))
		self.sink.set_property("port", self.config.getint("UDP%s" % p_item, "port"))

		# adding the pipleine elements and linking them together
		self.pipeline.add(self.source, scaler, rate, filter1, conv, encoder, rtpmp4vpay, self.sink)
		gst.element_link_many(self.source, scaler, rate, filter1, conv, encoder, rtpmp4vpay, self.sink)

		self.bus = self.pipeline.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect("message",self.on_message)
