import ROOT as r
from wsuPyROOTUtils import *
from gempython.utils.nesteddict import nesteddict as ndict

r.gROOT.SetBatch(True)
files = [
    "DACData_VFAT0_eta0",
    "DACData_VFAT0_p7_ca0",
    ]
path = "/home/mdalchen/work/dac_scans/904"
for fi in files:
    infile  = r.TFile("%s/%s.root"%(path,fi),"read")
    outfile = r.TFile("%s_output.root"%(fi),"recreate")
    tree    = infile.Get("dacTree")

    dacmode = {
        # "0IPREAMPIN"   : "I_{preamp,input}"  ,
        # "1IPREAMPFEED" : "I_{preamp,feedback}",
        # "2IPREAMPOUT"  : "I_{preamp,output}" ,
        # "4ISHAPER"     : "I_{shaper}"    ,
        # "5ISHAPERFEED" : "I_{shaper,feedback}",
        # "3ICOMP"       : "I_{comparator}"      ,
        "6VTHRESHOLD1" : "V_{threshold,1}",
        # "7VTHRESHOLD2" : "V_{threshold,2}",
        "8VCAL"        : "V_{cal}"       ,
        "9CALOUTVLOW"  : "V_{cal out, LOW}" ,
        "9CALOUTVHI"   : "V_{cal out, HI}"  ,
        }
    
    rawhist  = ndict()
    convhist = ndict()
    
    # for vfat in range(24):
    vfat = 0
    for dac in sorted(dacmode.keys()):
        # print "making %s histogram"%(dac[1:])
        outfile.cd()
        rawhist[vfat][ "raw%s"%(dac[1:])]  = r.TH2D("VFAT%d_raw%s"%( vfat,dac[1:]),"%s"%(dacmode[dac]),256,-0.5,255.5,1024,-0.5,1023.5)
        convhist[vfat]["conv%s"%(dac[1:])] = r.TH2D("VFAT%d_conv%s"%(vfat,dac[1:]),"%s"%(dacmode[dac]),256,-0.5,255.5,1500,0,1.5)
        rawhist[vfat][ "raw%s"%(dac[1:])].Sumw2()
        convhist[vfat]["conv%s"%(dac[1:])].Sumw2()
        # tree.Draw("dacoutval:dacinval>>%s"%(dac),"dacname==\"%s\"&&vfatN==%d"%(dac[1:],vfat),"colzs")
    for ev in tree:
        # print "filling histograms for vfatN==%d,dacname==%s"%(ev.vfatN,ev.dacname[0])
        # print rawhist[ev.vfatN]
        #rawVal  = ((ev.dacoutval)>>6)
        rawVal  = ev.dacoutval
        I_CONV_FACT = (0.977/1000.)/(2*1000)
        V_CONV_FACT = 2*(0.977/1000.)
        convVal = rawVal*2*(0.977/1000.)
        # print rawhist[ev.vfatN][ "raw%s"%(ev.dacname[0])]
        # print convhist[ev.vfatN]["conv%s"%(ev.dacname[0])]
        rawhist[vfat][ "raw%s"%(ev.dacname[0])].Fill( ev.dacinval,rawVal)
        convhist[vfat]["conv%s"%(ev.dacname[0])].Fill(ev.dacinval,convVal)
        pass
    vfat = 0
    # for vfat in range(24):
    canvs    = ndict()
    for con in ["raw","conv"]:
        canvs[con] = r.TCanvas("%sVFAT%d"%(con,vfat),"",1600,900)
        canvs[con].Divide(2,2)
        can = 0
    for dac in sorted(dacmode.keys()):
        print "making %s histogram"%(dac)
        can+=1
        canvs["raw"].cd(can)
        rawfit  = r.TF1("rawfunkyVFAT%d_%s"%(vfat,dac[1:]),"pol1",0,256)
        rawhist[vfat]["raw%s"%(dac[1:])].Fit("rawfunkyVFAT%d_%s"%(vfat,dac[1:]),"EMFN")
        rawhist[vfat]["raw%s"%(dac[1:])].SetXTitle("VFAT DAC Units")
        rawhist[vfat]["raw%s"%(dac[1:])].SetYTitle("OptoHybrid xADC Units")
        rawhist[vfat]["raw%s"%(dac[1:])].Draw("colz")

        canvs["conv"].cd(can)
        convfit  = r.TF1("convfunkyVFAT%d_%s"%(vfat,dac[1:]),"pol1",0,256)
        convhist[vfat]["conv%s"%(dac[1:])].Fit("convfunkyVFAT%d_%s"%(vfat,dac[1:]),"EMFN")
        convhist[vfat]["conv%s"%(dac[1:])].SetXTitle("VFAT DAC Units")
        convhist[vfat]["conv%s"%(dac[1:])].SetYTitle("V")
        convhist[vfat]["conv%s"%(dac[1:])].Draw("colz")

        outfile.cd()
        rawfit.Write()
        convfit.Write()
        convhist[vfat]["conv%s"%(dac[1:])].Write()
        rawhist[vfat]["raw%s"%(dac[1:])].Write()
        pass
    for con in ["raw","conv"]:
        canvs[con].SaveAs("%s_DACs_%s.png"%(fi,con))
        canvs[con].SaveAs("%s_DACs_%s.pdf"%(fi,con))
        canvs[con].SaveAs("%s_DACs_%s.C"%(  fi,con))
        pass
    # pass
    outfile.Write()
    outfile.Close()
pass
