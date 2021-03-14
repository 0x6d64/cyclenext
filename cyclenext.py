#!/usr/bin/python

import os
import time
import platform
from subprocess import call
import sys

taskdir = r"/Users/martindemling/task"
taskcommand = "/usr/local/bin/task"
filesToWatch = ["undo.data", "backlog.data"]  # this should be enough to get all operations including sync of remote tasks
getLazyAfterSecs = 3 * 60
forceRedrawSecs_default = 10  # this also determines the resolution of "last change x ago" info
loopDelaySecs_default = 0.33


def getFileAgeSecs(filename):
    t_mod = os.path.getmtime(filename)
    secondsSince = time.time() - t_mod
    return secondsSince

def getMinimalAgeSecs(pathList):
    ages = []
    for filename in pathList:
        ages.append(getFileAgeSecs(filename))
    return min(ages)

def redraw(limit, filterstring):
    
    limitstring = "limit:" + str(limit)
    minutesAgo = getMinimalAgeSecs(pathList) / 60
    
    clearTerminal()
    if minutesAgo < 60:
        print("last change %1.0f minutes ago" % (minutesAgo))
    elif minutesAgo < (24 * 60):
        print("last change %1.1f hours ago" % (minutesAgo / 60))
    else:
        print("last change %1.1f days ago" % (minutesAgo / (24 * 60)))
    call([taskcommand, filterstring, "rc.gc=off", limitstring])
    pass

def clearTerminal():
    os.system('cls' if platformIsWindows else "clear")
    
def calcLimit(termsize):
    tlines = int(termsize[0])
    tcols = int(termsize[1])
    if tcols > 90:
        factor = 0.6
    elif tcols > 65:
        factor = 0.4
    else:
        factor = 0.2
    limit = int(tlines * factor)
    return (limit if limit > 0 else 1)

# prepare
platformIsWindows = (platform.system() == "Windows")
pathList = []
for filename in filesToWatch:
    pathToAppend = os.path.join(taskdir, filename)
    if os.path.isfile(pathToAppend):
        pathList.append(pathToAppend)
timeSinceRedrawSecs = 0.0
termsizeOld = (0, 0)
filter = sys.argv[1] if len(sys.argv) > 1 else 'ready' # use ready as default filter

try:
    while True:
        termsize = os.popen('stty size', 'r').read().split()
        fileAgeSecs = getMinimalAgeSecs(pathList)
        lazyFactor = 5 if (fileAgeSecs > getLazyAfterSecs) else 1
        forceRedrawSecs = forceRedrawSecs_default * lazyFactor
        loopDelaySecs = loopDelaySecs_default * lazyFactor
        
        termSizeChanged = (termsize != termsizeOld)
        forceRedraw = (timeSinceRedrawSecs > forceRedrawSecs)
        fileChanged = (fileAgeSecs < (loopDelaySecs * 1.8))
            
        if termSizeChanged or forceRedraw or fileChanged:
            redraw(calcLimit(termsize), filter)
#             print('\a') # terminal bell for debug
            timeSinceRedrawSecs = 0
            time.sleep(loopDelaySecs)
            
        time.sleep(loopDelaySecs)
        timeSinceRedrawSecs += loopDelaySecs
        termsizeOld = termsize
except KeyboardInterrupt:
    print("   bye!")
