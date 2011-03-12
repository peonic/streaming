Streaming Solution with Gstreamer
==================
by Peter Innerhofer

It was created at Institut for Electronic Music and Acoustics within the
CO-ME-DI-A project leaded by Winfried Ritsch for the art installation 
"extended view" by Peter Venus.

The CO-ME-DI-A project is supported by the Education, Audiovisual & 
Culture Executive Agency (EACEA) of the European Comission for 
the period 2007 - 2010 (http://www.comedia.eu.org/).

Features:
 * create, controll, delete predefined streams from pure data
 * create a stream from a gstreamer pipeline string from pure data
 * controlling/handling with OSC Messages
 * can be distributed on multiple maschines (because of computational efforts of encoding)
 * all stream are encoded with mpeg4/divx
 
Example:
 * start main.py
 * start pd/control_test.pd
 * create the needed predefined Pipelines
 * start the stream
the stream is now running, see the commandline output!

Configuration File:
A config.ini file defines the parameter of a stream. 
For example: VideoSrcToUDPSink
this stream graps a v4l2 video src device encodes it and streams it to a 
destination host over UDP. In the config file, the host and port can be 
specified, the video src dev too.

the concept of the pipeline number:
in this application one can create multiple stream on one maschine, 
therefore a pipeline number is introduced. this pipeline number 
specifies with parameter of the config file is used to create a 
specific stream. dont mix it up with the stream number, this is just 
for starting, stopping and destroing a stream. the pipeline number 
specifies the parameter used of from the config file.

Encoding:
all streams are encoded with ffmpeg_mpeg4. this encoder has a low 
latecy, a small bandwith consumtion at low computational efforts. see 
the encoding_notes.txt for details.


Install
=======

executable file with all steps: install.sh

Git:
 $ sudo apt-get install git

Python:
 $ sudo apt-get install python python-gtk2 python-gobject python-gst0.10 python-gst0.10-dev 

pyOSC:
A Simple OpenSoundControl implementation, in Pure Python.
 $ git clone git://gitorious.org/pyosc/devel.git pyosc
 $ cd pyosc
 $ sudo ./setup.py install

Gstreamer:
 $ sudo apt-get install gstreamer0.10-nice gstreamer0.10-ffmpeg gstreamer0.10-alsa gstreamer0.10-plugins-base gstreamer0.10-plugins-good gstreamer0.10-plugins-bad gstreamer0.10-plugins-ugly gstreamer0.10-tools  

V4l2 Loopback:
v4l2loopback kernel module, use github repo from IOhannes, https://github.com/umlaeute/v4l2loopback
 $ git clone https://github.com/umlaeute/v4l2loopback v4l2loopback
 $ cd v4l2loopback
 $ make
 $ sudo make install

when loaded number of devices have can be defined i.e. 
 $ sudo modprobe v4l2loopback devices=10


TESTING the Installation
========================

load kernel module: 
 
 $ sudo modprobe v4l2loopback devices=3

test gst-loopback: 
 
 $ gst-launch -v videotestsrc ! video/x-raw-yuv,width=640,height=480,framerate=25/1 ! ffmpegcolorspace ! v4l2sink device=/dev/video2
 $ gst-launch -v v4l2src device=/dev/video2 ! xvimagesink
 
test all:
 * start pd, open pd/controll_test.pd
 * connect to host
 * choose config number
 * create predefined streams
 * start stream
