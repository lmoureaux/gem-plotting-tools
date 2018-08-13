#! /usr/bin/env python

r"""
``importChannelMap.py`` --- Imports channel maps for use within the framework
=============================================================================

Synopsis
--------

**importChannelMap.py** :token:`-i` <*INPUT FILE*> :token:`-o` <*OUTPUT FILE*>

Description
-----------

Imports channel maps for use within the framework. The input format is close to
what the electronics team provides, but still requires manual intervention.

The script checks the consistency of the input file and generated mapping. It is
silent if everything is fine.

Mandatory arguments
-------------------

.. program:: importChannelMap.py

.. option:: -i,--input <FILE>

    Specify the input file, in ``xlsx`` format.

.. option:: -s,--sheet <SHEET NAME>

    Specify the name of the sheet to import from the input file.

.. option:: -o,--output <FILE>

    Specify the output file.

Input format
------------

The input file should be in ``xlsx`` format and be organized in the same way as
`this EDMS document
<https://edms.cern.ch/ui/#!master/navigator/document?P:1115513923:100178398:subDocs>`_.
Failure to conform to the format can result in undefined behaviour.

This tool imports one sheet at a time, specified using the :option:`--sheet`
option.

Exit codes
----------

1. Wrong usage
2. A consistency check failed
"""

if __name__ == '__main__':
    # Handle options
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-i', '--input', type=str, dest='input',
                      help='Specify the input file', metavar='input')
    parser.add_option('-s', '--sheet', type=str, dest='sheet',
                      help='Specify the sheet in the input file', metavar='sheet')
    parser.add_option('-o', '--output', type=str, dest='output',
                      help='Specify the output file', metavar='output')
    (options, args) = parser.parse_args()

    if options.input is None:
        print('Error: The -i option is required')
        import sys
        sys.exit(1)

    if options.sheet is None:
        print('Error: The -s option is required')
        import sys
        sys.exit(1)

    if options.output is None:
        print('Error: The -o option is required')
        import sys
        sys.exit(1)

    # Parse input file
    import openpyxl
    xlsxfile = openpyxl.load_workbook(options.input, guess_types = True, data_only = True)
    sheet = xlsxfile[options.sheet]

    headers = [ cell.value for cell in sheet['A4:F4'][0] ]

    data = []
    for row in sheet['A6:F9999']:
        values = [ cell.value for cell in row ]
        if values == [ None ]*len(values) :
            # Skip empty lines
            continue

        # Convert eg 'IN12' to 12
        values[1] = int(values[1][2:])
        data.append(values)

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

    # Write map file
    with open(options.output, 'w') as out:
        out.write('vfat/I:strip/I:channel/I:PanPin/I\n')
        for vfat in range(24):
            for channel in range(128):
                out.write('%d\t%d\t%d\t%d\n' % (
                    vfat,
                    mapping['Strip'][vfat][channel],
                    channel,
                    mapping['PanPin'][vfat][channel]))
