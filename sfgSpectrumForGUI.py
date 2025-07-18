import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
import os
import copy
from matplotlib.figure import Figure
import matplotlib as mpl

# Set global font size BEFORE creating the figure
mpl.rcParams.update({
    'font.size': 5,         # Global font size
    'font.family': 'Arial',  # Optional: set font family
    'lines.linewidth': 1.0
})

#dimension of figures
fig_dim = 1.45
fig_dpi = 200

class SFGspectrumForGUI():
    def __init__(self,path,region,name,filesSFG,filesBG,filesCalib):
        
        #path to folder
        self.path = path
        
        #region of spectra: CH, CN, etc.
        self.region = region
        
        #unique sample name
        self.name = name
        
        #variable to store calibration offset
        self.shift = 0
        
        #lists of the sorted sample files, bg files, and calibration files
        self.filesSFG = filesSFG
        self.filesBG = filesBG
        self.filesCalib = filesCalib
        
        #import background spectrum
        if self.filesBG[0] is not None:
            for file in self.filesBG:
                if ('calib' not in file):
                    fullpath = os.path.join(path,file)
                    self.bg = importSFG(fullpath)
        else:
            print('No background file found')
            return
        
        #import SFG spectra
        self.scans = []
        for file in self.filesSFG:
            fullpath = os.path.join(path,file)
            scan = importSFG(fullpath)
            scan['wn'] = convert_SFG_to_IRwn(scan['wl'],1034)
            scan['raw'] = scan['counts']
            scan['counts'] = scan['counts'] - self.bg['counts']
            self.scans.append(scan)
            

        #import calibration spectra
        self.calib_scans = []
        for file in self.filesCalib:
            fullpath = os.path.join(self.path, file)
            calibscan = importSFG(fullpath)
            calibscan['wn'] = convert_SFG_to_IRwn(calibscan['wl'],1034)
            self.calib_scans.append(calibscan)
  
        #store number of scans
        self.num_scans = len(self.scans)
            
        #create a deep copy that holds uncalibrated wavenumbers    
        self.scans_uncorr = copy.deepcopy(self.scans)


    #plots all the SFG spectra for this sample      
    def plot(self):
        fig = Figure(figsize=(fig_dim,fig_dim), dpi=fig_dpi)
        ax = fig.add_subplot(111)
        for scan in self.scans:
            ax.plot(scan['wn'],scan['counts'])
            
        ax.set_title('BG corrected scans')
        ax.set_xlabel('Wavenumber [cm$^{-1}$]')
        ax.set_ylabel('SFG Intensity [counts]')
        fig.tight_layout() 
        return fig
         
    #plots one identified spectra
    def plotScan(self,scannum,xlim=None):
        fig = Figure(figsize=(fig_dim,fig_dim), dpi=fig_dpi)
        ax = fig.add_subplot(111)
        ax.plot(self.scans[scannum]['wn'],self.scans[scannum]['counts'])
        ax.set_title("Scan: " + str(scannum))
        if xlim is not None:
            ax.set_xlim(xlim[0],xlim[1])
        ax.set_xlabel('Wavenumber [cm$^{-1}$]')
        ax.set_ylabel('SFG Intensity [counts]')
        fig.tight_layout() 
        return fig
            
    
    #adjusts the x-axis following the calibrated shift
    def apply_calib(self):
        for i, scan in enumerate(self.scans):
            self.scans[i]['wn'] = self.scans_uncorr[i]['wn'] - self.shift
        print('Calibration applied.')
        return
        
    #do the fit to calculate the shift        
    def fit_calib(self,fitrange):
        if self.region == 'CH':
            fig = self.fit_calibPS(fitrange)
        elif self.region =='CN':
            fig = self.fit_calibACN(fitrange)
        else:
            print("No calibration code for that region")
        return fig
        
    def fit_calibPS(self,fitrange,num=0):
        #right now just does first ps spectrum available but future code could allow selection
        print("PS calibration files available: ")
        for file in self.filesCalib:
            print(file)
        print("PS calibration file ", num, " chosen.")
        
        self.calib_spectrum = self.calib_scans[num]
    
        #indexes for the values entered that bound the peak
        idx1 = (np.abs(self.calib_spectrum['wn'] - fitrange[0])).argmin()
        idx2 = (np.abs(self.calib_spectrum['wn'] - fitrange[1])).argmin()
        
        #segments within bounds
        xShort = np.abs(self.calib_spectrum['wn'][idx2:idx1+1].values)
        yShort = np.abs(self.calib_spectrum['counts'][idx2:idx1+1].values)
        
        #initial guesses for the fit                        
        xcen1 = (fitrange[0]+fitrange[1])/2
        sigma1 = 20
        a1 = self.calib_spectrum['counts'].max()/2

        xcen2 = 2900
        sigma2 = 200
        a2 = self.calib_spectrum['counts'].max()
        off = 0
        
        guesses =[a1,xcen1,sigma1,a2,xcen2,sigma2,off]
        lw = [0,2700,1,0,2700,10,0]
        up = [self.calib_spectrum['counts'].max(),3000,50,self.calib_spectrum['counts'].max()*2,3100,1000,self.calib_spectrum['counts'].max()]
       
        fig = Figure(figsize=(fig_dim*0.75,fig_dim*0.75), dpi=fig_dpi)
        ax = fig.add_subplot(111)
        ax.plot(self.calib_spectrum['wn'][idx2-5:idx1+5],self.calib_spectrum['counts'][idx2-5:idx1+5])
        
        #fit 
        popt,pcov = curve_fit(twogauss,xShort,yShort,p0=guesses,bounds = [lw,up],maxfev = 10000)
        
        #plot with fit and points
        ax.plot(xShort,twogauss(xShort,*popt),'ro:',label='fit',markersize=1)
        ax.plot(self.calib_spectrum['wn'][idx2],self.calib_spectrum['counts'][idx2],'o',markersize=1)
        ax.plot(self.calib_spectrum['wn'][idx1],self.calib_spectrum['counts'][idx1],'o',markersize=1)
        ax.set_title('Fitted PS Calibration')
        ax.set_xlabel('Wavenumber [cm$^{-1}$]')
        ax.set_ylabel('SFG Intensity [a.u.]')
        fig.tight_layout() 
        
        #set shift for this peak
        shift = popt[1]-2850.13
        print('shift is ',shift)
        self.shift = shift
        
        return fig

    def fit_calibACN(self,fitrange):
        #reference peak value
        self.acnpeakvalue = 2253.6
        
        #takes first calibration spectrum
        self.calib_spectrum = self.calib_scans[0]

        #indexes for the values entered that bound the peak
        idx1 = (np.abs(self.calib_spectrum['wn'] - fitrange[0])).argmin()
        idx2 = (np.abs(self.calib_spectrum['wn'] - fitrange[1])).argmin()
        
        #segments within bounds
        xShort = np.abs(self.calib_spectrum['wn'][idx2:idx1+1].values)
        yShort = np.abs(self.calib_spectrum['counts'][idx2:idx1+1].values)
        
        #initial guesses for the fit                        
        xcen1 = (fitrange[0]+fitrange[1])/2
        sigma1 = 20
        a1 = self.calib_spectrum['counts'].max()/2

        xcen2 = 2250
        sigma2 = 20
        a2 = self.calib_spectrum['counts'].max()
        off = 0
        
        guesses =[a1,xcen1,sigma1,a2,xcen2,sigma2,off]
        lw = [0,2100,1,0,2100,1,0]
        up = [self.calib_spectrum['counts'].max(),2300,1000,self.calib_spectrum['counts'].max()*2,2300,1000,self.calib_spectrum['counts'].max()]
       
        fig = Figure(figsize=(fig_dim*0.75,fig_dim*0.75), dpi=fig_dpi)
        ax = fig.add_subplot(111)
        ax.plot(self.calib_spectrum['wn'][idx2-5:idx1+5],self.calib_spectrum['counts'][idx2-5:idx1+5])
        
        #fit 
        popt,pcov = curve_fit(twogauss,xShort,yShort,p0=guesses,bounds = [lw,up],maxfev = 10000)
        
        #plot with fit and points
        ax.plot(xShort,twogauss(xShort,*popt),'ro:',label='fit',markersize=1)
        ax.plot(self.calib_spectrum['wn'][idx2],self.calib_spectrum['counts'][idx2],'o',markersize=1)
        ax.plot(self.calib_spectrum['wn'][idx1],self.calib_spectrum['counts'][idx1],'o',markersize=1)
        #ax.set_title('Fitted ANC Calibration')
        #ax.set_xlabel('Wavenumber [cm$^{-1}$]')
        #ax.set_ylabel('SFG Intensity [a.u.]')
        fig.tight_layout() 
        
        #set shift for this peak
        shift = popt[1]- self.acnpeakvalue
        print('Fitted ACN peak center:' + str(popt[1]))
        print('Shift is ',shift)
        
        self.shift = shift
        print('ACN Calibration applied.')
        
        return fig


    def fitgaussians(self,goldparams=None):
        if goldparams == None:
            if self.region == 'CN':
                goldparams = ([0,20000,2000000],[1800,2100,2300],[0,50,1000])
            elif self.region == 'CH':
                goldparams = ([0,20000,2000000],[2700,2900,3100],[0,50,1000])
        
        guesses = [goldparams[0][1],goldparams[1][1],goldparams[2][1]]
        lw = [goldparams[0][0],goldparams[1][0],goldparams[2][0]]
        up = [goldparams[0][2],goldparams[1][2],goldparams[2][2]]


        def gaussianGold(wn, gold_amp, gold_w, gold_width):
            return gold_amp*np.exp(-(wn-gold_w)**2/gold_width**2)

        #background subtract and sum
        self.sumdata = 0
        self.sumfits = 0
        
        fig_fg = Figure(figsize=(fig_dim,fig_dim), dpi=fig_dpi)
        ax = fig_fg.add_subplot(111)
        for scan in self.scans:
            xdata = scan['wn']
            ydata = scan['counts']
            popt, pcov = curve_fit(gaussianGold, xdata, ydata, p0=guesses,bounds = [lw,up], maxfev = 10000)
            ax.plot(xdata,gaussianGold(xdata,popt[0],popt[1],popt[2])/popt[0])
            ax.plot(xdata,ydata/popt[0])
            self.sumdata = self.sumdata + ydata/popt[0]
            self.sumfits = self.sumfits + gaussianGold(xdata,popt[0],popt[1],popt[2])/popt[0]
            #print(popt)
        ax.set_facecolor('white')
        ax.set_xlabel('Wavenumber [cm$^{-1}$]')
        ax.set_ylabel('SFG Intensity [a.u.]')
        if self.region == 'CH':
            ax.set_xlim([2700, 3150])
        if self.region == 'CN':
            ax.set_xlim([2000, 2350])
        fig_fg.tight_layout() 


        fig_sum = Figure(figsize=(fig_dim,fig_dim), dpi=fig_dpi)
        ax = fig_sum.add_subplot(111)
        ax.plot(xdata,self.sumdata/self.sumfits)
        
        self.gaussiannorm = self.sumdata/self.sumfits
        
        if self.region == 'CH':
            ax.set_xlim([2750, 3050])
        if self.region == 'CN':
            ax.set_xlim([2100, 2250])
        ax.set_ylim([0, 2])
        x0,x1 = ax.get_xlim()
        y0,y1 = ax.get_ylim()
        ax.set_aspect(abs(x1-x0)/abs(y1-y0))
        ax.set_title(self.name)
        ax.set_xlabel('Wavenumber [cm$^{-1}$]')
        ax.set_ylabel('SFG Intensity [a.u.]')
        fig_sum.tight_layout() 
        
        #return the two figures
        return (fig_fg, fig_sum)
            
    def fitLorentzians(self,scannum,goldparams,oscparams,scaling=None,xlim=None,fitrange=None):
        #organize inputs for fitting
        scan = self.scans[scannum]
        lw = [sublist[0] for sublist in goldparams]
        gs = [sublist[1] for sublist in goldparams]
        up = [sublist[2] for sublist in goldparams]
        
        for osc in oscparams:
            osclw = [sublist[0] for sublist in osc]
            oscgs = [sublist[1] for sublist in osc]
            oscup = [sublist[2] for sublist in osc]
            
            lw.extend(osclw)
            gs.extend(oscgs)
            up.extend(oscup)
            
        #define individual lorentzian function
        def lorentzian(wn,amp,center,gamma,phase):
            return (amp/(wn-center+1j*gamma))*np.exp(1j*phase)
        
        #define overall fit function
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
        
        #perform the fit
        popt, pcov = curve_fit(fitFlexible, xdata, ydata, p0=gs,bounds = [lw,up], maxfev = 10000)
        oscparamfit = popt[3:]
        
        fig_fit = Figure(figsize=(fig_dim,fig_dim), dpi=fig_dpi)
        ax = fig_fit.add_subplot(111)
        ax.plot(xdata,ydata,'o',markersize= 1.2)
        ax.plot(xdata,fitFlexible(xdata,popt[0],popt[1],popt[2],*oscparamfit))
        
        numoscs = int(len(oscparamfit)/4)
        for i in range(numoscs):
            ax.plot(xdata,np.sqrt(np.abs(lorentzian(xdata,popt[4*i+3],popt[4*i+4],popt[4*i+5],popt[4*i+6]))**2))
        if xlim is not None:
            ax.set_xlim(xlim[0],xlim[1])
        x0,x1 = ax.get_xlim()
        y0,y1 = ax.get_ylim()
        ax.set_aspect(abs(x1-x0)/abs(y1-y0))
        ax.set_title(self.name)
        ax.set_xlabel('Wavenumber [cm$^{-1}$]')
        ax.set_ylabel('SFG Intensity [a.u.]')
        fig_fit.tight_layout()
        
        fitparams = popt
        fitparams_error = np.sqrt(np.diag(pcov))
        
        return (fig_fit, fitparams,fitparams_error)
        
#gaussian function to fit calibration spectra
def twogauss(x,a1,xcen1,sigma1,a2,xcen2,sigma2,off):
    return -a1*np.exp(-(x-xcen1)**2/(2*sigma1**2)) + a2*np.exp(-(x-xcen2)**2/(2*sigma2**2))+off

def convert_SFG_to_IRwn(SFG,vis):
    IR = 1e7/((SFG**-1) - (vis**-1))**-1
    return IR
    
def importSFG(name):
    if name.endswith(".asc"):
        df = importAndor(name)
    elif name.endswith(".csv"):
        df = importPI(name)
    else:
        print('not correct file type.')
        return
    return df
    
def importAndor(name):
    df = pd.read_csv(name, delimiter='\t', names=['wl', 'counts'], skiprows=37, engine='python')
    return df
    
def importPI(name):        
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