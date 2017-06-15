#!/usr/bin/env python

def extractResults(infname,link=99,chip=99):
    import ROOT as r
    # from array import array
    from gempython.utils.nesteddict import nesteddict as ndict
    import sys,os
    from chamberInfo import chamber_config

    print("PYTHONPATH %s"%(os.getenv('PYTHONPATH')))
    print("GEMPYTHONPATH %s"%(os.getenv('GEMPYTHONPATH')))

    r.gROOT.SetBatch(True)
    r.gStyle.SetOptStat(0)
    r.gErrorIgnoreLevel = r.kError
    basedir = None

    try:
        basedir = "/gemdata/%s/dacscan/current"%(chamber_config[link])
    except KeyError as e:
        print("Unable to find %d in chamber list: %s"%(link,str(e)))
        exit(0)
    infile  = r.TFile("%s/DACScanData.root"%(basedir), "read")
    if not infile:
        print("Unable to find input file: %s/DACScanData.root"%(basedir,infname))
        exit(1)
    elif not infile.IsOpen():
        print("Unable to open input file: %s/DACScanData.root"%(basedir,infname))
        exit(1)
    elif infile.IsZombie():
        print("Zombie input file: %s/DACScanData.root"%(basedir,infname))
        exit(1)

    if not os.path.isdir("/tmp/%s"%(os.getenv("USER"))):
        os.mkdir("/tmp/%s"%(os.getenv("USER")))
        pass
    outfile = r.TFile("/tmp/%s/%s_DACScanData_%s_output.root"%(os.getenv("USER"),chamber_config[link],infname), "recreate")
    tree    = infile.Get("dacTree")

    dacmode = {
        "IPREAMPIN"   : "I_{preamp,input}"  ,
        "IPREAMPFEED" : "I_{preamp,feedback}",
        "IPREAMPOUT"  : "I_{preamp,output}" ,
        "ISHAPER"     : "I_{shaper}"    ,
        "ISHAPERFEED" : "I_{shaper,feedback}",
        "ICOMP"       : "I_{comparator}"      ,
        "VTHRESHOLD1" : "V_{threshold,1}",
        "VTHRESHOLD2" : "V_{threshold,2}",
        "VCAL"        : "V_{cal}"       ,
        "CALOUTVLOW"  : "V_{cal out, LOW}" ,
        "CALOUTVHI"   : "V_{cal out, HI}"  ,
    }

    # outtree = r.TTree("dacScanAnalyzed","Analyzed and fitted DAC scan data")

    # dacname = vector('string')()
    # dacname.push_back("N/A")
    # outtree.Branch( 'dacname', dacname )

    # dacinval = array( 'i', [ 0 ] )
    # outtree.Branch( 'dacinval', dacinval, 'dacinval/I' )

    # dacrawval = array( 'i', [ 0 ] )
    # outtree.Branch( 'dacrawval', dacrawval, 'dacrawval/I' )

    # dacconvval = array( 'i', [ 0 ] )
    # outtree.Branch( 'dacconvval', dacconvval, 'dacconvval/I' )

    # vfatN = array( 'i', [ 0 ] )
    # outtree.Branch( 'vfatN', vfatN, 'vfatN/I' )

    # chipID = vector('string')()
    # chipID.push_back("N/A")
    # outtree.Branch( 'chipID', chipID )

    # link = array( 'i', [ 0 ] )
    # outtree.Branch( 'link', link, 'link/I' )

    rawhist  = ndict()
    convhist = ndict()
    rawfit   = ndict()
    convfit  = ndict()

    r.TH1.SetDefaultSumw2()

    # # Define three histograms for fit:
    # param0hist   = ndict()
    # param1hist   = ndict()
    # param0v1hist = ndict()

    # for dac in sorted(dacmode.keys()):
    #     if dac.find("VLOW") > 0:
    #         param0hist[dac]   = r.TH1F("param0hist%s"%(dac),  "",50,0.5,1.0)
    #         param1hist[dac]   = r.TH1F("param1hist%s"%(dac),  "",50,1000.*-0.00075,1000.*-0.00025)
    #         param0v1hist[dac] = r.TH2F("param0v1hist%s"%(dac),"",50,0.5,1.0, 50,1000.*-0.00075,1000.*-0.00025)
    #         pass
    #     elif dac.find("VHI") > 0:
    #         param0hist[dac]   = r.TH1F("param0hist%s"%(dac),  "",50,0.5,1.0)
    #         param1hist[dac]   = r.TH1F("param1hist%s"%(dac),  "",50,1000.*-0.0001,1000.*0.0001)
    #         param0v1hist[dac] = r.TH2F("param0v1hist%s"%(dac),"",50,0.5,1.0, 50,1000.*-0.0001,1000.*0.0001)
    #         pass
    #     elif dac.find("VCAL") > 0:
    #         param0hist[dac]   = r.TH1F("param0hist%s"%(dac),  "",50,0.25,0.75)
    #         param1hist[dac]   = r.TH1F("param1hist%s"%(dac),  "",50,1000.*-0.00035,1000.*-0.0002)
    #         param0v1hist[dac] = r.TH2F("param0v1hist%s"%(dac),"",50,0.25,0.75, 50,1000.*0.00025,1000.*0.00075)
    #         pass
    #     else:
    #         param0hist[dac]   = r.TH1F("param0hist%s"%(dac),  "",50,0.25,0.75)
    #         param1hist[dac]   = r.TH1F("param1hist%s"%(dac),  "",50,1000.*-0.00035,1000.*-0.0002)
    #         param0v1hist[dac] = r.TH2F("param0v1hist%s"%(dac),"",50,0.25,0.75, 50,1000.*0.00025,1000.*0.00075)
    #         pass
    #     param0hist[dac].GetYaxis().SetTitle("")
    #     param0hist[dac].GetXaxis().SetTitle("V^{Out}_{CAL} Offset [V]")
    #     param1hist[dac].GetYaxis().SetTitle("")
    #     param1hist[dac].GetXaxis().SetTitle("V^{Out}_{CAL}/V^{DAC}_{CAL} [mV]")
    #     param0v1hist[dac].GetXaxis().SetTitle("V^{Out}_{CAL} Offset [V]")
    #     param0v1hist[dac].GetYaxis().SetTitle("V^{Out}_{CAL}/V^{DAC}_{CAL} [mV]")
    #     pass
    print("I will work!")

    for vfat in range(24):
        for dac in sorted(dacmode.keys()):
            outfile.cd()
            rawhist[vfat][ "raw%s"%(dac)]  = r.TH2I("%s_VFAT%d_raw%s"%( chamber_config[link],vfat,dac),"%s"%(dacmode[dac]),
                                                    256,-0.5,255.5,1024,-0.5,1023.5)
            if (dacmode[dac][0] == "I"):
                convhist[vfat]["conv%s"%(dac)] = r.TH2F("%s_VFAT%d_conv%s"%(chamber_config[link],vfat,dac),"%s"%(dacmode[dac]),
                                                        256,-0.5,255.5,1024,0,0.0005)
            else:
                convhist[vfat]["conv%s"%(dac)] = r.TH2F("%s_VFAT%d_conv%s"%(chamber_config[link],vfat,dac),"%s"%(dacmode[dac]),
                                                        256,-0.5,255.5,1024,0,1.25)
                pass
            rawhist[vfat][ "raw%s"%(dac)].Sumw2()
            convhist[vfat]["conv%s"%(dac)].Sumw2()
            pass
        pass

    print "looping tree, filling histograms"
    for ev in tree:
        rawVal  = (ev.dacoutval)
        # 0.977uV per ADC
        convVal = rawVal*(0.977/1000.)*2 # value in V, passes through a divider
        if (dacmode[ev.dacname[0]][0] == "I"):
            convVal = rawVal*(0.977/1000.)/2000. # value in A, using the 2kOhm resistor
            pass
        # print("%s %s %d %2.6f"%(ev.dacname[0],dacmode[ev.dacname[0]][0],rawVal,convVal))
        rawhist[ev.vfatN]["raw%s"%( ev.dacname[0])].Fill(ev.dacinval,rawVal)
        convhist[ev.vfatN]["conv%s"%(ev.dacname[0])].Fill(ev.dacinval,convVal)
            # pass
        pass

    print "fitting histograms"
    outdata = file("outdata_%s.txt"%(infname),"w")

    import CMS_lumi as cmslumi
    import tdrstyle as tdr
    tdr.setTDRStyle()

    for vfat in range(24):
        canvs    = ndict()
        for con in ["raw","conv"]:
            canvs[con] = r.TCanvas("%sVFAT%d"%(con,vfat),"",1600,900)
            canvs[con].Divide(4,3)
            can = 0
            pass
        for dac in sorted(dacmode.keys()):
            print "fitting %s histogram"%(dac)
            can+=1
            fitMin = 0
            fitMax = 256
            rawfit[vfat][ "raw%s"%( dac)] = r.TF1("rawfunky%s_VFAT%d_%s"%( chamber_config[link],vfat,dac),"pol1",0,256)
            convfit[vfat]["conv%s"%(dac)] = r.TF1("convfunky%s_VFAT%d_%s"%(chamber_config[link],vfat,dac),"pol1",0,256)

            fitting = True
            while (fitting):
                rawResult = rawhist[vfat]["raw%s"%(dac)].Fit("rawfunky%s_VFAT%d_%s"%(chamber_config[link],vfat,dac),"EMFNRS","",
                                                             fitMin,fitMax)
                convResult = convhist[vfat]["conv%s"%(dac)].Fit("convfunky%s_VFAT%d_%s"%(chamber_config[link],vfat,dac),"EMFNRS","",
                                                                fitMin,fitMax)
                rawFitChi2  = rawfit[vfat][ "raw%s"%( dac)].GetChisquare()
                rawFitNDF   = rawfit[vfat][ "raw%s"%( dac)].GetNDF()
                convFitChi2 = convfit[vfat]["conv%s"%(dac)].GetChisquare()
                convFitNDF  = convfit[vfat]["conv%s"%(dac)].GetNDF()
                print("VFAT%d %s %2.4g/%2.4g  %2.4g/%2.4g"%(vfat,dac,rawFitChi2,rawFitNDF,convFitChi2,convFitNDF))
                rawResult.Print("V")
                convResult.Print("V")

                rawfit[vfat][ "raw%s"%( dac)].SetParameters(0.0,0.0,0.0)
                convfit[vfat]["conv%s"%(dac)].SetParameters(0.0,0.0,0.0)

                fitMin = 25
                fitMax = 200
                rawResult = rawhist[vfat]["raw%s"%(dac)].Fit("rawfunky%s_VFAT%d_%s"%(chamber_config[link],vfat,dac),"EMFNRS","",
                                                             fitMin,fitMax)
                convResult = convhist[vfat]["conv%s"%(dac)].Fit("convfunky%s_VFAT%d_%s"%(chamber_config[link],vfat,dac),"EMFNRS","",
                                                                fitMin,fitMax)
                rawFitChi2  = rawfit[vfat][ "raw%s"%( dac)].GetChisquare()
                rawFitNDF   = rawfit[vfat][ "raw%s"%( dac)].GetNDF()
                convFitChi2 = convfit[vfat]["conv%s"%(dac)].GetChisquare()
                convFitNDF  = convfit[vfat]["conv%s"%(dac)].GetNDF()
                print("ranged: VFAT%d %s %2.4g/%2.4g  %2.4g/%2.4g"%(vfat,dac,rawFitChi2,rawFitNDF,convFitChi2,convFitNDF))
                rawResult.Print("V")
                convResult.Print("V")
                sys.stdout.flush()
                fitting = False
                pass

            canvs["raw"].cd(can)
            rawhist[vfat]["raw%s"%(dac)].SetXTitle("%s^{DAC} [VFAT DAC Units]"%(dacmode[dac]))
            rawhist[vfat]["raw%s"%(dac)].SetYTitle("%s^{Out} [xADC]"%(dacmode[dac]))
            rawhist[vfat]["raw%s"%(dac)].Draw("colz")
            r.gStyle.SetOptStat(11111111)

            canvs["conv"].cd(can)
            convhist[vfat]["conv%s"%(dac)].SetXTitle("%s^{DAC} [VFAT DAC Units]"%(dacmode[dac]))
            convhist[vfat]["conv%s"%(dac)].SetYTitle("%s^{Out} [%s]"%(dacmode[dac],"A" if dacmode[dac][0]=="I" else "V"))
            convhist[vfat]["conv%s"%(dac)].Draw("colz")
            r.gStyle.SetOptStat(11111111)

            outdata.write("%s_VFAT%02d %s %f %f\n"%(chamber_config[link],vfat,dac,
                                                      convfit[vfat]["conv%s"%(dac)].GetParameter(0),
                                                      convfit[vfat]["conv%s"%(dac)].GetParameter(1)))

            # param0hist[  dac].Fill(      convfit[vfat]["conv%s"%(dac)].GetParameter(0))
            # param1hist[  dac].Fill(1000.*convfit[vfat]["conv%s"%(dac)].GetParameter(1))
            # param0v1hist[dac].Fill(      convfit[vfat]["conv%s"%(dac)].GetParameter(0),
            #                            1000.*convfit[vfat]["conv%s"%(dac)].GetParameter(1))

            outfile.cd()
            rawfit[vfat][  "raw%s"%( dac)].Write()
            convfit[vfat][ "conv%s"%(dac)].Write()
            convhist[vfat]["conv%s"%(dac)].Write()
            rawhist[vfat][ "raw%s"%( dac)].Write()
            pass
        for con in ["raw","conv"]:
            canvs[con].SaveAs("/tmp/%s/%s_VFAT%d_%s_%s.png"%(os.getenv('USER'),chamber_config[link],vfat,infname,con))
            canvs[con].SaveAs("/tmp/%s/%s_VFAT%d_%s_%s.pdf"%(os.getenv('USER'),chamber_config[link],vfat,infname,con))
            # canvs[con].SaveAs("/tmp/%s/%s_VFAT%d_%s_%s.C"%(  os.getenv('USER'),chamber_config[link],vfat,infname,con))
            pass
        pass

    # r.gROOT.SetBatch(False)
    vcalfit = None
    for vfat in range(24):
        canvs = r.TCanvas("canvs","",1600,900)
        # get the
        vcalfit = r.TF1("vcal%s_VFAT%d"%(chamber_config[link],vfat),"%s-%s"%(
            convfit[vfat]["conv%s"%("CALOUTVHI")].GetName(),
            convfit[vfat]["conv%s"%("CALOUTVLOW")].GetName()
        ),0,256)
        convhist[vfat]["convCALOUTVHI"].Draw()
        convfit[vfat]["convCALOUTVHI"].SetLineWidth(2)
        convfit[vfat]["convCALOUTVHI"].SetLineStyle(2)
        convfit[vfat]["convCALOUTVHI"].SetLineColor(r.kBlue)
        convfit[vfat]["convCALOUTVHI"].Draw("same")

        convfit[vfat]["convCALOUTVLOW"].SetLineWidth(2)
        convfit[vfat]["convCALOUTVLOW"].SetLineStyle(2)
        convfit[vfat]["convCALOUTVLOW"].SetLineColor(r.kOrange)
        convfit[vfat]["convCALOUTVLOW"].Draw("same")

        vcalfit.SetLineWidth(2)
        vcalfit.SetLineStyle(2)
        vcalfit.SetLineColor(r.kRed)
        vcalfit.Draw("same")
        outdata.write("%s_VFAT%02d  V_Hi - V_Low   %f   %f\n"%(chamber_config[link],vfat,
                                                               vcalfit.GetParameter(0),
                                                               vcalfit.GetParameter(1)))
        vcalfit.Write()
        # raw_input("enter to continue")
        pass
    outdata.close()

    # for dac in sorted(dacmode.keys()):
    #     canvs = r.TCanvas("canvs","",1600,900)
    #     param0hist[dac].Draw()
    #     param0hist[dac].Write()
    #     canvs.SaveAs("param0hist%s_%s.png"%(dac,infname))
    #     param1hist[dac].Draw()
    #     param1hist[dac].Write()
    #     canvs.SaveAs("param1hist%s_%s.png"%(dac,infname))
    #     param0v1hist[dac].Draw("colz")
    #     param0v1hist[dac].Write()
    #     canvs.SaveAs("param0v1hist%s_%s.png"%(dac,infname))
    #     pass
    outfile.Write()
    outfile.Close()
    return

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("infname", help="Input file name (part between 'DACScanData_' and '.root'",type=str)
    parser.add_argument("-d", "--debug", help="debugging information",action="store_true")
    parser.add_argument("--link", help="Specify a link to process",type=int,default=99)
    parser.add_argument("--chip", help="Specify a chip to process",type=int,default=99)

    args = parser.parse_args()

    extractResults(args.infname,args.link)
    print("Done processing DACs for link%d"%(args.link))
