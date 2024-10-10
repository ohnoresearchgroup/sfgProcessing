import os
from sfgSpectrum import SFGspectrum

class SFGdataFolder():
    def __init__(self,path):
        self.path = path
        self.allFiles = os.listdir(path)
        self.ascFiles = [file for file in self.allFiles if file.endswith(".asc")]
        
        self.chNames = list(set([file.rsplit("_",2)[0] for file in self.ascFiles if file.split("_")[-2] == 'CH']))
        self.chNames.sort()
        self.chSpectra = {name: None for name in self.chNames}
        print("CH Spectra Available: ", self.chNames)

        self.cnNames = list(set([file.rsplit("_",2)[0] for file in self.ascFiles if file.split("_")[-2] == 'CN']))
        self.cnNames.sort()
        self.cnSpectra = {name: None for name in self.cnNames}
        print("CN Spectra Available: " ,self.cnNames)
        
        self.coNames = list(set([file.rsplit("_",2)[0] for file in self.ascFiles if file.split("_")[-2] == 'CO']))
        self.coNames.sort()
        self.coSpectra = {name: None for name in self.coNames}
        print("CO Spectra Available: " ,self.coNames)        
        
        print()
        print()
        
        print("CH:")
        print()
        print()
        self.chFiles = {}
        self.chFilesBG = {}
        self.chFilesCalib = {}
        for name in self.chNames:
            allSampleFiles = [file for file in self.ascFiles if name == file.split('_')[0]]
            self.chFiles[name] = [file for file in allSampleFiles if ((file.split('_')[-2] == 'CH') and ('bg' not in file))]
            self.chFilesBG[name] = [file for file in allSampleFiles if ((file.split('_')[-2] == 'CH') and ('bg' in file))]
            self.chFilesCalib[name] = [file for file in allSampleFiles if ('_pp_' in file) or ('_ps_' in file)]
            self.printFilesForName(name,"CH")
      
        print("CN:")
        print()
        print()        
        self.cnFiles = {}
        self.cnFilesBG = {}
        self.cnFilesCalib = {}
        for name in self.cnNames:
            allSampleFiles = [file for file in self.ascFiles if name == file.split('_')[0]]
            self.cnFiles[name] = [file for file in allSampleFiles if ((file.split('_')[-2] == 'CN') and ('bg' not in file) and ('4450' not in file) and ('calib' not in file))]
            self.cnFilesBG[name] = [file for file in allSampleFiles if ((file.split('_')[-2] == 'CN') and ('bg' in file))]
            self.cnFilesCalib[name] = [file for file in allSampleFiles if ((file.split('_')[-2] == 'CN') and (('4450' in file) or (('calib' in file) and ('bg' not in file))))]
            self.printFilesForName(name,"CN")
            
            
        print("CO:")
        print()
        print()        
        self.coFiles = {}
        self.coFilesBG = {}
        self.coFilesCalib = {}
        for name in self.coNames:
            allSampleFiles = [file for file in self.ascFiles if name == file.split('_')[0]]
            self.coFiles[name] = [file for file in allSampleFiles if ((file.split('_')[-2] == 'CO') and ('bg' not in file) and ('4450' not in file) and ('calib' not in file))]
            self.coFilesBG[name] = [file for file in allSampleFiles if ((file.split('_')[-2] == 'CO') and ('bg' in file))]
            self.coFilesCalib[name] = [file for file in allSampleFiles if ((file.split('_')[-2] == 'CO') and (('4450' in file) or (('calib' in file) and ('bg' not in file))))]
            self.printFilesForName(name,"CN")
            
    def printFilesForName(self,name,stretch):
        if stretch == 'CN':
            print("Sample Name: {}".format(name))
            print()
            print("Spectra Available:")
            for file in self.cnFiles[name]:
                  print(file)
            print()
            print("Background Available:")
            for file in self.cnFilesBG[name]:
                print(file)
            print()
            print("Calibration:")
            for file in self.cnFilesCalib[name]:
                print(file)
            print()
            print()
        elif stretch == 'CH':
            print("Sample Name: {}".format(name))
            print()
            print("Spectra Available:")
            for file in self.chFiles[name]:
                  print(file)
            print()
            print("Background Available:")
            for file in  self.chFilesBG[name]:
                print(file)
            print()
            print("Calibration:")
            for file in self.chFilesCalib[name]:
                print(file)
            print()
            print()
        elif stretch == 'CO':
            print("Sample Name: {}".format(name))
            print()
            print("Spectra Available:")
            for file in self.coFiles[name]:
                print(file)
            print()
            print("Background Available:")
            for file in  self.coFilesBG[name]:
                print(file)
            print()
            print("Calibration:")
            for file in self.coFilesCalib[name]:
                print(file)
            print()
            print()     
            
        else:
            print("No available stretch specified.")
        
            
    def processSpectrum(self,stretch,number,skip=None):
        if stretch == "CN":
            if number >= len(self.cnNames):
                print('Number greater than available CN spectra')
            else:
                name = self.cnNames[number]
                print('Processing CN spectrum: ', name)
                self.printFilesForName(name,'CN')
                return SFGspectrum(self.path,stretch,name,self.cnFiles[name],self.cnFilesBG[name],self.cnFilesCalib[name],skip)
        elif stretch == "CH":
            if number >= len(self.chNames):
                print('Number greater than available CH spectra')
            else:
                name = self.chNames[number]
                print('Processing CH spectrum: ', name)
                self.printFilesForName(name,'CH')
                return SFGspectrum(self.path,stretch,name,self.chFiles[name],self.chFilesBG[name],self.chFilesCalib[name],skip)
        elif stretch == "CO":
            if number >= len(self.coNames):
                print('Number greater than available CO spectra')
            else:
                name = self.coNames[number]
                print('Processing CO spectrum: ', name)
                self.printFilesForName(name,'CO')
                return SFGspectrum(self.path,stretch,name,self.coFiles[name],self.coFilesBG[name],self.coFilesCalib[name],skip)
        else:
            print("No available stretch specified.")        
        
        
        
        
        
        

                
                      