from macros.plotoptions import parser

(options, args) = parser.parse_args()

def plot_vfat_summary(VFAT, STRIP, fit_filename):
    import ROOT as r

    fitF = r.TFile(fit_filename)
    if options.channels:
        vNoise = r.TH2D('vNoise', 'Noise vs trim for VFAT %i Channel %i; trimDAC [DAC units]; Noise [DAC units]'%(VFAT, STRIP), 32, -0.5, 31.5, 60, -0.5, 59.5)
        pass
    else:
        vNoise = r.TH2D('vNoise', 'Noise vs trim for VFAT %i Strip %i; trimDAC [DAC units]; Noise [DAC units]'%(VFAT, STRIP), 32, -0.5, 31.5, 60, -0.5, 59.5)
        pass
    vNoise.GetYaxis().SetTitleOffset(1.5)
    for event in fitF.scurveFitTree:
        if (event.vfatN == VFAT) and ((event.vfatstrip == STRIP and not options.channels) or (event.vfatCH == STRIP and options.channels)):
            vNoise.Fill(event.trimDAC, event.noise)
            pass
        pass
    canvas = r.TCanvas('canvas', 'canvas', 500, 500)
    r.gStyle.SetOptStat(0)
    vNoise.Draw('colz')
    canvas.Update()
    if options.channels:
        canvas.SaveAs('Noise_Trim_VFAT_%i_Channel_%i.png'%(VFAT, STRIP))
        pass
    else:
        canvas.SaveAs('Noise_Trim_VFAT_%i_Strip_%i.png'%(VFAT, STRIP))
        pass
    return

plot_vfat_summary(options.vfat, options.strip, options.filename)
