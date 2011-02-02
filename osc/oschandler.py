import OSC
import time, threading

class OSCServer:
	""" 
	receiving OSC with pyOSC
	https://trac.v2.nl/wiki/pyOSC
	example by www.ixi-audio.net based on pyOSC documentation

	this is a very basic example, for detailed info on pyOSC functionality check the OSC.py file 
	or run pydoc pyOSC.py. you can also get the docs by opening a python shell and doing
	>>> import OSC
	>>> help(OSC)
	"""

	def __init__(self,server_addr):
		self.server_addr = server_addr
		self.server = OSC.OSCServer(self.server_addr)

		# this registers a 'default' handler (for unmatched messages), 
		# an /'error' handler, an '/info' handler.
		# And, if the client supports it, a '/subscribe' & '/unsubscribe' handler
		self.server.addDefaultHandlers()

	def addMsgHandler(self,osc_message_string,function):
		# callback function, wenn recieving osc message
		print "Register Callback-function: %s" % osc_message_string
		self.server.addMsgHandler(osc_message_string, function)

	def printAddressSpace(self):
		# just checking which handlers we have added
		print "Registered Callback-functions are :"
		for addr in self.server.getOSCAddressSpace():
			print addr

	def start(self):
		# Start OSCServer
		print "\nStarting OSCServer."
		self.st = threading.Thread( target = self.server.serve_forever )
		self.st.start()

	def close(self):
		print "\nClosing OSCServer."
		self.server.close()
		print "Waiting for Server-thread to finish"
		self.st.join() ##!!!
		print "Done"

class OSCClient:
	"""
	sending OSC Messages with pyOSC
	https://trac.v2.nl/wiki/pyOSC
	example by www.ixi-audio.net based on pyOSC documentation

	this is a very basic example, for detailed info on pyOSC functionality check the OSC.py file 
	or run pydoc pyOSC.py. you can also get the docs by opening a python shell and doing
	>>> import OSC
	>>> help(OSC)
	"""
	
	def __init__(self,client_addr):    
		self.client = OSC.OSCClient()
		self.connect(client_addr)
		
	def connect(self,client_addr):
		self.client.connect( client_addr ) 

	def sendMessage(self,addr,data):
		msg = OSC.OSCMessage()
		msg.setAddress(addr)
		msg.append(data)
		self.client.send(msg)
