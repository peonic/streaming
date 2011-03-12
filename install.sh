#!/bin/bash

# git

sudo apt-get install git

# python

sudo apt-get install python python-gtk2 python-gobject python-gst0.10 python-gst0.10-dev 

# pyOSC

git clone git://gitorious.org/pyosc/devel.git pyosc
cd pyosc
sudo ./setup.py install
cd ..

# gstreamer

sudo apt-get install gstreamer0.10-nice gstreamer0.10-ffmpeg gstreamer0.10-alsa gstreamer0.10-plugins-base gstreamer0.10-plugins-good gstreamer0.10-plugins-bad gstreamer0.10-plugins-ugly gstreamer0.10-tools  

# v4l2loopback kernel module

git clone https://github.com/umlaeute/v4l2loopback v4l2loopback
cd v4l2loopback
make
sudo make install
cd ..

# TESTING the Installation
#
# sudo modprobe v4l2loopback devices=3
# gst-launch -v videotestsrc ! video/x-raw-yuv,width=640,height=480,framerate=25/1 ! ffmpegcolorspace ! v4l2loopback device=/dev/video2
# gst-launch -v v4l2src device=/dev/video2 ! xvimagesink
