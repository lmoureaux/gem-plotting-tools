#! /usr/bin/env python

# Author: Louis Moureaux (lmoureau@ulb.ac.be)

import ROOT as r
import os.path
from argparse import ArgumentParser

# Define and parse options
parser = ArgumentParser()
parser.add_argument(dest='inputs', nargs='+',
                    help='Files to compare', metavar='in.root')
parser.add_argument('-o', '--output', dest='output',
                    default='LatencyCompared',
                    help='Output file name without extension', metavar='out')
parser.add_argument('-g', '--png', dest='png', action='store_true',
                    help='Write the plots to png files')

options = parser.parse_args()

r.gROOT.SetBatch()

inputs = [ r.TFile(filename) for filename in options.inputs ]
output = r.TFile(options.output + '.root', 'RECREATE')

numInputs = len(inputs)
for vfat in range(24):
  # Create the comparison
  canvas = r.TCanvas('lat-vfat%d' % vfat, 'canv', numInputs * 1000, 1000)
  canvas.Divide(numInputs)
  for i in range(numInputs):
    canvas.cd(i + 1)
    plot = inputs[i].Get('lat%d_ga' % vfat)
    plot.SetTitle(options.inputs[i])
    plot.Draw()
  # Write to ROOT file
  output.cd()
  canvas.Write()
  # Write png file if needed
  if options.png:
    canvas.SaveAs(options.output + '%d.png' % vfat)
