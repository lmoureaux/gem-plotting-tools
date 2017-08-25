#! /usr/bin/env python

# Checks that ana_scans.py --anaType=scurve works.

import testutils as tu

tu.testCommand(['ana_scans.py', '--scandate=current', '--anaType=scurve'])

outputDir = 'travis/scurve/current/SCurveData/'
tu.testFile(outputDir + 'Summary.png')
tu.testFile(outputDir + 'PrunedSummary.png')
tu.testFile(outputDir + 'fitSummary.png')
tu.testFile(outputDir + 'SCurveFitData.root')
tu.testFile(outputDir + 'chConfig.txt')
