#! /usr/bin/env python

# Checks that ana_scans.py --anaType=scurve works.

import testutils as tu

tu.testCommand(['ana_scans.py', '--scandate=current', '--anaType=scurve'])
