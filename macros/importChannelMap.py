#! /usr/bin/env python

r"""
``importChannelMap.py`` --- Imports channel maps for use within the framework
=============================================================================

Synopsis
--------

**importChannelMap.py** :token:`-i` <*INPUT FILE*>

Description
-----------

TODO

Mandatory arguments
-------------------

.. program:: importChannelMap.py

.. option:: -i,--input <FILE>

    Specify the input file. It must be in a specific ``csv`` format; check the
    dedicated section for details.
"""

if __name__ == '__main__':
    # Handle options
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-i', '--input', type=str, dest='input',
                      help='Specify the input file', metavar='input')
    (options, args) = parser.parse_args()

    if options.input is None:
        print('Error: The -i option is required')
        import sys
        sys.exit(1)

    # Parse input file
    headers = None
    data = []
    with open(options.input) as csvfile:
        import csv
        reader = csv.reader(csvfile)
        firstRow = True
        for row in reader:
            if firstRow:
                headers = row
                firstRow = False
            else:
                for i in range(len(row)):
                    row[i] = int(row[i])
                data.append(row)
            pass
        pass

    # Sanity checks: column headers
    import re
    import sys
    if not re.search('pin', headers[0], re.IGNORECASE):
        print('Error: The first column should contain Panasonic pin numbers')
        sys.exit(2)
    if not re.search('chan', headers[1], re.IGNORECASE):
        print('Error: The second column should contain channel numbers')
        sys.exit(2)
    for column in range(2, len(headers)):
        if not re.search('\d+', headers[column]):
            print('Error: The header of column %d should contain information about vfat position')
            sys.exit(2)
        pass

    # Find which vfats are included in every column
    import numpy as np
    vfat_found = np.zeros(24, dtype=bool)
    vfat_column = np.zeros(24, dtype=int)
    for column in range(2, len(headers)):
        for result in re.findall('\d+', headers[column]):
            vfat = int(result)
            if vfat_found[vfat]:
                print('Error: VFAT %d included twice' % vfat)
                sys.exit(2)
            else:
                vfat_found[vfat] = True
                vfat_column[vfat] = column
            pass
        pass

    # Sanity check: missing VFATs
    if not np.all(vfat_found):
        missing = np.where(np.logical_not(vfat_found))[0]
        missing = missing.astype(str)
        missing = ', '.join(missing)
        print('Error: Missing VFATs: %s' % missing)
        sys.exit(2)

    # Build the mapping container
    import gempython.gemplotting.utils.anaInfo as anaInfo
    mapping = {}
    for name in anaInfo.mappingNames:
        mapping[name] = np.full((24, 128), -1)
        pass

    # Fill mapping
    for vfat in range(24):
        column = vfat_column[vfat]
        for row in data:
            # row[0] = PanPin
            # row[1] = vfatCH
            # row[column] = Strip
            # This is checked at load time
            mapping['PanPin'][vfat][row[1]] = row[0]
            mapping['Strip' ][vfat][row[1]] = row[column]
            mapping['vfatCH'][vfat][row[1]] = row[1]
            pass
        pass

    # Sanity check: missing entries
    for name in anaInfo.mappingNames:
        missing = (mapping[name] == -1)
        if np.any(missing):
            print('Error: Missing entries for %s:' % name)
            missing = np.where(missing)
            for i in range(len(missing[0])):
                print('VFAT %d channel %d' % (missing[0][i], missing[1][i]))
                pass
            sys.exit(2)
            pass
        pass

    # Sanity check: entries out of bounds
    for name in anaInfo.mappingNames:
        outOfBounds = (mapping[name] < 0)
        if name != 'PanPin':
            outOfBounds = np.logical_or(outOfBounds, mapping[name] >= 128)
        if np.any(outOfBounds):
            print('Error: Missing entries for %s:' % name)
            outOfBounds = np.where(outOfBounds)
            for i in range(len(outOfBounds[0])):
                print('VFAT %d channel %d: %d' % (
                    outOfBounds[0][i],
                    outOfBounds[1][i],
                    mapping[name][outOfBounds[0][i]][outOfBounds[1][i]]))
                pass
            sys.exit(2)
            pass
        pass

    # Sanity check: reverse
    # Try to find every channel and strip in data for every VFAT
    for name in anaInfo.mappingNames:
        if name != 'PanPin':
            # PanPin isn't a bijection
            for vfat in range(24):
                for stripOrChan in range(128):
                    if not stripOrChan in mapping['Strip'][vfat]:
                        print('Error: %s %d is not present for VFAT %d' % (
                            name,
                            stripOrChan,
                            vfat))
                        pass
                    pass
                pass
            pass
        pass