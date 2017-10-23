#!/bin/env python
"""
Script to take Scurve data using OH ultra scans
By: Cameron Bravo (c.bravo@cern.ch)
"""

import sys
from array import array
from gempython.tools.vfat_user_functions_uhal import *

from qcoptions import parser

parser.add_option("-f", "--filename", type="string", dest="filename", default="SCurveData.root",
                  help="Specify Output Filename", metavar="filename")
parser.add_option("--latency", type="int", dest = "latency", default = 37,
                  help="Specify Latency", metavar="latency")
parser.add_option("--CalPhase", type="int", dest = "CalPhase", default = 0,
                  help="Specify CalPhase. Must be in range 0-8", metavar="CalPhase")
parser.add_option("--L1Atime", type="int", dest = "L1Atime", default = 250,
                  help="Specify time between L1As in bx", metavar="L1Atime")
parser.add_option("--pulseDelay", type="int", dest = "pDel", default = 40,
                  help="Specify time of pulse before L1A in bx", metavar="pDel")
parser.add_option("--chMin", type="int", dest = "chMin", default = 0,
                  help="Specify minimum channel number to scan", metavar="chMin")
parser.add_option("--chMax", type="int", dest = "chMax", default = 127,
                  help="Specify maximum channel number to scan", metavar="chMax")

(options, args) = parser.parse_args()

if options.MSPL < 1 or options.MSPL > 8:
    print 'MSPL must be in the range 1-8'
    exit(1)
    pass
if options.CalPhase < 0 or options.CalPhase > 8:
    print 'CalPhase must be in the range 0-8'
    exit(1)
    pass
if not (0 <= options.chMin <= options.chMax < 128):
    print "chMin %d not in [0,%d] or chMax %d not in [%d,127] or chMax < chMin"%(options.chMin,options.chMax,options.chMax,options.chMin)
    exit(1)
    pass

if options.debug:
    uhal.setLogLevelTo( uhal.LogLevel.INFO )
else:
    uhal.setLogLevelTo( uhal.LogLevel.ERROR )

import ROOT as r
filename = options.filename
myF = r.TFile(filename,'recreate')

# Setup the output TTree
from treeStructure import gemTreeStructure
gemData = gemTreeStructure('scurveTree','Tree Holding CMS GEM SCurve Data')
gemData.calPhase[0] = options.CalPhase
gemData.l1aTime[0] = options.L1Atime
gemData.latency[0] = options.latency
gemData.link[0] = options.gtx
gemData.mspl[0] = options.MSPL
gemData.Nev[0] = options.nevts
gemData.pDel[0] = options.pDel

import subprocess,datetime,time
gemData.utime[0] = int(time.time())
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print startTime
Date = startTime

ohboard = getOHObject(options.slot,options.gtx,options.shelf,options.debug)

SCURVE_MIN = 0
SCURVE_MAX = 254

N_EVENTS = gemData.Nev[0]
CHAN_MIN = options.chMin
CHAN_MAX = options.chMax + 1
if options.debug:
    CHAN_MAX = 5
    pass

mask = options.vfatmask

try:
    setTriggerSource(ohboard,options.gtx,1)
    configureLocalT1(ohboard, options.gtx, 1, 0, options.pDel, options.L1Atime, 0, options.debug)
    startLocalT1(ohboard, options.gtx)

    print 'Link %i T1 controller status: %i'%(options.gtx,getLocalT1Status(ohboard,options.gtx))

    writeAllVFATs(ohboard, options.gtx, "Latency",    options.latency, mask)
    writeAllVFATs(ohboard, options.gtx, "ContReg0", 0x37, mask)
    writeAllVFATs(ohboard, options.gtx, "ContReg2",   (options.MSPL - 1) << 4, mask)
    writeAllVFATs(ohboard, options.gtx, "CalPhase",  0xff >> (8 - options.CalPhase), mask)

    for vfat in range(0,24):
        if (mask >> vfat) & 0x1: continue
        for scCH in range(CHAN_MIN,CHAN_MAX):
            trimVal = (0x3f & readVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH)))
            writeVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),trimVal)

    gemData.mode[0] = scanmode.SCURVE
    for scCH in range(CHAN_MIN,CHAN_MAX):
        gemData.vfatCH[0] = scCH
        print "Channel #"+str(scCH)
        for vfat in range(0,24):
            if (mask >> vfat) & 0x1: continue
            trimVal = (0x3f & readVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH)))
            writeVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),trimVal+64)
        configureScanModule(ohboard, options.gtx, gemData.mode[0], mask, channel = scCH,
                            scanmin = SCURVE_MIN, scanmax = SCURVE_MAX, numtrigs = int(N_EVENTS),
                            useUltra = True, debug = options.debug)
        printScanConfiguration(ohboard, options.gtx, useUltra = True, debug = options.debug)
        startScanModule(ohboard, options.gtx, useUltra = True, debug = options.debug)
        scanData = getUltraScanResults(ohboard, options.gtx, SCURVE_MAX - SCURVE_MIN + 1, options.debug)
        for i in range(0,24):
            if (mask >> i) & 0x1: continue
            gemData.vfatN[0] = i
            dataNow = scanData[i]
            gemData.trimRange[0] = (0x07 & readVFAT(ohboard,options.gtx, i,"ContReg3"))
            gemData.trimDAC[0]   = (0x1f & readVFAT(ohboard,options.gtx, i,"VFATChannels.ChanReg%d"%(scCH)))
            gemData.vth1[0]      = (0xff & readVFAT(ohboard,options.gtx, i,"VThreshold1"))
            for VC in range(SCURVE_MAX-SCURVE_MIN+1):
                try:
                    gemData.vcal[0]  = int((dataNow[VC] & 0xff000000) >> 24)
                    gemData.Nhits[0] = int(dataNow[VC] & 0xffffff)
                except IndexError:
                    print 'Unable to index data for channel %i'%scCH
                    print dataNow
                    gemData.vcal[0]  = -99
                    gemData.Nhits[0] = -99
                finally:
                    gemData.gemTree.Fill()
        for vfat in range(0,24):
            if (mask >> vfat) & 0x1: continue
            trimVal = (0x3f & readVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH)))
            writeVFAT(ohboard,options.gtx,vfat,"VFATChannels.ChanReg%d"%(scCH),trimVal)
        gemData.gemTree.AutoSave("SaveSelf")
        sys.stdout.flush()
        pass
    stopLocalT1(ohboard, options.gtx)
    writeAllVFATs(ohboard, options.gtx, "ContReg0",    0x36, mask)

except Exception as e:
    gemData.gemTree.AutoSave("SaveSelf")
    print "An exception occurred", e
finally:
    myF.cd()
    gemData.gemTree.Write()
    myF.Close()
