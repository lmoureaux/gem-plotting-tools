from macros.plotoptions import parser

parser.add_option("-o","--overlay", action="store_true", dest="overlay_fit",
                  help="Make overlay of fit result on scurve", metavar="overlay_fit")

(options, args) = parser.parse_args()

filename = options.filename
overlay_fit = options.overlay_fit
channel_yes = options.channels
vfat  = options.vfat
strip = options.strip

def plot_scurve(VFAT, CH, fit_filename, overlay_fit, channel_yes, nInjections=500):
    import ROOT as r
    fitF = r.TFile(fit_filename)
    Scurve = TH1D()
    for event in fitF.scurveFitTree:
        if (event.vfatN == VFAT) and ((event.vfatCH == CH and channel_yes) or (event.vfatstrip == CH and not channel_yes)):
            Scurve = ((fitF.scurveFitTree.scurve_h).Clone())
            if overlay_fit:
                param0 = event.threshold
                param1 = event.noise
                param2 = event.pedestal
                pass
            pass
        pass
    if overlay_fit:
        fitTF1 =  r.TF1('myERF','%i*TMath::Erf((TMath::Max([2],x)-[0])/(TMath::Sqrt(2)*[1]))+%i'%nInjections,1,253)
        fitTF1.SetParameter(0, param0)
        fitTF1.SetParameter(1, param1)
        fitTF1.SetParameter(2, param2)
        pass
    canvas = r.TCanvas('canvas', 'canvas', 500, 500)
    r.gStyle.SetOptStat(0)
    Scurve.Draw()
    if overlay_fit:
        fitTF1.Draw('SAME')
        pass
    canvas.Update()
    if overlay_fit:
        r.gStyle.SetOptStat(111)
        print param0, param1, param2
        if channel_yes:
            canvas.SaveAs('Fit_Overlay_VFAT%i_Channel%i.png'%(VFAT, CH))
            pass
        else:
            canvas.SaveAs('Fit_Overlay_VFAT%i_Strip%i.png'%(VFAT, CH))
            pass
    else:
        if channel_yes:
            canvas.SaveAs('Scurve_VFAT%i_Channel%i.png'%(VFAT, CH))
            pass
        else:
            canvas.SaveAs('Scurve_VFAT%i_Strip%i.png'%(VFAT, CH))
            pass
        pass
    return

plot_scurve(vfat, strip, filename, overlay_fit, channel_yes)
