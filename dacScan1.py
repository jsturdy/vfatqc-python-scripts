#!/bin/env python
"""
Script to measure the DAC values on the VFATs
By: Jared Sturdy (sturdy@cern.ch)
"""

import sys
from array import array
from gempython.tools.vfat_user_functions_uhal import *
from gempython.utils.gemlogger import colors,getGEMLogger

from qcoptions import parser

parser.add_option("--filename", type="string", dest="filename", default="DACData.root",
                  help="Specify Output Filename", metavar="filename")

(options, args) = parser.parse_args()

import cProfile, pstats, StringIO
pr = cProfile.Profile()
pr.enable()

gemlogger = getGEMLogger(__name__)
gemlogger.setLevel(logging.INFO)

if options.debug:
    uhal.setLogLevelTo( uhal.LogLevel.DEBUG )
else:
    uhal.setLogLevelTo( uhal.LogLevel.ERROR )

from ROOT import TFile,TTree,vector
filename = options.filename
myF = TFile(filename,'recreate')
myT = TTree('dacTree','Tree Holding CMS GEM DAC Data')

Nev = array( 'i', [ 0 ] )
Nev[0] = options.nevts
myT.Branch( 'Nev', Nev, 'Nev/I' )
dacname = vector('string')()
dacname.push_back("N/A")
myT.Branch( 'dacname', dacname )
dacinval = array( 'i', [ 0 ] )
myT.Branch( 'dacinval', dacinval, 'dacinval/I' )
dacoutval = array( 'i', [ 0 ] )
myT.Branch( 'dacoutval', dacoutval, 'dacoutval/I' )
vfatN = array( 'i', [ 0 ] )
myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
vfatID = vector('string')()
vfatID.push_back("N/A")
myT.Branch( 'vfatID', vfatID )
link = array( 'i', [ 0 ] )
myT.Branch( 'link', link, 'link/I' )
link[0] = options.gtx
shelf = array( 'i', [ 0 ] )
myT.Branch( 'shelf', shelf, 'shelf/I' )
shelf[0] = options.shelf
utime = array( 'i', [ 0 ] )
myT.Branch( 'utime', utime, 'utime/I' )

import subprocess,datetime,time
utime[0] = int(time.time())
startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
print startTime
Date = startTime

ohboard = getOHObject(options.slot,options.gtx,options.shelf,options.debug)

N_EVENTS = Nev[0]
dacmode = {
    "IPREAMPIN"   : [1, None, 0,"IPreampIn"],
    "IPREAMPFEED" : [2, None, 0,"IPreampFeed"],
    "IPREAMPOUT"  : [3, None, 0,"IPreampOut"],
    "ISHAPER"     : [4, None, 0,"IShaper"],
    "ISHAPERFEED" : [5, None, 0,"IShaperFeed"],
    "ICOMP"       : [6, None, 0,"IComp"],
    "VTHRESHOLD1" : [7, None, 1,"VThreshold1"],
    "VTHRESHOLD2" : [8, None, 1,"VThreshold2"],
    "VCAL"        : [9, None, 1,"VCal"],
    "CALOUTVHI"   : [10,1,    1,"VCal"],
    "CALOUTVLOW"  : [10,2,    1,"VCal"],
}

adcReg = {
    0:["VAUX.VAL_4", "VAUX.VAL_1"],
    1:["VAUX.VAL_6", "VAUX.VAL_5"],
    2:["VAUX.VAL_13","VPVN"],
}

try:
    # calibration correction seems to already be applied
    # for i in range(4):
    #     oldval = readRegister(ohboard,"GEM_AMC.OH.OH%d.ADC.CONTROL.CONF_REG.CAL%d"%(options.gtx,i))
    #     writeRegister(ohboard,"GEM_AMC.OH.OH%d.ADC.CONTROL.CONF_REG.CAL%d"%(options.gtx,i),0x1)
    #     newval = readRegister(ohboard,"GEM_AMC.OH.OH%d.ADC.CONTROL.CONF_REG.CAL%d"%(options.gtx,i))
    #     print "CAL%d old/new = 0x%x/0x%x"%(i,oldval,newval)
    #     pass
    writeAllVFATs(ohboard, options.gtx, "ContReg0", 0x36)
    chipIDs = getAllChipIDs(ohboard,options.gtx)
    for i in range(8):
        # replace with a broadcast?
        for col in range(3):
            writeVFAT(ohboard, options.gtx, ((col*8)+i), "ContReg0", 0x37)
            pass
        for dactype in dacmode.keys():
            sys.stdout.flush()
            dacname[0] = dactype
            dac = dacmode[dactype]
            cr0val = []
            # replace with a broadcast?
            for col in range(3):
                writeVFAT(ohboard, options.gtx, ((col*8)+i), "ContReg1", dac[0])
                if dac[1]:
                    cr0val.append(readVFAT(ohboard, options.gtx, ((col*8)+i), "ContReg0"))
                    writeval = cr0val[col]|(dac[1]<<6)
                    writeVFAT(ohboard, options.gtx, ((col*8)+i), "ContReg0", writeval)
                    pass
            for val in range(256):
                dacinval[0]  = val
                # replace with a broadcast?
                for col in range(3):
                    writeVFAT(ohboard, options.gtx, ((col*8)+i), dacmode[dactype][3], val)
                    pass
                for sample in range(N_EVENTS):
                    for col in range(3):
                        rawval       = readRegister(ohboard,"GEM_AMC.OH.OH%d.ADC.%s"%(options.gtx,adcReg[col][dacmode[dactype][2]]))
                        dacoutval[0] = (rawval >> 6)
                        vfatN[0]     = ((col*8)+i)
                        vfatID[0]    = chipIDs[vfatN[0]]
                        myT.Fill()
                        pass
                    pass
                pass
            # for col in range(3):
            #     if dac[1]:
            #         writeVFAT(ohboard, options.gtx, ((col*8)+i), "ContReg0", cr0val[col])
            #         pass
            #     pass
            pass
        for col in range(3):
            writeVFAT(ohboard, options.gtx, ((col*8)+i), "ContReg0", 0x0)
            writeVFAT(ohboard, options.gtx, ((col*8)+i), "ContReg1", 0x0)
            pass
        myT.AutoSave("SaveSelf")
        sys.stdout.flush()
        pass

except Exception as e:
    myT.AutoSave("SaveSelf")
    print "An exception occurred", e
finally:
    myF.cd()
    myT.Write()
    myF.Close()

    pr.disable()
    s = StringIO.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print s.getvalue()
