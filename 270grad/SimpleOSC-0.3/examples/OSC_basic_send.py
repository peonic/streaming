
""" Basic module to ease the use of pyOSC module https://trac.v2.nl/wiki/pyOSC

you must have pyOSC installed for this to run.

This is meant to be used by students or newies that are starting to experiment with OSC. If you are an advanced user
you probably want to bypass this module and use directly pyOSC, we have some examples of very simple use in our website.
Check the pyOSC website for more documentation.

License : LGPL
"""

from simpleOSC import *

import time, random

"""
note that if there is nobody listening in the other end we get an error like this
    OSC.OSCClientError: while sending: [Errno 111] Connection refused
so we need to have an app listening in the receiving port for this to work properly

this is a very basic example, for detailed info on pyOSC functionality check the OSC.py file 
or run pydoc pyOSC.py. you can also get the docs by opening a python shell and doing
>>> import OSC
>>> help(OSC)
"""



initOSCClient('127.0.0.1', 9000)

# basic message
sendOSCMsg( '/test', [33, 222, 111, "hello"] )



# bundle : few messages sent together
# use them to send many different messages on every loop for instance in a game. saves CPU and it is faster
bundle = createOSCBundle()

bundle.append( { 'addr':"/print", 'args':["blahblah", 677] } ) # one way to append

msg = createOSCMsg( '/print', [123, 'txakoli'] ) # another way to append
bundle.append(msg)

bundle.append( createOSCMsg( '/print', [7878, 'gorri'] ) ) # the same in one line

sendOSCBundle(bundle)# now send it



# lets try sending a different random number every frame in a loop

try :
    seed = random.Random() # need to seed first 
    
    while 1: # endless loop
        n = seed.randint(1, 1000) # get a random num every loop
        sendOSCMsg( '/print', [ n ] )
        time.sleep(5) # wait here some secs

except KeyboardInterrupt:
    print "Closing OSCClient"
    closeOSC()
    print "Done"
        
