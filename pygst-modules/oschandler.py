""" receiving OSC with pyOSC
https://trac.v2.nl/wiki/pyOSC
example by www.ixi-audio.net based on pyOSC documentation

this is a very basic example, for detailed info on pyOSC functionality check the OSC.py file 
or run pydoc pyOSC.py. you can also get the docs by opening a python shell and doing
>>> import OSC
>>> help(OSC)
"""


import OSC
import time, threading


class OSCHandler:

  def __init__(self,addr):
    self.osc_receive_address = addr
    self.osc_server = OSC.OSCServer(self.osc_receive_address)

    # this registers a 'default' handler (for unmatched messages), 
    # an /'error' handler, an '/info' handler.
    # And, if the client supports it, a '/subscribe' & '/unsubscribe' handler
    self.osc_server.addDefaultHandlers()

  def addMsgHandler(self,osc_message_string,function):
    # callback function, wenn recieving osc message
    self.osc_server.addMsgHandler(osc_message_string, function)

  def printAddressSpace(self):
    # just checking which handlers we have added
    print "Registered Callback-functions are :"
    for addr in self.osc_server.getOSCAddressSpace():
      print addr

  def start(self):
    # Start OSCServer
    print "\nStarting OSCServer. Use ctrl-C to quit."
    self.st = threading.Thread( target = self.osc_server.serve_forever )
    self.st.start()

  def close(self):
    print "\nClosing OSCServer."
    self.osc_server.close()
    print "Waiting for Server-thread to finish"
    self.st.join() ##!!!
    print "Done"
