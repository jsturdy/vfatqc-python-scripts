#!/bin/env python
"""
Script to measure the DAC values on the VFATs
By: Jared Sturdy (sturdy@cern.ch)
"""

def printUpdate(counter,total,stepSize,width,header,new=False,special=None):
    import sys,time
    compper = 100.*(1.0*counter/total)
    comp = "%2d %%"%(compper)
    counts = counter/stepSize
    clear  = '\033[K'
    backup = '\033[1A'
    if (special):
        backup  = '\033[1A'
        sys.stdout.write("\n%si'm special! %s\n%s%s"%(clear,special,backup,backup))
        pass
    if new:
        sys.stdout.write("\n%s[%s: %s%s %s]"%(clear,header,"-"*counts," "*(width-counts),comp))
    else:
        sys.stdout.write("\n%s%s[%s: %s%s %s]"%(backup,clear,header,"-"*counts," "*(width-counts),comp))
        pass
    sys.stdout.flush()
    sys.stdout.write("\b"*(width+1-counts+1+len(comp)))
    sys.stdout.flush()
    return

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

toolbar_width = 100
total   = len(dacmode.keys())*256*N_EVENTS*3
stepSize = total/toolbar_width

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

    print("Looping over iEta sectors")

    for i in range(8):
        counter = 0
        printUpdate(counter,total,stepSize,toolbar_width,"iEta%d"%(i),True)
        colmask = (((((0x1<<8)|0x1)<<8)|0x1)<<i)
        colmask = 0xfffffff&(~colmask)
        writeAllVFATs(ohboard, options.gtx, "ContReg0", 0x37, mask=colmask)

        for dactype in dacmode.keys():
            printUpdate(counter,total,stepSize,toolbar_width,"iEta%d"%(i),False,"%s"%(dactype))
            sys.stdout.flush()
            dacname[0] = dactype
            dac = dacmode[dactype]
            cr0val = []
            writeAllVFATs(ohboard, options.gtx, "ContReg1", dac[0], mask=colmask)

            if dac[1] > 0:
                cr0val= 0x37
                writeval = cr0val|(dac[1]<<6)
                writeAllVFATs(ohboard, options.gtx, "ContReg0", writeval,mask=colmask)
                pass

            for val in range(256):
                dacinval[0]  = val
                writeAllVFATs(ohboard, options.gtx, dacmode[dactype][3], val, mask=colmask)

                for sample in range(N_EVENTS):
                    for col in range(3):
                        rawval       = readRegister(ohboard,"GEM_AMC.OH.OH%d.ADC.%s"%(options.gtx,adcReg[col][dacmode[dactype][2]]))
                        dacoutval[0] = (rawval >> 6)
                        vfatN[0]     = ((col*8)+i)
                        vfatID[0]    = chipIDs[vfatN[0]]
                        myT.Fill()

                        if (counter%stepSize == 0):
                            printUpdate(counter,total,stepSize,toolbar_width,"iEta%d"%(i))
                            pass
                        counter+=1
                        pass
                    pass
                pass

            # reset the DAC value after the loop?
            writeAllVFATs(ohboard, options.gtx, dacmode[dactype][3], 0, mask=colmask)
            pass

        writeAllVFATs(ohboard, options.gtx, "ContReg0", 0x0, mask=colmask)
        writeAllVFATs(ohboard, options.gtx, "ContReg1", 0x0, mask=colmask)

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
