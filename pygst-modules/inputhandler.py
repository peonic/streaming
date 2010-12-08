#!/usr/bin/env python
# streaming for 270grad
# by peter innerhofer
#
# Description: 
# builds n streams (default 4) from v4l2src, encodes them with xvid (ffenc_mpeg4), and send them via udp to a host (default 127.0.0.1 port=5000)
# second pipeline will recieve the stream, decode it, and forward it to a v4l2loopback device
# 


import sys, os
import threading, time
import gobject


class InputHandler:

  def __init__(self):
    print "init"
    self.callback_function = self.print_help


  def callback_function(self,method):
    

  def get_input(self):
    raw_input('input commands:')
    

  def print_help(self):
    print "this is the input handler help"
    print " input commands: s...start/stop, q...quit"

