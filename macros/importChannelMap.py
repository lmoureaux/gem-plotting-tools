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

    Specify the input file. It must be in a specific ``csv`` format; check the
    dedicated section for details.

.. option:: -o,--output <FILE>

    Specify the output file.

Input format
------------

The input file should be in ``csv`` format. It has to be created manually from
the documentation provided by the electronics team, e.g. `this EDMS document
<https://edms.cern.ch/ui/#!master/navigator/document?P:1115513923:100178398:subDocs>`_.
The procedure is as follows:

1. Edit the ``xlsx`` file to contain only the required information:
    1. Unmerge merged cells
    2. Remove all metadata and drawings, except column headers in the row with
       the hybrid positions
    3. Make sure that there's no empty line
    4. Remove the ``IN`` prefix from the "VFAT CHANNEL NUMBERS" column. In
       LibreOffice, the easiest way is as follows:

       * Open the search and replace dialog (``Ctrl+H``)
       * Check the "Regular expressions" box (under "Other options")
       * Enter ``IN([0-9]+)`` in the "Search" box
       * Enter ``$1`` in the "Replace with" box
       * Hit the "Replace all" button.

   Your sheet should now look like this:

    ==================================================  ====================  ======================================================  =========================
    130 Pins PANASONIC CONNECTOR PIN OUTS AXK5SA3277YG  VFAT CHANNEL NUMBERS  Hybrid Positions 2,3,4,5,6,7,8,9,10,11, 12, 13, 14, 15  Hybrid Positions    00,01
    ==================================================  ====================  ======================================================  =========================
    3                                                   0                     0                                                       63
    5                                                   1                     1                                                       62
    7                                                   4                     2                                                       61
    ==================================================  ====================  ======================================================  =========================

2. Export the relevant sheet to ``csv``. In LibreOffice, this is done by using
   the "Save As..." entry of the "File" menu while the sheet is selected, and
   selecting the appropriate format.
3. Check that the ``csv`` file corresponds to the sheet you exported, has the
   required headers and no spurious columns. This can be done from within your
   spreadsheet software.

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
    parser.add_option('-o', '--output', type=str, dest='output',
                      help='Specify the output file', metavar='output')
    (options, args) = parser.parse_args()

    if options.input is None:
        print('Error: The -i option is required')
        import sys
        sys.exit(1)

    if options.output is None:
        print('Error: The -o option is required')
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
