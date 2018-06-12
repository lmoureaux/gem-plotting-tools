#! /usr/bin/env python

import numpy as np

class MaskedRange(object):
    """Represents a range of scans in TimeSeriesData, for a given VFAT and
    channel

    Attributes:
        begin: Index of the first scan in the range
        end: Index of the first scan not in the range
        vfat: VFAT number
        channel: Channel number
    """

    def __init__(self, data, vfat, channel, start, end):
        """Constructor

        Args:
            data: A TimeSeriesData object to load scan results from
            vfat: The VFAT number
            channel: The channel number in the VFAT
            start: The index of the first scan in the range
            end: The index of the first scan not in the range
        """
        self._dates = data.dates
        self._mask = data.mask[vfat,channel]
        self._maskReason = data.maskReason[vfat,channel]

        self.vfat = vfat
        self.channel = channel
        self.start = start
        self.end = end

    def beforeStartString(self):
        """Returns the date of the last scan before the range

        Returns:
            If the range includes the first available scan, returns 'never'.
            Else returns a string containing the date of the scan, formatted as
            %Y.%m.%d.%H.%M.
        """
        if self.start == 0:
            return 'never'
        else:
            return self._dates[self.start - 1]

    def startString(self):
        """Returns the date of the first scan in the range

        Returns:
            If the range includes the first available scan, returns 'first'.
            Else returns a string containing the date of the scan, formatted as
            %Y.%m.%d.%H.%M.
        """
        if self.start == 0:
            return 'first'
        else:
            return self._dates[self.start]

    def endString(self):
        """Returns the date of the last scan in the range

        Returns:
            If the range includes the last available scan, returns 'never'. Else
            returns a string containing the date of the scan, formatted as
            %Y.%m.%d.%H.%M.
        """
        if self.end == len(self._dates):
            return 'never'
        else:
            return self._dates[self.end - 1]

    def afterEndString(self):
        """Returns the date of the first scan after the range

        Returns:
            If the range includes the last available scan, returns 'none'. Else
            returns a string containing the date of the scan, formatted as
            %Y.%m.%d.%H.%M.
        """
        if self.end >= len(self._dates) - 1:
            return 'none'
        else:
            return self._dates[self.end]

    def scanCount(self):
        """Returns the number of scans in the range"""
        return self.end - self.start

    def badMaskReasonScanCount(self):
        """Returns the number of scans with non-zero maskReason in the range"""
        return np.count_nonzero(self._maskReason[self.start:self.end])

    def maskedScanCount(self):
        """Returns the number of scans with mask set in the range"""
        return np.count_nonzero(self._mask[self.start:self.end])

    def maskedScanRatio(self):
        """Returns the fraction of scans with mask set in the range"""
        return float(self.maskedScanCount()) / self.scanCount()

    def initialMaskReason(self):
        """Returns the maskReason for the first scan in the range"""
        return int(self._maskReason[self.start])

    def allMaskReasons(self):
        """Returns a maskReason bitmask that contains all the maskReasons in the
        range"""
        res = 0
        for time in range(self.start, self.end):
            res |= int(self._maskReason[time])
        return res

    def additionnalMaskReasons(self):
        """Returns a maskReason bitmask that contains all the maskReaons in the
        range but not in the first scan"""
        return self.allMaskReasons() ^ self.initialMaskReason()

def _findRangesMeta(data, vfat, channel, channelData, maxSkip):
    """Finds ranges of scans based on the contents of channelData.

    Searches the data for ranges of scans with channelData == true. During the
    search, at most maxSkip scans with no maskReason set can be skipped. Only
    ranges with more than minBadScans are kept.

    Args:
        data: The TimeSeriesData object to pull data from
        vfat: The VFAT to return ranges for
        channel: The channel to return ranges for
        channelData: A list of booleans, with each entry representing one scan
        maxSkip: The maximum number of "good" scans between two "bad" scans

    Returns:
        A list of MaskedRange objects
    """
    ranges = []

    start = 0
    while start < len(channelData) - 1:
        if channelData[start]:
            end = start
            skipped = 0
            for time in range(start, len(channelData)):
                if channelData[time]:
                    end = time + 1
                    skipped = 0
                else:
                    skipped += 1
                if skipped > maxSkip:
                    break

            if end > start:
                ranges.append(MaskedRange(data, vfat, channel, start, end))

            start = end + 1
        else:
            start += 1

    return ranges


def findRangesMaskReason(data, vfat, channel, maxSkip = 5, minBadScans = 4):
    """Finds ranges of scans based on the maskReason attribute.

    Searches the data for the given vfat and channel for ranges of scans with
    non-zero maskReason. During the search, at most maxSkip scans with no
    maskReason set can be skipped. Only ranges with more than minBadScans are
    kept.

    Args:
        data: The TimeSeriesData object to pull data from
        vfat: The VFAT to return ranges for
        channel: The channel to return ranges for
        maxSkip: The maximum number of "good" scans between two "bad" scans
        minBadScans: The minimum number of bad scans

    Returns:
        A list of MaskedRange objects
    """
    ranges = _findRangesMeta(data,
                             vfat,
                             channel,
                             data.maskReason[vfat,channel] != 0,
                             maxSkip)

    return list(filter(lambda r: r.badMaskReasonScanCount() >= minBadScans,
                       ranges))

def findRangesMask(data, vfat, channel, maxSkip = 5, minBadScans = 4):
    """Finds ranges of scans based on the mask attribute.

    Searches the data for the given vfat and channel for ranges of scans with
    non-zero maskReason. During the search, at most maxSkip scans with mask not
    set can be skipped. Only ranges with more than minBadScans are kept.

    Args:
        data: The TimeSeriesData object to pull data from
        vfat: The VFAT to return ranges for
        channel: The channel to return ranges for
        maxSkip: The maximum number of "good" scans between two "bad" scans
        minBadScans: The minimum number of bad scans

    Returns:
        A list of MaskedRange objects
    """
    ranges = _findRangesMeta(data,
                             vfat,
                             channel,
                             data.mask[vfat,channel] != 0,
                             maxSkip)

    return list(filter(lambda r: r.maskedScanCount() >= minBadScans,
                       ranges))

class TimeSeriesData(object):
    """Holds information about time variation of scan results.

    Each property is stored as a 3D Numpy array with indexes
    [vfat][strip][time]. The time index -> scan date mapping is exposed in the
    date attribute.

    Attributes:
        dates: Array of strings containing the scan dates.
        mask: Data for the "mask" property,
        maskReason: Data for the "maskReason" property,
    """

    def __init__(self, inputDir):
        """Creates a TimeSeriesData object by reading the files located in the
        inputDir directory.

        The input directory must contain the following files:

        * gemPlotterOutput_mask_vs_scandate.root
        * gemPlotterOutput_maskReason_vs_scandate.root

        They are created by plotTimeSeries.py.

        Args:
            inputDir: The path to the input directory
        """
        import ROOT as r
        from root_numpy import hist2array

        file_mask = r.TFile('%s/gemPlotterOutput_mask_vs_scandate.root' % inputDir, 'READ')
        file_maskReason = r.TFile('%s/gemPlotterOutput_maskReason_vs_scandate.root' % inputDir, 'READ')

        self.mask = [] # [vfat][time][strip]; warning: reordered after loading
        self.maskReason = [] # [vfat][time][strip]; warning: reordered after loading

        for vfat in range(0,24):
            dirname = 'VFAT%d' % vfat
            dir_mask = file_mask.Get(dirname)
            dir_maskReason = file_maskReason.Get(dirname)

            hist_mask = dir_mask.Get("h_ROBstr_vs_scandate_Obsmask_VFAT%d" % vfat)
            hist_maskReason = dir_maskReason.Get("h_ROBstr_vs_scandate_ObsmaskReason_VFAT%d" % vfat)

            self.mask.append(hist2array(hist_mask))
            self.maskReason.append(hist2array(hist_maskReason))

            self.dates = [] # [time]
            for bin in range(hist_mask.GetNbinsX()):
                self.dates.append(hist_mask.GetXaxis().GetBinLabel(bin + 1))

        self.dates = np.array(self.dates)
        self.mask = np.array(self.mask)
        self.maskReason = np.array(self.maskReason)

        self.mask = np.swapaxes(self.mask, 1, 2) # Reorder to [vfat][strip][time]
        self.maskReason = np.swapaxes(self.maskReason, 1, 2) # Reorder to [vfat][strip][time]

    def removeBadScans(self, maxMaskedChannelFraction = 0.07):
        """Finds bad scans and removes them from the data.

        Any scan matching one of the following criteria is considered bad:

        * No channel was masked
        * The fraction of masked channels is higher than maxMaskedChannelFraction

        Args:
            maxMaskedChannelFraction: The maximum fraction of masked channels
                for a scan to be kept.
        """
        numMaskedChannels = np.count_nonzero(self.mask, (0, 1))
        badScans = np.logical_or(numMaskedChannels == 0,
                                 numMaskedChannels / 24. / 128 > maxMaskedChannelFraction)
        self.dates = self.dates[np.logical_not(badScans)]
        self.mask = self.mask[:,:,np.logical_not(badScans)]
        self.maskReason = self.maskReason[:,:,np.logical_not(badScans)]

if __name__ == '__main__':
    import os
    import os.path
    import sys

    from optparse import OptionParser, OptionGroup
    parser = OptionParser()
    parser.add_option("-i", "--inputDir", type=str, dest="inputDir",
                      help="Input directory (=output directory of plotTimeSeries.py)")
    (options, args) = parser.parse_args()

    if options.inputDir is None:
        print("Error: The -i argument is required")
        sys.exit(os.EX_USAGE)

    if not os.path.isdir(options.inputDir):
        print("Error: Not a directory: %s" % options.inputDir)
        sys.exit(os.EX_USAGE)

    data = TimeSeriesData(options.inputDir)
    data.removeBadScans()

    from gempython.gemplotting.utils.anaInfo import MaskReason

    for vfat in range(24):
        timePoints = data.mask.shape[2]
        print '''
## VFAT %d

first scan is %s
latest scan is %s

| Channel | Known good       | Range begins     | Range ends       | #scans | Masked%% | Initial `maskReason`                | Other subsequent `maskReason`s |
| ------: | :--------------- | :--------------- | :--------------- | -----: | ------: | :---------------------------------- | :----------------------------- |''' % (
            vfat,
            data.dates[0],
            data.dates[timePoints - 1])
        for chan in range(128):
            for r in findRangesMaskReason(data, vfat, chan):
                additionnalReasons = r.additionnalMaskReasons()
                print '| {:>7} | {:<16} | {:<16} | {:<16} | {:>6} | {:>7.0f} | {:<35} | {:<30} |'.format(
                    chan,
                    r.beforeStartString(),
                    r.startString(),
                    r.endString(),
                    r.scanCount(),
                    100 * r.maskedScanRatio(),
                    MaskReason.humanReadable(r.initialMaskReason()),
                    MaskReason.humanReadable(additionnalReasons) if additionnalReasons != 0 else '')
