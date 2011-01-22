Streaming Solution
==================
by Peter Innerhofer

Streaming Solution with Gstreamer. 

Features:
 * create, controll, delete predefined streams from pure data
 * create a stream from a gstreamer pipeline string from pure data
 * controlling/handling with OSC Messages
 * can be distributed on multiple maschines (because of computational efforts of encoding)
 * all stream are encoded with divx
 
Example:
 * start main.py
 * start example.pd
 * send /stream/create/fromfactory Video..... (one of the exampe Pipelines)
 * send /stream/start $1 	where $1 is the number of the stream, now 0
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
