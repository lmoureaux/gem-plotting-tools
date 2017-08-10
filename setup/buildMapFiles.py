import os
from channelMaps import *
from PanChannelMaps import *
chamberType = ['long','short']

buildHome = os.environ.get('BUILD_HOME')
baseDir = '%s/gem-plotting-tools/setup'%buildHome

for cT in chamberType:
    outF = open('%s/%sChannelMap.txt'%(baseDir,cT),'w')
    outF.write('vfat/I:strip/I:channel/I:PanPin/I\n')
    for vfat in range(0,24):
        for strip in range(0,128):
            channel = stripToChannel(cT,vfat,strip)
            panpin = StripToPan(cT, vfat, strip)
            outF.write('%i\t%i\t%i\t%i\n'%(vfat,strip,channel+1,panpin))
            pass
        pass
    outF.close()
    pass

