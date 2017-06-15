#!/bin/env python

def launch(args):
  return launchArgs(*args)

def launchArgs(tool, slot, link, chamber, scanmin, scanmax, nevts,
               vt1=None,vt2=0,mspl=None,
               perchannel=False,trkdata=False,ztrim=4.0,config=False):
  import datetime,os,sys
  import subprocess
  from subprocess import CalledProcessError
  from chamberInfo import chamber_config
  from gempython.utils.wrappers import runCommand

  startTime = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M")
  dataPath = os.getenv('DATA_PATH')

  scanType = "vt1"
  dataType = "VT1Threshold"
  dirPath  = None

  # Build Commands
  setupCmds = []
  preCmd    = None
  cmd       = ["time", "%s"%(tool),"-s%d"%(slot),"-g%d"%(link)]

  if tool == "ultraScurve.py":
    scanType = "scurve"
    dataType = "SCurve"
    dirPath  = "%s/%s/%s/"%(dataPath,chamber_config[link],scanType)
    setupCmds.append( ["mkdir","-p",dirPath+startTime] )
    setupCmds.append( ["unlink",dirPath+"current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"current"] )
    dirPath = dirPath+startTime
    cmd.append( "--filename=%s/SCurveData.root"%dirPath )
    if mspl:
      cmd.append( "--mspl=%d"%(mspl) )
    preCmd = ["confChamber.py","-s%d"%(slot),"-g%d"%(link)]
    if vt1 in range(256):
      preCmd.append("--vt1=%d"%(vt1))
      pass
    pass
  elif tool == "trimChamber.py":
    scanType = "trim"
    dataType = None
    preCmd   = ["confChamber.py","-s%d"%(slot),"-g%d"%(link)]
    if vt1 in range(256):
      preCmd.append("--vt1=%d"%(vt1))
      pass
    dirPath = "%s/%s/%s/z%f/"%(dataPath,chamber_config[link],scanType,ztrim)
    setupCmds.append( ["mkdir","-p",dirPath+startTime] )
    setupCmds.append( ["unlink",dirPath+"current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"current"] )
    dirPath = dirPath+startTime
    cmd.append("--ztrim=%f"%(ztrim))
    if vt1 in range(256):
      cmd.append("--vt1=%d"%(vt1))
      pass
    cmd.append( "--dirPath=%s"%dirPath )
    pass
  elif tool == "ultraThreshold.py":
    scanType = "threshold"
    if vt2 in range(256):
      cmd.append("--vt2=%d"%(vt2))
      pass
    if perchannel:
      cmd.append("--perchannel")
      scanType = scanType + "/channel"
      pass
    else:
      scanType = scanType + "/vfat"
      if trkdata:
        cmd.append("--trkdata")
        scanType = scanType + "/trk"
        pass
      else:
        scanType = scanType + "/trig"
        pass
      pass
    dirPath = "%s/%s/%s/"%(dataPath,chamber_config[link],scanType)
    setupCmds.append( ["mkdir","-p",dirPath+startTime] )
    setupCmds.append( ["unlink",dirPath+"current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"current"] )
    dirPath = dirPath+startTime
    cmd.append( "--filename=%s/ThresholdScanData.root"%dirPath )
    pass
  elif tool == "fastLatency.py":
    scanType = "latency/trig"
    dirPath  = "%s/%s/%s/"%(dataPath,chamber_config[link],scanType)
    setupCmds.append( ["mkdir","-p",dirPath+startTime] )
    setupCmds.append( ["unlink",dirPath+"current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"current"] )
    dirPath = dirPath+startTime
    cmd.append( "--filename=%s/FastLatencyScanData.root"%dirPath )
    cmd.append( "--nevts=%d"%(nevts) )
    if mspl:
      cmd.append( "--mspl=%d"%(mspl) )
    pass
  elif tool == "ultraLatency.py":
    scanType = "latency/trk"
    dirPath  = "%s/%s/%s/"%(dataPath,chamber_config[link],scanType)
    setupCmds.append( ["mkdir","-p",dirPath+startTime] )
    setupCmds.append( ["unlink",dirPath+"current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"current"] )
    dirPath = dirPath+startTime
    cmd.append( "--filename=%s/LatencyScanData.root"%dirPath )
    cmd.append( "--scanmin=%d"%(scanmin) )
    cmd.append( "--scanmax=%d"%(scanmax) )
    cmd.append( "--nevts=%d"%(nevts) )
    if mspl:
      cmd.append( "--mspl=%d"%(mspl) )
    pass
  elif tool == "dacScan.py":
    scanType = "dacscan"
    dirPath  = "%s/%s/%s/"%(dataPath,chamber_config[link],scanType)
    setupCmds.append( ["mkdir","-p",dirPath+startTime] )
    setupCmds.append( ["unlink",dirPath+"current"] )
    setupCmds.append( ["ln","-s",startTime,dirPath+"current"] )
    dirPath = dirPath+startTime
    cmd.append( "--filename=%s/DACScanData.root"%dirPath )
    cmd.append( "--nevts=%d"%(nevts) )
    pass

  # Execute Commands
  try:
    for setupCmd in setupCmds:
      print setupCmd
      runCommand(setupCmd)
      pass
    log = file("%s/scanLog.log"%(dirPath),"w")
    if preCmd and config:
      print preCmd
      runCommand(preCmd,log)
      pass
    print cmd
    runCommand(cmd,log)
  except CalledProcessError as e:
    print "Caught exception",e
    pass
  return

if __name__ == '__main__':

  import sys,os,signal
  import subprocess
  import itertools
  from multiprocessing import Pool, freeze_support
  from chamberInfo import chamber_config
  from gempython.utils.wrappers import envCheck

  from qcoptions import parser

  parser.add_option("--series", action="store_true", dest="series",
                    help="Run tests in series (default is false)", metavar="series")
  parser.add_option("--config", action="store_true", dest="config",
                    help="Configure chambers before running scan", metavar="config")
  parser.add_option("--tool", type="string", dest="tool",default="ultraScurve.py",
                    help="Tool to run (scan or analyze", metavar="tool")
  parser.add_option("--vt1", type="int", dest="vt1", default=100,
                    help="Specify VT1 to use", metavar="vt1")
  parser.add_option("--vt2", type="int", dest="vt2", default=0,
                    help="Specify VT2 to use", metavar="vt2")
  parser.add_option("--mspl", type="int", dest = "MSPL", default = 4,
                    help="Specify MSPL.  Must be in the range 1-8", metavar="MSPL")
  parser.add_option("--perchannel", action="store_true", dest="perchannel",
                    help="Run a per-channel VT1 scan", metavar="perchannel")
  parser.add_option("--trkdata", action="store_true", dest="trkdata",
                    help="Run a per-VFAT VT1 scan using tracking data (default is to use trigger data)", metavar="trkdata")

  (options, args) = parser.parse_args()

  envCheck('DATA_PATH')
  envCheck('BUILD_HOME')

  if options.tool not in ["trimChamber.py","ultraThreshold.py","ultraLatency.py","fastLatency.py","ultraScurve.py","dacScan.py"]:
    print "Invalid tool specified"
    exit(1)

  if options.debug:
    print itertools.izip([options.tool for x in range(len(chamber_config))],
                         [options.slot for x in range(len(chamber_config))],
                         chamber_config.keys(),
                         chamber_config.values(),
                         [options.scanmin for x in range(len(chamber_config))],
                         [options.scanmax for x in range(len(chamber_config))],
                         [options.nevts   for x in range(len(chamber_config))],
                         [options.vt1     for x in range(len(chamber_config))],
                         [options.vt2     for x in range(len(chamber_config))],
                         [options.MSPL    for x in range(len(chamber_config))],
                         [options.perchannel for x in range(len(chamber_config))],
                         [options.trkdata for x in range(len(chamber_config))],
                         [options.ztrim   for x in range(len(chamber_config))],
                         [options.config  for x in range(len(chamber_config))],
                         )

  if options.series:
    print "Running jobs in serial mode"
    for link in chamber_config.keys():
      chamber = chamber_config[link]
      launch([options.tool,options.slot,link,chamber,
              options.vt2,options.MSPL,
              options.perchannel,options.trkdata,options.ztrim,options.config])
      pass
    pass
  else:
    print "Running jobs in parallel mode (using Pool(12))"
    freeze_support()
    # from: https://stackoverflow.com/questions/11312525/catch-ctrlc-sigint-and-exit-multiprocesses-gracefully-in-python
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    pool = Pool(12)
    signal.signal(signal.SIGINT, original_sigint_handler)
    try:
      res = pool.map_async(launch,
                           itertools.izip([options.tool for x in range(len(chamber_config))],
                                          [options.slot for x in range(len(chamber_config))],
                                          chamber_config.keys(),
                                          chamber_config.values(),
                                          [options.scanmin for x in range(len(chamber_config))],
                                          [options.scanmax for x in range(len(chamber_config))],
                                          [options.nevts   for x in range(len(chamber_config))],
                                          [options.vt1     for x in range(len(chamber_config))],
                                          [options.vt2     for x in range(len(chamber_config))],
                                          [options.MSPL    for x in range(len(chamber_config))],
                                          [options.perchannel for x in range(len(chamber_config))],
                                          [options.trkdata for x in range(len(chamber_config))],
                                          [options.ztrim   for x in range(len(chamber_config))],
                                          [options.config  for x in range(len(chamber_config))],
                                          )
                           )
      # timeout must be properly set, otherwise tasks will crash
      print res.get(999999999)
      print("Normal termination")
      pool.close()
      pool.join()
    except KeyboardInterrupt:
      print("Caught KeyboardInterrupt, terminating workers")
      pool.terminate()
    except Exception as e:
      print("Caught Exception %s, terminating workers"%(str(e)))
      pool.terminate()
    except: # catch *all* exceptions
      e = sys.exc_info()[0]
      print("Caught non-Python Exception %s"%(e))
      pool.terminate()
