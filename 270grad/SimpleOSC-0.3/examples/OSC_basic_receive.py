
""" Basic module to ease the use of pyOSC module https://trac.v2.nl/wiki/pyOSC

you must have pyOSC installed for this to run.

This is meant to be used by students or newies that are starting to experiment with OSC. If you are an advanced user
you probably want to bypass this module and use directly pyOSC, we have some examples of very simple use in our website.
Check the pyOSC website for more documentation.

License : LGPL
"""


from simpleOSC import *
import time




initOSCServer('127.0.0.1', 9001)



# define a message-handler function for the server to call.
def printing_handler(addr, tags, data, source):
    print "---"
    print "received new osc msg from %s" % getUrlStr(source)
    print "with addr : %s" % addr
    print "typetags : %s" % tags
    print "the actual data is :%s" % data
    print "---"

setOSCHandler("/print", printing_handler) # adding our function


# just checking which handlers we have added. not really needed
reportOSCHandlers()



try :
    while 1 :
        time.sleep(1)

except KeyboardInterrupt :
    print "\nClosing OSCServer."
    print "Waiting for Server-thread to finish"
    closeOSC()
    print "Done"
        
