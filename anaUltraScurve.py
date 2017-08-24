#! /usr/bin/env python
import os
import numpy as np
from optparse import OptionParser
from array import array
from anautilities import *
from anaInfo import *
from fitting.fitScanData import *
from mapping.channelMaps import *
from mapping.PanChannelMaps import *
from gempython.utils.nesteddict import nesteddict as ndict

from anaoptions import parser

parser.add_option("-b", "--drawbad", action="store_true", dest="drawbad",
                  help="Draw fit overlays for Chi2 > 10000", metavar="drawbad")
parser.add_option("-f", "--fit", action="store_true", dest="SaveFile",
                  help="Save the Fit values to Root file", metavar="SaveFile")
parser.add_option("--IsTrimmed", action="store_true", dest="IsTrimmed",
                  help="If the data is from a trimmed scan, plot the value it tried aligning to", metavar="IsTrimmed")
parser.add_option("--zscore", type="float", dest="zscore", default=3.5,
                  help="Z-Score for Outlier Identification in MAD Algo", metavar="zscore")
parser.set_defaults(outfilename="SCurveData.root")

(options, args) = parser.parse_args()
filename = options.filename[:-5]
os.system("mkdir " + filename)

print filename
outfilename = options.outfilename

vToQb = -0.8
vToQm = 0.05

import ROOT as r
r.gROOT.SetBatch(True)
r.gStyle.SetOptStat(1111111)
GEBtype = options.GEBtype
inF = r.TFile(filename+'.root')
if options.SaveFile:
    outF = r.TFile(filename+'/'+outfilename, 'recreate')
    myT = r.TTree('scurveFitTree','Tree Holding FitData')
    pass

#Build the channel to strip mapping from the text file
chanToStripLUT = []
stripToChanLUT = []
chanToPanPinLUT = []
for vfat in range(0,24):
    chanToStripLUT.append([])
    stripToChanLUT.append([])
    chanToPanPinLUT.append([])
    for channel in range(0,128):
        chanToStripLUT[vfat].append(0)
        stripToChanLUT[vfat].append(0)
        chanToPanPinLUT[vfat].append(0)
        pass
    pass

from gempython.utils.wrappers import envCheck
envCheck('GEM_PLOTTING_PROJECT')

projectHome = os.environ.get('GEM_PLOTTING_PROJECT')
if GEBtype == 'long':
    intext = open(projectHome+'/mapping/longChannelMap.txt', 'r')
    pass
if GEBtype == 'short':
    intext = open(projectHome+'/mapping/shortChannelMap.txt', 'r')
    pass

for i, line in enumerate(intext):
    if i == 0: continue
    mapping = line.rsplit('\t')
    chanToStripLUT[int(mapping[0])][int(mapping[2]) - 1] = int(mapping[1])
    stripToChanLUT[int(mapping[0])][int(mapping[1])] = int(mapping[2]) - 1
    chanToPanPinLUT[int(mapping[0])][int(mapping[2]) -1] = int(mapping[3])
    pass

if options.IsTrimmed:
    trimmed_text = open('scanInfo.txt', 'r')
    trimVcal = []
    for vfat in range(0,24):
        trimVcal.append(0)
        pass
    for n, line in enumerate(trimmed_text):
        if n == 0: continue
        print line
        scanInfo = line.rsplit('  ')
        trimVcal[int(scanInfo[0])] = float(scanInfo[4])
        pass
    pass

if options.SaveFile:
    vfatN = array( 'i', [ 0 ] )
    myT.Branch( 'vfatN', vfatN, 'vfatN/I' )
    vfatCH = array( 'i', [ 0 ] )
    myT.Branch( 'vfatCH', vfatCH, 'vfatCH/I' )
    ROBstr = array( 'i', [ 0 ] )
    myT.Branch( 'ROBstr', ROBstr, 'ROBstr/I' )
    mask = array( 'i', [ 0 ] )
    myT.Branch( 'mask', mask, 'mask/I' )
    maskReason = array( 'i', [ 0 ] )
    myT.Branch( 'maskReason', maskReason, 'maskReason/I' )
    panPin = array( 'i', [ 0 ] )
    myT.Branch( 'panPin', panPin, 'panPin/I' )
    trimRange = array( 'i', [ 0 ] )
    myT.Branch( 'trimRange', trimRange, 'trimRange/I' )
    vthr = array( 'i', [ 0 ] )
    myT.Branch( 'vthr', vthr, 'vthr/I' )
    trimDAC = array( 'i', [ 0 ] )
    myT.Branch( 'trimDAC', trimDAC, 'trimDAC/I' )
    threshold = array( 'f', [ 0 ] )
    myT.Branch( 'threshold', threshold, 'threshold/F')
    noise = array( 'f', [ 0 ] )
    myT.Branch( 'noise', noise, 'noise/F')
    pedestal = array( 'f', [ 0 ] )
    myT.Branch( 'pedestal', pedestal, 'pedestal/F')
    ped_eff = array( 'f', [ 0 ] )
    myT.Branch( 'ped_eff', ped_eff, 'ped_eff/F')
    scurve_h = r.TH1D()
    myT.Branch( 'scurve_h', scurve_h)
    chi2 = array( 'f', [ 0 ] )
    myT.Branch( 'chi2', chi2, 'chi2/F')
    ndf = array( 'i', [ 0 ] )
    myT.Branch( 'ndf', ndf, 'ndf/I')
    Nhigh = array( 'i', [ 0 ] )
    myT.Branch( 'Nhigh', Nhigh, 'Nhigh/I')
    pass

vSummaryPlots = ndict()
vSummaryPlotsPanPin2 = ndict()
vSummaryPlotsPruned = ndict()
vSummaryPlotsPrunedPanPin2 = ndict()
vScurves = []
vthr_list = []
trim_list = []
trimrange_list = []
lines = []
def overlay_fit(VFAT, CHAN):
    Scurve = r.TH1D('Scurve','Scurve for VFAT %i channel %i;VCal [DAC units]'%(VFAT, CHAN),255,-0.5,254.5)
    strip = chanToStripLUT[VFAT][CHAN]
    pan_pin = chanToPanPinLUT[VFAT][CHAN]
    for event in inF.scurveTree:
        if (event.vfatN == VFAT) and (event.vfatCH == CHAN):
            Scurve.Fill(event.vcal, event.Nhits)
            pass
        pass
    param0 = scanFits[0][VFAT][CHAN]
    param1 = scanFits[1][VFAT][CHAN]
    param2 = scanFits[2][VFAT][CHAN]
    fitTF1 =  r.TF1('myERF','500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
    fitTF1.SetParameter(0, param0)
    fitTF1.SetParameter(1, param1)
    fitTF1.SetParameter(2, param2)
    canvas = r.TCanvas('canvas', 'canvas', 500, 500)
    r.gStyle.SetOptStat(1111111)
    Scurve.Draw()
    fitTF1.Draw('SAME')
    canvas.Update()
    canvas.SaveAs('Fit_Overlay_VFAT%i_Strip%i.png'%(VFAT, strip))
    return

for vfat in range(0,24):
    vScurves.append([])
    vthr_list.append([])
    trim_list.append([])
    trimrange_list.append([])
    if options.IsTrimmed:
        lines.append(r.TLine(-0.5, trimVcal[vfat], 127.5, trimVcal[vfat]))
        pass
    if not (options.channels or options.PanPin):
        vSummaryPlots[vfat] = r.TH2D('vSummaryPlots%i'%vfat,'VFAT %i;Strip;VCal [fC]'%vfat,128,-0.5,127.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSummaryPlots[vfat].GetYaxis().SetTitleOffset(1.5)
        vSummaryPlotsPruned[vfat] = r.TH2D('vSummaryPlotsPruned%i'%vfat,'VFAT %i;Strip;VCal [fC]'%vfat,128,-0.5,127.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSummaryPlotsPruned[vfat].GetYaxis().SetTitleOffset(1.5)
        pass
    if options.channels:
        vSummaryPlots[vfat] = r.TH2D('vSummaryPlots%i'%vfat,'VFAT %i;Channels;VCal [fC]'%vfat,128,-0.5,127.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSummaryPlots[vfat].GetYaxis().SetTitleOffset(1.5)
        vSummaryPlotsPruned[vfat] = r.TH2D('vSummaryPlotsPruned%i'%vfat,'VFAT %i;Channels;VCal [fC]'%vfat,128,-0.5,127.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSummaryPlotsPruned[vfat].GetYaxis().SetTitleOffset(1.5)
        pass
    if options.PanPin:
        vSummaryPlots[vfat] = r.TH2D('vSummaryPlots%i'%vfat,'VFAT %i_0-63;63 - Panasonic Pin;VCal [fC]'%vfat,64,-0.5,63.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSummaryPlots[vfat].GetYaxis().SetTitleOffset(1.5)
        vSummaryPlotsPruned[vfat] = r.TH2D('vSummaryPlotsPruned%i'%vfat,'VFAT %i_0-63;63 - Panasonic Pin;VCal [fC]'%vfat,64,-0.5,63.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSummaryPlotsPruned[vfat].GetYaxis().SetTitleOffset(1.5)
        vSummaryPlotsPanPin2[vfat] = r.TH2D('vSummaryPlotsPanPin2_%i'%vfat,'vSummaryPlots%i_64-127;127 - Panasonic Pin;VCal [fC]'%vfat,64,-0.5,63.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSummaryPlotsPanPin2[vfat].GetYaxis().SetTitleOffset(1.5)
        vSummaryPlotsPrunedPanPin2[vfat] = r.TH2D('vSummaryPlotsPrunedPanPin2_%i'%vfat,'vSummaryPlots%i_64-127;127 - Panasonic Pin;VCal [fC]'%vfat,64,-0.5,63.5,256,vToQm*-0.5+vToQb,vToQm*255.5+vToQb)
        vSummaryPlotsPrunedPanPin2[vfat].GetYaxis().SetTitleOffset(1.5)
        pass
    for chan in range (0,128):
        vScurves[vfat].append(r.TH1D('Scurve_%i_%i'%(vfat,chan),'Scurve_%i_%i;VCal [DAC units]'%(vfat,chan),256,-0.5,255.5))
        vthr_list[vfat].append(0)
        trim_list[vfat].append(0)
        trimrange_list[vfat].append(0)
        pass
    pass

if options.SaveFile:
    fitter = ScanDataFitter()
    pass

# Fill
for event in inF.scurveTree:
    strip = chanToStripLUT[event.vfatN][event.vfatCH]
    pan_pin = chanToPanPinLUT[event.vfatN][event.vfatCH]
    if not (options.channels or options.PanPin):
        vSummaryPlots[event.vfatN].Fill(strip,vToQm*event.vcal+vToQb,event.Nhits)
        pass
    if options.channels:
        vSummaryPlots[event.vfatN].Fill(event.vfatCH,vToQm*event.vcal+vToQb,event.Nhits)
        pass
    if options.PanPin:
        if (pan_pin < 64):
            vSummaryPlots[event.vfatN].Fill(63-pan_pin,vToQm*event.vcal+vToQb,event.Nhits)
            pass
        else:
            vSummaryPlotsPanPin2[event.vfatN].Fill(127-pan_pin,vToQm*event.vcal+vToQb,event.Nhits)
            pass
        pass
    x = vScurves[event.vfatN][event.vfatCH].FindBin(event.vcal)
    vScurves[event.vfatN][event.vfatCH].SetBinContent(x, event.Nhits)
    r.gStyle.SetOptStat(1111111)
    vthr_list[event.vfatN][event.vfatCH] = event.vthr
    trim_list[event.vfatN][event.vfatCH] = event.trimDAC
    trimrange_list[event.vfatN][event.vfatCH] = event.trimRange
    if options.SaveFile:
        fitter.feed(event)
        pass
    pass

if options.SaveFile:
    scanFits = fitter.fit()
    pass

# Determine hot channels
import numpy as np
if options.SaveFile:
    print 'Determining hot channels'
    masks = []
    maskReasons = []
    effectivePedestals = [ np.zeros(128) for vfat in range(24) ]
    for vfat in range(0, 24):
        trimValue = np.zeros(128)
        channelNoise = np.zeros(128)
        fitFailed = np.zeros(128, dtype=bool)
        for ch in range(0, 128):
            # Get fit results
            threshold[0] = scanFits[0][vfat][ch]
            noise[0] = scanFits[1][vfat][ch]
            pedestal[0] = scanFits[2][vfat][ch]
            # Compute values for cuts
            channelNoise[ch] = noise[0]
            FittedFunction = r.TF1('myERF','500*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+500',1,253)
            for i in range(3):
                FittedFunction.SetParameter(i, scanFits[i][vfat][ch])
                pass
            effectivePedestals[vfat][ch] = FittedFunction.Eval(0.0)
            # Compute the value to apply MAD on for each channel
            trimValue[ch] = threshold[0] - options.ztrim * noise[0]
            pass
        fitFailed = np.logical_not(fitter.fitValid[vfat])
        # Determine outliers
        hot = isOutlierMADOneSided(trimValue, thresh=options.zscore,
                                   rejectHighTail=False)
        # Create reason array
        reason = np.zeros(128, dtype=int) # Not masked
        reason[hot] |= MaskReason.HotChannel
        reason[fitFailed] |= MaskReason.FitFailed
        reason[fitter.isDead[vfat]] |= MaskReason.DeadChannel
        reason[channelNoise > 20] |= MaskReason.HighNoise
        reason[effectivePedestals[vfat] > 50] |= MaskReason.HighEffPed
        maskReasons.append(reason)
        masks.append(reason != MaskReason.NotMasked)
        print 'VFAT %2d: %d dead, %d hot channels, %d failed fits, %d high noise, %d high eff.ped.' % (vfat,
                np.count_nonzero(fitter.isDead[vfat]),
                np.count_nonzero(hot),
                np.count_nonzero(fitFailed),
                np.count_nonzero(channelNoise > 20),
                np.count_nonzero(effectivePedestals[vfat] > 50))

# Fill pruned
if options.SaveFile:
    for event in inF.scurveTree:
        if masks[event.vfatN][event.vfatCH]:
            continue
        strip = chanToStripLUT[event.vfatN][event.vfatCH]
        pan_pin = chanToPanPinLUT[event.vfatN][event.vfatCH]
        if not (options.channels or options.PanPin):
            vSummaryPlotsPruned[event.vfatN].Fill(strip,vToQm*event.vcal+vToQb,event.Nhits)
        if options.channels:
            vSummaryPlotsPruned[event.vfatN].Fill(event.vfatCH,vToQm*event.vcal+vToQb,event.Nhits)
        if options.PanPin:
            if (pan_pin < 64):
                vSummaryPlotsPruned[event.vfatN].Fill(63-pan_pin,vToQm*event.vcal+vToQb,event.Nhits)
            else:
                vSummaryPlotsPrunedPanPin2[event.vfatN].Fill(127-pan_pin,vToQm*event.vcal+vToQb,event.Nhits)

# Store values in ROOT file
if options.SaveFile:
    fitSums = {}
    for vfat in range (0,24):
        fitThr = []        
        fitENC = []
        stripList = []
        panList = []
        chanList = []
        for chan in range (0, 128):
            #Get strip and pan pin
            strip = chanToStripLUT[vfat][chan]
            pan_pin = chanToPanPinLUT[vfat][chan]
            #Store strip, chan and pan pin
            stripList.append(float(strip))
            panList.append(float(pan_pin))
            chanList.append(float(chan))
            #Filling the Branches
            param0 = scanFits[0][vfat][chan]
            param1 = scanFits[1][vfat][chan]
            param2 = scanFits[2][vfat][chan]
            ped_eff[0] = effectivePedestals[vfat][chan]
            vfatN[0] = vfat
            vfatCH[0] = chan
            ROBstr[0] = strip
            panPin[0] = pan_pin
            trimRange[0] = trimrange_list[vfat][chan] 
            vthr[0] = vthr_list[vfat][chan]
            trimDAC[0] = trim_list[vfat][chan]
            threshold[0] = param0
            fitThr.append(vToQm*param0+vToQb)
            noise[0] = param1
            fitENC.append(vToQm*param1*options.ztrim)
            pedestal[0] = param2
            mask[0] = masks[vfat][chan]
            maskReason[0] = maskReasons[vfat][chan]
            chi2[0] = scanFits[3][vfat][chan]
            ndf[0] = int(scanFits[5][vfat][chan])
            holder_curve = vScurves[vfat][chan]
            holder_curve.Copy(scurve_h)
            Nhigh[0] = int(scanFits[4][vfat][chan])
            #Filling the arrays for plotting later
            if options.drawbad:
                if (Chi2 > 1000.0 or Chi2 < 1.0):
                    overlay_fit(vfat, chan)
                    print "Chi2 is, %d"%(Chi2)
                    pass
                pass
            myT.Fill()
            pass
        if not (options.channels or options.PanPin):
            fitSums[vfat] = r.TGraphErrors(len(fitThr),np.array(stripList),np.array(fitThr),np.zeros(len(fitThr)),np.array(fitENC))
            fitSums[vfat].SetTitle("VFAT %i Fit Summary;Strip;Threshold [fC]"%vfat)
            pass
        elif options.channels:
            fitSums[vfat] = r.TGraphErrors(len(fitThr),np.array(chanList),np.array(fitThr),np.zeros(len(fitThr)),np.array(fitENC))
            fitSums[vfat].SetTitle("VFAT %i Fit Summary;Channel;Threshold [fC]"%vfat)
            pass
        elif options.PanPin:
            fitSums[vfat] = r.TGraphErrors(len(fitThr),np.array(panList),np.array(fitThr),np.zeros(len(fitThr)),np.array(fitENC))
            fitSums[vfat].SetTitle("VFAT %i Fit Summary;Panasonic Pin;Threshold [fC]"%vfat)
            pass
        
        fitSums[vfat].SetName("fitSum%i"%vfat)
        fitSums[vfat].SetMarkerStyle(2)
        pass
    pass

def saveSummary(vSummaryPlots, vSummaryPlotsPanPin2, name='Summary'):
    legend = r.TLegend(0.75,0.7,0.88,0.88)
    r.gStyle.SetOptStat(0)
    if not options.PanPin:
        canv = make3x8Canvas('canv', vSummaryPlots, 'colz')
        for vfat in range(0,24):
            canv.cd(vfat+1)
            if options.IsTrimmed:
                legend.Clear()
                legend.AddEntry(line, 'trimVCal is %f'%(trimVcal[vfat]))
                legend.Draw('SAME')
                print trimVcal[vfat]
                lines[vfat].SetLineColor(1)
                lines[vfat].SetLineWidth(3)
                lines[vfat].Draw('SAME')
                pass
            canv.Update()
            pass
        pass
    else:
        canv = r.TCanvas('canv','canv',500*8,500*3)
        canv.Divide(8,6)
        r.gStyle.SetOptStat(0)
        for ieta in range(0,8):
            for iphi in range (0,3):
                r.gStyle.SetOptStat(0)
                canv.cd((ieta+1 + iphi*16)%48 + 16)
                vSummaryPlots[ieta+(8*iphi)].Draw('colz')
                canv.Update()
                canv.cd((ieta+9 + iphi*16)%48 + 16)
                vSummaryPlotsPanPin2[ieta+(8*iphi)].Draw('colz')
                canv.Update()
                pass
            pass
        pass

    canv.SaveAs(filename+'/%s.png' % name)

saveSummary(vSummaryPlots, vSummaryPlotsPanPin2)
if options.SaveFile:
    saveSummary(vSummaryPlotsPruned, vSummaryPlotsPrunedPanPin2, name='PrunedSummary')

if options.SaveFile:
    r.gStyle.SetOptStat(0)
    canv = make3x8Canvas('canv', fitSums, 'ap')
    canv.SaveAs(filename+'/fitSummary.png')
    pass

if options.SaveFile:
    confF = open(filename+'/chConfig.txt','w')
    confF.write('vfatN/I:vfatCH/I:trimDAC/I:mask/I\n')
    for vfat in range (0,24):
        for chan in range (0, 128):
            confF.write('%i\t%i\t%i\t%i\n'%(vfat,chan,trim_list[vfat][chan],masks[vfat][chan]))
            pass
        pass
    confF.close()
    outF.cd()
    for vfat in fitSums.keys():
        fitSums[vfat].Write()
        pass
    myT.Write()
    outF.Close()
    pass
