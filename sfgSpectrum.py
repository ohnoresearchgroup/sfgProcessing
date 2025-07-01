import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, peak_widths
from scipy.signal import savgol_filter
from scipy.optimize import curve_fit
from scipy import exp
import os
import copy
from scipy.interpolate import interp1d

class SFGspectrum():
    def __init__(self,path,stretch,name,files,filesBG,filesCalib,skip=None):

        self.path = path
        self.stretch = stretch
        self.name = name
        
        self.files = files
        self.filesBG = filesBG
        self.filesCalib = filesCalib
        
        #skip files of names given to skip
        if skip is not None:
            for skipfile in skip:
                self.files = [f for f in self.files if skipfile not in f]    
        
        #import background spectra
        if self.filesBG[0] is not None:
            for file in self.filesBG:
                if ('calib' not in file):
                    if file.endswith(".asc"):
                        self.bg = self.importAndor(path + file)
                    elif file.endswith(".csv"):
                        self.bg = self.importPI(path + file)
                    else:
                        print('not correct file type.')
                    break
        else:
            print('No background file found')
            return
        
        #import SFG spectra
        self.scans = []
        for file in self.files:
            if file.endswith(".asc"):
                scan = self.importAndor(path + file)
            elif file.endswith(".csv"):
                scan = self.importPI(path + file)
            else:
                print('not correct file type.')
            scan['wn'] = convert_SFG_to_IRwn(scan['wl'],1034)
            scan['raw'] = scan['counts']
            scan['counts'] = scan['counts'] - self.bg['counts']
            self.scans.append(scan)
            
    def importAndor(self,name):
        df = pd.read_csv(name, delimiter='\t', names=['wl', 'counts'], skiprows=37, engine='python')
        return df
    
    def importPI(self,name):        
        df = pd.read_csv(name)
        numFrames = df['Frame'].max()
        counts = np.zeros(1340)
        ind_dfs = []
        for i in range(numFrames):
            filtered_df = df[df['Frame'] == i + 1]
            filtered_df = filtered_df.reset_index(drop=True)
            #add up intensity from individual frames
            counts = counts + filtered_df['Intensity'].values
            
            #rename column for intensity of individual frame
            newname = 'Frame' + str(i+1)
            filtered_df.rename(columns={'Intensity': newname }, inplace=True)
            ind_dfs.append(filtered_df)
        
        #combine each dataframe, dropping duplicate columns
        df_combined = pd.concat(ind_dfs, axis=1).loc[:, ~pd.concat(ind_dfs, axis=1).columns.duplicated()]
        df_combined['counts'] = counts
        df_combined.drop(['ROI','Frame','Row','Column'], axis = 1, inplace = True)
        df_combined.rename(columns={'Wavelength': 'wl'}, inplace=True)
        
        return df_combined
        

            
    def plot(self):
        plt.figure()
        for scan in self.scans:
            plt.plot(scan['wn'],scan['counts'])
            plt.title('BG corrected scans')
            
    def plotScan(self,scannum,xlim=None):
        plt.figure()
        plt.plot(self.scans[scannum]['wn'],self.scans[scannum]['counts'])
        plt.title("Scan: " + str(scannum))
        if xlim is not None:
            plt.xlim(xlim[0],xlim[1])

    def setBlank(self):
        #set blank interpolation function
        blank = self.gaussiannorm
        x = self.scans[0]['wn']
        return interp1d(x, blank, kind='linear', fill_value="extrapolate")

    def checkEtalonCorrection(self,blank_interpolate, guess = None, region = 'CH'):
        self.blank_interpolate = blank_interpolate

        if region == 'CH':
            xlims = [2750,3050]
        elif region == 'CN':
            xlims = [2100,2225]
        else:
            print("unknown region: " + region)

        # if doesn't have gaussian norm, create guassian norm
        if not hasattr(self, 'gaussiannorm'):
            self.fitgaussians()

        y = self.gaussiannorm
        x = self.scans[0]['wn']

        correcteds = []
        for i in range(25):
            blank_i = self.blank_interpolate(x + i)
            corrected_i = y/blank_i
            correcteds.append(corrected_i)

        plt.figure()
        for idx,corrected in enumerate(correcteds):
            plt.plot(x,corrected+idx)
        plt.xlim(xlims)
        plt.ylim([0,26])
        ax=plt.gca()
        x0,x1 = ax.get_xlim()
        y0,y1 = ax.get_ylim()
        ax.set_aspect(abs(x1-x0)/abs(y1-y0)*2)

        if guess is not None:
            i = guess - 1
            plt.figure()
            plt.plot(x,correcteds[i-1],label = str(i))
            plt.plot(x,correcteds[i],label = str(i+1))
            plt.plot(x,correcteds[i+1],label = str(i+2))
            plt.xlim(xlims)
            plt.ylim([0,2])
            plt.legend()
            ax=plt.gca()
            x0,x1 = ax.get_xlim()
            y0,y1 = ax.get_ylim()
            ax.set_aspect(abs(x1-x0)/abs(y1-y0))
        
        
    def corrEtalon(self,idx):
        # if hasn't been done before, create deep copy in scans_uncorr
        if not hasattr(self, 'scans_uncorr'):
            self.scans_uncorr = copy.deepcopy(self.scans)

        x = self.scans[0]['wn']
        blank = self.blank_interpolate(x + idx-1)

        for idx,scan in enumerate(self.scans):
            scan['counts'] = self.scans_uncorr[idx]['counts']/blank
        
            
        
        
    def calibPS(self,fitrange,num=0,second = None):
        print("PS calibration files available: ")
        for file in self.filesCalib:
            print(file)

        print("PS calibration with file ",num," chosen.")

        #import calibration spectra
        file = self.filesCalib[num]
        if file.endswith(".asc"):
            self.ps = self.importAndor(self.path + file)
        elif file.endswith(".csv"):
            self.ps = self.importPI(self.path + file)
        else:
            print('not correct file type.')
        self.ps['wn'] = convert_SFG_to_IRwn(self.ps['wl'],1034)

        #plt calibration spectra
        plt.figure()
        plt.plot(self.ps['wn'],self.ps['counts'])
        plt.xlim([2700,3000])
        plt.title('PS Spectrum')
    
        #indexes for the values entered that bound the peak
        idx1 = (np.abs(self.ps['wn'] - fitrange[0])).argmin()
        idx2 = (np.abs(self.ps['wn'] - fitrange[1])).argmin()
        
        #segments within bounds
        xShort = np.abs(self.ps['wn'][idx2:idx1+1].values)
        yShort = np.abs(self.ps['counts'][idx2:idx1+1].values)

        #gaussian function to fit the segment
        def twogauss(x,a1,xcen1,sigma1,a2,xcen2,sigma2,off):
            return -a1*np.exp(-(x-xcen1)**2/(2*sigma1**2)) + a2*np.exp(-(x-xcen2)**2/(2*sigma2**2))+off
        
        #initial guesses for the fit                        
        xcen1 = (fitrange[0]+fitrange[1])/2
        sigma1 = 20
        a1 = self.ps['counts'].max()/2

        xcen2 = 2900
        sigma2 = 200
        a2 = self.ps['counts'].max()
        off = 0
        
        guesses =[a1,xcen1,sigma1,a2,xcen2,sigma2,off]
        lw = [0,2700,1,0,2700,10,0]
        up = [self.ps['counts'].max(),3000,50,self.ps['counts'].max()*2,3100,1000,self.ps['counts'].max()]
       
        plt.figure()
        plt.plot(self.ps['wn'][idx2-5:idx1+5],self.ps['counts'][idx2-5:idx1+5])
        
        #fit 
        popt,pcov = curve_fit(twogauss,xShort,yShort,p0=guesses,bounds = [lw,up],maxfev = 10000)
        
        #plot with fit and points
        plt.plot(xShort,twogauss(xShort,*popt),'ro:',label='fit')
        plt.plot(self.ps['wn'][idx2],self.ps['counts'][idx2],'o',markersize=5)
        plt.plot(self.ps['wn'][idx1],self.ps['counts'][idx1],'o',markersize=5)
        plt.title('Fitted PS Calibration')
        
        #set shift for this peak
        shift = popt[1]-2850.13
        print('1st shift is ',shift)

        #also calibrate to the second peak    
        if second is not None:
                #plt calibration spectra
            plt.figure()
            plt.plot(self.ps['wn'],self.ps['counts'])
            plt.xlim([2900,3100])
            plt.title('PS Spectrum 2')

            #indexes for the values entered that bound the peak
            idx1 = (np.abs(self.ps['wn'] - second[0])).argmin()
            idx2 = (np.abs(self.ps['wn'] - second[1])).argmin()
        
            #segments within bounds
            xShort = np.abs(self.ps['wn'][idx2:idx1+1].values)
            yShort = np.abs(self.ps['counts'][idx2:idx1+1].values)

            #initial guesses for the fit                        
            xcen1 = (second[0]+second[1])/2
            sigma1 = 20
            a1 = self.ps['counts'].max()/2

            xcen2 = 3000
            sigma2 = 200
            a2 = self.ps['counts'].max()
            off = 0
        
            guesses =[a1,xcen1,sigma1,a2,xcen2,sigma2,off]
            lw = [0,2700,1,0,2700,10,0]
            up = [self.ps['counts'].max(),3200,50,self.ps['counts'].max()*2,3200,1000,self.ps['counts'].max()]
       
            plt.figure()
            plt.plot(self.ps['wn'][idx2-5:idx1+5],self.ps['counts'][idx2-5:idx1+5])
        
            #fit 
            popt,pcov = curve_fit(twogauss,xShort,yShort,p0=guesses,bounds = [lw,up],maxfev = 10000)
        
            #plot with fit and points
            plt.plot(xShort,twogauss(xShort,*popt),'ro:',label='fit')
            plt.plot(self.ps['wn'][idx2],self.ps['counts'][idx2],'o',markersize=5)
            plt.plot(self.ps['wn'][idx1],self.ps['counts'][idx1],'o',markersize=5)
            plt.title('2nd Fitted PS Calibration')

            #set shift for this peak
            shift2 = popt[1]-3001.40
            print('2nd shift is ',shift2)

            totalshift = (shift+shift2)/2
            print("Total shift is ", totalshift)

            for scan in self.scans:
                scan['wn'] = scan['wn'] - totalshift
                
            print('Double PS calibration applied.')
        else:
            for scan in self.scans:
                scan['wn'] = scan['wn'] - shift
            print('Single Calibration applied.')

        #plt calibration spectra
        plt.figure()
        plt.plot(scan['wn'],self.ps['counts'])
        plt.xlim([2700,3100])
        plt.title('Calibrated PS Spectrum')


        


    def calibACN(self,range=[2100,2300],initpeak = 2250,shift = None):
        #if hardcoded shift is entered, perform shift and return
        if shift is not None:
            print('Entered shift is ',shift)
            for scan in self.scans:
                scan['wn'] = scan['wn'] - shift
            print('Entered ACN Calibration applied.')
            return
            
        self.acnpeakvalue = 2253.6

        
        print('ACN calibration file:')
        self.calibACNfile = [file for file in self.filesCalib if ('bg' not in file) and ('calib' in file)][0]
        print(self.calibACNfile)
        
        if self.calibACNfile.endswith(".asc"):
            self.calibACN = self.importAndor(self.path +  self.calibACNfile)
        elif self.calibACNfile.endswith(".csv"):
            self.calibACN = self.importPI(self.path +  self.calibACNfile)
        else:
            print('not correct file type.')

        self.calibACN['wn'] = convert_SFG_to_IRwn(self.calibACN['wl'],1034)


        #plt calibration spectra
        plt.figure()
        plt.plot(self.calibACN['wn'],self.calibACN['counts'])
        plt.xlim([2100,2350])
        plt.title('ACN Calibration')

        #indexes for the values entered that bound the peak
        idx1 = (np.abs(self.calibACN['wn'] - range[0])).argmin()
        idx2 = (np.abs(self.calibACN['wn'] - range[1])).argmin()
        
        #segments within bounds
        xShort = np.abs(self.calibACN['wn'][idx2:idx1+1].values)
        yShort = np.abs(self.calibACN['counts'][idx2:idx1+1].values)

        #gaussian function to fit the segment
        def twogauss(x,a1,xcen1,sigma1,a2,xcen2,sigma2,off):
            return -a1*np.exp(-(x-xcen1)**2/(2*sigma1**2)) + a2*np.exp(-(x-xcen2)**2/(2*sigma2**2))+off
        
        #initial guesses for the fit                        
        xcen1 = (range[0]+range[1])/2
        sigma1 = 20
        a1 = self.calibACN['counts'].max()/2

        xcen2 = initpeak
        sigma2 = 20
        a2 = self.calibACN['counts'].max()
        off = 0
        
        guesses =[a1,xcen1,sigma1,a2,xcen2,sigma2,off]
        lw = [0,2100,1,0,2100,1,0]
        up = [self.calibACN['counts'].max(),2300,1000,self.calibACN['counts'].max()*2,2300,1000,self.calibACN['counts'].max()]
       
        plt.figure()
        plt.plot(self.calibACN['wn'][idx2-5:idx1+5],self.calibACN['counts'][idx2-5:idx1+5])
        
        #fit 
        popt,pcov = curve_fit(twogauss,xShort,yShort,p0=guesses,bounds = [lw,up],maxfev = 10000)
        
        #plot with fit and points
        plt.plot(xShort,twogauss(xShort,*popt),'ro:',label='fit')
        plt.plot(self.calibACN['wn'][idx2],self.calibACN['counts'][idx2],'o',markersize=5)
        plt.plot(self.calibACN['wn'][idx1],self.calibACN['counts'][idx1],'o',markersize=5)
        plt.title('Fitted ANC Calibration')
        
        #set shift for this peak
        shift = popt[1]- self.acnpeakvalue
        print('Fitted ACN peak center:' + str(popt[1]))
        print('Shift is ',shift)
        for scan in self.scans:
            scan['wn'] = scan['wn'] - shift
        print('ACN Calibration applied.')


    def calibCO2(self):
        return

        
        

        
    def fitgaussians(self,goldparams=None):
        if goldparams == None:
            if self.stretch == 'CN':
                goldparams = ([0,20000,2000000],[1800,2100,2300],[0,50,1000])
            elif self.stretch == 'CH':
                goldparams = ([0,20000,2000000],[2700,2900,3100],[0,50,1000])
        
        guesses = [goldparams[0][1],goldparams[1][1],goldparams[2][1]]
        lw = [goldparams[0][0],goldparams[1][0],goldparams[2][0]]
        up = [goldparams[0][2],goldparams[1][2],goldparams[2][2]]


        def gaussianGold(wn, gold_amp, gold_w, gold_width):
            return gold_amp*np.exp(-(wn-gold_w)**2/gold_width**2)

        #background subtract and sum
        self.sumdata = 0
        self.sumfits = 0
        plt.figure()
        for scan in self.scans:
            xdata = scan['wn']
            ydata = scan['counts']
            popt, pcov = curve_fit(gaussianGold, xdata, ydata, p0=guesses,bounds = [lw,up], maxfev = 10000)
            plt.plot(xdata,gaussianGold(xdata,popt[0],popt[1],popt[2])/popt[0])
            plt.plot(xdata,ydata/popt[0])
            self.sumdata = self.sumdata + ydata/popt[0]
            self.sumfits = self.sumfits + gaussianGold(xdata,popt[0],popt[1],popt[2])/popt[0]
            #print(popt)
        ax = plt.gca()
        ax.set_facecolor('white')
        plt.ylabel('SFG Intensity [counts]')
        plt.xlabel('Wavenumber [cm^-1]')
        if self.stretch == 'CH':
            plt.xlim([2750, 3150])
        if self.stretch == 'CN':
            plt.xlim([1900, 2350])


        plt.figure()
        plt.plot(xdata,self.sumdata)
        plt.plot(xdata,self.sumfits)

        plt.figure()
        plt.plot(xdata,self.sumdata/self.sumfits)
        
        self.gaussiannorm = self.sumdata/self.sumfits
        
        if self.stretch == 'CH':
            plt.xlim([2750, 3050])
        if self.stretch == 'CN':
            plt.xlim([2100, 2225])
        plt.ylim([0, 2])
        ax=plt.gca()
        x0,x1 = ax.get_xlim()
        y0,y1 = ax.get_ylim()
        ax.set_aspect(abs(x1-x0)/abs(y1-y0))
        plt.title(self.name)
        plt.xlabel('Wavenumber [cm$^{-1}$]')
        plt.ylabel('SFG Intensity [a.u.]')
        set_size(3,3)
        plt.tight_layout()
            
    def fitLorentzians(self,scannum,goldparams,oscparams,scaling=None,xlim=None,fitrange=None):      
        scan = self.scans[scannum]
        lw = [sublist[0] for sublist in goldparams]
        gs = [sublist[1] for sublist in goldparams]
        up = [sublist[2] for sublist in goldparams]
        
        oscnum = len(oscparams)
        for osc in oscparams:
            osclw = [sublist[0] for sublist in osc]
            oscgs = [sublist[1] for sublist in osc]
            oscup = [sublist[2] for sublist in osc]
            
            lw.extend(osclw)
            gs.extend(oscgs)
            up.extend(oscup)
                
        print(lw)
        print(gs)
        print(up)
            

        def lorentzian(wn,amp,center,gamma,phase):
            return (amp/(wn-center+1j*gamma))*np.exp(1j*phase)
        
        def fitFlexible(wn, gold_amp, gold_center, gold_width, *oscparams):
            if len(oscparams) % 4 == 0:
                numoscs = int(len(oscparams)/4)
                y = np.zeros(len(wn))
                for i in range(numoscs):
                    y = y + lorentzian(wn,oscparams[4*i],oscparams[4*i+1],oscparams[4*i+2],oscparams[4*i+3])
                y = y + gold_amp
                y = np.abs(y)**2*np.exp(-(wn-gold_center)**2/gold_width**2)
                return y
            else:
                print('number of osc params incorrect')

        xdata = scan['wn']
        ydata = scan['counts']/np.max(scan['counts'])
        if fitrange is not None:
            idx1 = np.absolute(xdata-fitrange[1]).argmin()
            idx2 = np.absolute(xdata-fitrange[0]).argmin()
            xdata = xdata[idx1:idx2]
            ydata = ydata[idx1:idx2]
        
        popt, pcov = curve_fit(fitFlexible, xdata, ydata, p0=gs,bounds = [lw,up], maxfev = 10000)
        oscparamfit = popt[3:]
        oscparamfit_error = np.sqrt(np.diag(pcov))[3:]

        print(oscparamfit)
        print(oscparamfit_error)

        


        
        plt.figure()
        plt.plot(xdata,ydata,'o')
        plt.plot(xdata,fitFlexible(xdata,popt[0],popt[1],popt[2],*oscparamfit))
        totalFit = fitFlexible(xdata,popt[0],popt[1],popt[2],*oscparamfit)
        numoscs = int(len(oscparamfit)/4)
        for i in range(numoscs):
            plt.plot(xdata,np.sqrt(np.abs(lorentzian(xdata,popt[4*i+3],popt[4*i+4],popt[4*i+5],popt[4*i+6]))**2))
        if xlim is not None:
            plt.xlim(xlim[0],xlim[1])
        ax=plt.gca()
        x0,x1 = ax.get_xlim()
        y0,y1 = ax.get_ylim()
        ax.set_aspect(abs(x1-x0)/abs(y1-y0))
        plt.title(self.name)
        plt.xlabel('Wavenumber [cm$^{-1}$]')
        plt.ylabel('SFG Intensity [a.u.]')
        set_size(3,3)
        plt.tight_layout()
        
        print()
        print('gold amp =',  np.round(popt[0],1))
        print('gold center =',  np.round(popt[1],1))
        print('gold width =',  np.round(popt[2],1))
        print()
        
        outputLorentzians = []
        for i in range(int(len(oscparamfit)/4)):
            l = [oscparamfit[4*i],oscparamfit[4*i+1],oscparamfit[4*i+2],oscparamfit[4*i+3]]
            print("Osc ",i+1,"amp =", np.round(oscparamfit[4*i],1))
            print("Osc ",i+1,"center =", np.round(oscparamfit[4*i+1],1))
            print("Osc ",i+1,"gamma =", np.round(oscparamfit[4*i+2],1))
            print("Osc ",i+1,"phase =", np.round(np.degrees(oscparamfit[4*i+3]),1))

            print("Osc ",i+1,"amp_error =", np.round(oscparamfit_error[4*i],2))
            print("Osc ",i+1,"center_error =", np.round(oscparamfit_error[4*i+1],2))
            print("Osc ",i+1,"gamma_error =", np.round(oscparamfit_error[4*i+2],2))
            print("Osc ",i+1,"phase_error  =", np.round(np.degrees(oscparamfit_error[4*i+3]),2))
            print()
            outputLorentzians.append(l)
        
        return (outputLorentzians,totalFit,ydata,xdata)

    def plotLorentzians(self,listLorentzians,xlim=None,ylim=None):
        def lorentzian(wn,amp,center,gamma,phase):
            return (amp/(wn-center+1j*gamma))*np.exp(1j*phase)
    
        plt.figure()
        plt.plot(self.scans[0]['wn'],self.gaussiannorm)
        for l in listLorentzians:
            plt.plot(self.scans[0]['wn'],np.sqrt(np.abs(lorentzian(self.scans[0]['wn'],l[0],l[1],l[2],l[3]))**2))    
        if xlim is not None:
            plt.xlim(xlim[0],xlim[1])
        if ylim is not None:
            plt.ylim(ylim[0],ylim[1])
        ax=plt.gca()
        x0,x1 = ax.get_xlim()
        y0,y1 = ax.get_ylim()
        ax.set_aspect(abs(x1-x0)/abs(y1-y0))
        plt.title(self.name)
        plt.xlabel('Wavenumber [cm$^{-1}$]')
        plt.ylabel('SFG Intensity [a.u.]')
        set_size(3,3)
        plt.tight_layout()
    



def calcSFGwl(wl1,wl2):
        wl = ((wl1**-1) + (wl2**-1))**-1
        return wl

def convert_SFG_to_IRwn(SFG,vis):
    IR = 1e7/((SFG**-1) - (vis**-1))**-1
    return IR

def modified_z_score(intensity):
        median_int= np.median(intensity)
        mad_int = np.median([np.abs(intensity - median_int)])
        modified_z_scores = 0.6745 * (intensity - median_int) / mad_int
        return modified_z_scores

def removeCR(y,width, thresh):
        spikes = abs(np.array(modified_z_score(np.diff(y)))) > thresh
        y_out = y.copy() # So we don’t overwrite y
        for i in np.arange(len(spikes)):
            if spikes[i] != 0: # If we have an spike in position i
                w = np.arange(i-width,i+1+width) # we select 2 m + 1 points around our spike
                w2 = w[spikes[w] == 0] # From such interval, we choose the ones which are not spikes
                y_out[i] = np.mean(y[w2]) # and we average their values
        return y_out

    
def set_size(w,h, ax=None):
    """ w, h: width, height in inches """
    if not ax: ax=plt.gca()
    l = ax.figure.subplotpars.left
    r = ax.figure.subplotpars.right
    t = ax.figure.subplotpars.top
    b = ax.figure.subplotpars.bottom
    figw = float(w)/(r-l)
    figh = float(h)/(t-b)
    ax.figure.set_size_inches(figw, figh)