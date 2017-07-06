#! /usr/bin/env python

# Author: Louis Moureaux (lmoureau@ulb.ac.be)

import ROOT as r
import os.path
from argparse import ArgumentParser

# Define and parse options
parser = ArgumentParser()
parser.add_argument(dest='inputs', nargs='+',
                    help='Files to compare', metavar='in.root')
parser.add_argument('-l', '--legend', dest='legend',
                    default=None, nargs='+',
                    help='Legend entries', metavar='legend')
parser.add_argument('-o', '--output', dest='output',
                    default='LatencyCompared',
                    help='Output file name without extension', metavar='out')
parser.add_argument('-g', '--png', dest='png', action='store_true',
                    help='Write the plots to png files')

options = parser.parse_args()

r.gROOT.SetBatch()

swatch = [ r.kBlue, r.kGreen, r.kMagenta, r.kCyan, r.kOrange,
           r.kSpring, r.kTeal, r.kAzure, r.kViolet, r.kPink ]

inputs = [ r.TFile(filename) for filename in options.inputs ]
output = r.TFile(options.output + '.root', 'RECREATE')

# Setup legend entries
legendEntries = []
if options.legend != None:
  legendEntries = options.legend
# Add defaults for missing entries
for i in range(len(legendEntries), len(inputs)):
  legendEntries.append(options.inputs[i])

numInputs = len(inputs)
for vfat in range(24):
  # Create the comparison
  canvas = r.TCanvas('canvas-lat-vfat%d' % vfat, '', 1000, 1000)
  canvas.cd()
  legend = r.TLegend(0.7, 0.8, 0.9, 0.9)
  for i in range(numInputs):
    plot = inputs[i].Get('lat%d_ga' % vfat)
    plot.SetTitle('NHits(latency) for vfat %d' % vfat)
    plot.SetLineColor(swatch[i % len(swatch)])
    plot.GetYaxis().SetRangeUser(-0.05, 0.5)
    plot.Draw('' if i == 0 else 'same')
    legend.AddEntry(plot, legendEntries[i])
  legend.Draw()
  # Write to ROOT file
  output.cd()
  canvas.Write()
  # Write png file if needed
  if options.png:
    canvas.SaveAs(options.output + '%d.png' % vfat)
