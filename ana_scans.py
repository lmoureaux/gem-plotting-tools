#! /usr/bin/env python
"""
@author: Cameron Bravo (c.bravo@cern.ch)
         Brian Dorney (brian.l.dorney@cern.ch)

"""
def launchAna(args):
  return launchAnaArgs(*args)

def launchAnaArgs(anaType, cName, cType, scandate, scandatetrim=None, ztrim=4.0, chConfigKnown=False, channels=False, panasonic=False):
  import os
  import subprocess
  from subprocess import CalledProcessError
  from anaInfo import ana_config
  from gempython.utils.wrappers import runCommand

  dataPath  = os.getenv('DATA_PATH')
  dirPath   = ""
  elogPath  = "%s/%s"%(os.getenv('ELOG_PATH'),scandate)
    
  print "Analysis Requested: %s"%(anaType)

  #Build Commands
  cmd = [ana_config[anaType]]
  postCmds = []
  postCmds.append(["mkdir","-p","%s"%(elogPath)])
  if anaType == "latency":
    dirPath = "%s/%s/%s/trk/%s/"%(dataPath,cName,anaType,scandate)
    filename = dirPath + "LatencyScanData.root"
    if not os.path.isfile(filename):
      print "No file to analyze. %s does not exist"%(filename)
      return
    
    cmd.append("--infilename=%s"%(filename))
    cmd.append("--outfilename=%s"%("latencyAna.root"))
    
    postCmds.append(["cp","%s/LatencyScanData/Summary.png"%(dirPath),
                 "%s/LatencySumary_%s.png"%(elogPath,cName)])
    postCmds.append(["cp","%s/LatencyScanData/MaxHitsPerLatByVFAT.png"%(dirPath),
                 "%s/MaxHitsPerLatByVFAT_%s.png"%(elogPath,cName)])
    postCmds.append(["cp","%s/LatencyScanData/SignalOverSigPBkg.png"%(dirPath),
                 "%s/SignalOverSigPBkg_%s.png"%(elogPath,cName)])
    
    pass
  elif anaType == "scurve":
    dirPath = "%s/%s/%s/%s/"%(dataPath,cName,anaType,scandate)
    filename = dirPath + "SCurveData.root"
    if not os.path.isfile(filename):
      print "No file to analyze. %s does not exist"%(filename)
      return

    cmd.append("--infilename=%s"%(filename))
    cmd.append("--outfilename=%s"%("SCurveFitData.root"))
    cmd.append("--fit")
    cmd.append("--type=%s"%(cType))
    if channels:
        cmd.append("--channels")
        pass
    if panasonic:
        cmd.append("--panasonic")
        pass

    postCmds.append(["cp","%s/SCurveData/Summary.png"%(dirPath),
                 "%s/SCurveSummary_%s_ztrim%2.2f.png"%(elogPath,cName,ztrim)])
    postCmds.append(["cp","%s/SCurveData/chConfig.txt"%(dirPath),
                 "%s/chConfig_%s_ztrim%2.2f.txt"%(elogPath,cName,ztrim)])
    pass
  elif anaType == "threshold":
    dirPath = "%s/%s/%s/channel/%s/"%(dataPath,cName,anaType,scandate)
    filename = dirPath + "ThresholdScanData.root"
    if not os.path.isfile(filename):
      print "No threshold file to analyze. %s does not exist"%(filename)
      return

    cmd.append("--infilename=%s"%(filename))
    cmd.append("--outfilename=%s"%("ThresholdPlots.root"))
   
    if chConfigKnown:
      cmd.append("--chConfigKnown")
      dirPath_Trim = "%s/%s/trim/z%f/%s/SCurveData_Trimmed/"%(dataPath,cName,ztrim,scandatetrim)
      filename_Trim = dirPath_Trim + "SCurveFitData.root"
      if not os.path.isfile(filename_Trim):
        print "No scurve fit data file to analyze. %s does not exist"%(filename_Trim)
        return
      
      cmd.append("--fileScurveFitTree=%s"%(filename_Trim))
      pass

    postCmds.append(["cp","%s/ThresholdScanData/ThreshSummary.png"%(dirPath),
                   "%s/ThreshSummary_%s.png"%(elogPath,cName)])
    postCmds.append(["cp","%s/ThresholdScanData/ThreshPrunedSummary.png"%(dirPath),
                   "%s/ThreshPrunedSummary_%s.png"%(elogPath,cName)])
    postCmds.append(["cp","%s/ThresholdScanData/vfatConfig.txt"%(dirPath),
                   "%s/vfatConfig_%s.txt"%(elogPath,cName)])
    if chConfigKnown:
      postCmds.append(["cp","%s/ThresholdScanData/chConfig_MasksUpdated.txt"%(dirPath),
                     "%s/chConfig_MasksUpdated_%s.txt"%(elogPath,cName)])
      pass
    pass
  elif anaType == "trim":
    dirPath = "%s/%s/%s/z%f/%s/"%(dataPath,cName,anaType,ztrim,scandate)
    filename = dirPath + "SCurveData_Trimmed.root"
    if not os.path.isfile(filename):
      print "No file to analyze. %s does not exist"%(filename)
      return

    cmd.append("--infilename=%s"%(filename))
    cmd.append("--outfilename=%s"%("SCurveFitData.root"))
    cmd.append("--fit")
    cmd.append("--type=%s"%(cType))
    if channels:
        cmd.append("--channels")
        pass
    if panasonic:
        cmd.append("--panasonic")
        pass
        
    postCmds.append(["cp","%s/SCurveData_Trimmed/Summary.png"%(dirPath),
                 "%s/SCurveSummaryTrimmed_%s_ztrim%2.2f.png"%(elogPath,cName,ztrim)])
    postCmds.append(["cp","%s/SCurveData_Trimmed/chConfig.txt"%(dirPath),
                 "%s/chConfigTrimmed_%s_ztrim%2.2f.txt"%(elogPath,cName,ztrim)])
    pass

  #Execute Commands
  try:
    log = file("%s/anaLog.log"%(dirPath),"w")
 
    #runCommand(cmd,log)
    runCommand(cmd)
    for item in postCmds:
      runCommand(item)
      pass
  except CalledProcessError as e:
    print "Caught exception",e
    pass
  return

if __name__ == '__main__':
  import sys,os,signal
  import subprocess
  import itertools
  from multiprocessing import Pool, freeze_support
  from mapping.chamberInfo import chamber_config, GEBtype
  from anaInfo import ana_config
  from gempython.utils.wrappers import envCheck

  from anaoptions import parser

  parser.add_option("--series", action="store_true", dest="series",
                    help="Run tests in series (default is false)", metavar="series")
  parser.add_option("--anaType", type="string", dest="anaType",
                     help="Analysis type to be executed, from list {'latency','scurve','threshold','trim'}", metavar="anaType")

  (options, args) = parser.parse_args()

  envCheck('BUILD_HOME')
  envCheck('DATA_PATH')
  envCheck('ELOG_PATH')

  if options.anaType not in ana_config.keys():
    print "Invalid analysis specificed, please select only from the list:"
    print ana_config.keys()
    exit(1)
    pass

  if options.debug:
    print list(itertools.izip([options.anaType for x in range(len(chamber_config))],
                         chamber_config.values(),
                         [GEBtype[x]        for x in chamber_config.keys()],
                         [options.scandate  for x in range(len(chamber_config))],
                         [options.scandatetrim  for x in range(len(chamber_config))],
                         [options.ztrim   for x in range(len(chamber_config))],
                         [options.chConfigKnown   for x in range(len(chamber_config))],
                         [options.channels   for x in range(len(chamber_config))],
                         [options.PanPin   for x in range(len(chamber_config))]
                         )
              )

  if options.series:
    print "Running jobs in serial mode"
    for link in chamber_config.keys():
      chamber = chamber_config[link]
      launchAna([options.anaType for x in range(len(chamber_config))],
                 chamber_config.values(),
                 [GEBtype[x]        for x in chamber_config.keys()],
                 [options.scandate  for x in range(len(chamber_config))],
                 [options.scandatetrim  for x in range(len(chamber_config))],
                 [options.ztrim   for x in range(len(chamber_config))],
                 [options.chConfigKnown   for x in range(len(chamber_config))],
                 [options.channels   for x in range(len(chamber_config))],
                 [options.PanPin   for x in range(len(chamber_config))]
               )
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
      res = pool.map_async(launchAna,
                           itertools.izip([options.anaType for x in range(len(chamber_config))],
                                          chamber_config.values(),
                                          [GEBtype[x]        for x in chamber_config.keys()],
                                          [options.scandate  for x in range(len(chamber_config))],
                                          [options.scandatetrim  for x in range(len(chamber_config))],
                                          [options.ztrim   for x in range(len(chamber_config))],
                                          [options.chConfigKnown   for x in range(len(chamber_config))],
                                          [options.channels   for x in range(len(chamber_config))],
                                          [options.PanPin   for x in range(len(chamber_config))]
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
