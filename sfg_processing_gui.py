import os
import tkinter as tk
from tkinter import filedialog, ttk, Toplevel, Label
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sfgSpectrumForGUI import SFGspectrumForGUI
from processingwindow import ProcessingWindow


# organize spectra into lists based on the region
def organize_files(folder_path):
    #get all files in folder
    all_files = os.listdir(folder_path)
    #find the subset of asc or csv files
    asc_files = [file for file in all_files if (file.endswith(".asc") or file.endswith(".csv"))]
    
    #find the subset that are CH
    ch_list = list(set([file.rsplit("_",2)[0] for file in asc_files if file.split("_")[-2] == 'CH']))
    ch_list.sort()
    
    #find the subset that are CN
    cn_list = list(set([file.rsplit("_",2)[0] for file in asc_files if file.split("_")[-2] == 'CN']))
    cn_list.sort()
    
    #find the subset that are CO
    co_list = list(set([file.rsplit("_",2)[0] for file in asc_files if file.split("_")[-2] == 'CO']))
    co_list.sort()
    
    return (ch_list, cn_list, co_list, asc_files)


class FolderOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Open Spectrum From Folder")
        self.root.geometry("550x300")

        # Select folder button
        self.select_button = tk.Button(root, text="Select Folder", command=self.select_folder)
        self.select_button.pack(pady=10)

        # Variables for dropdowns
        self.ch_var = tk.StringVar()
        self.cn_var = tk.StringVar()
        self.co_var = tk.StringVar()

        # CH row
        ch_frame = tk.Frame(root)
        ch_frame.pack(pady=5)
        tk.Label(ch_frame, text="CH:").pack(side=tk.LEFT)
        self.ch_menu = ttk.Combobox(ch_frame, textvariable=self.ch_var, state="readonly", width=30)
        self.ch_menu.pack(side=tk.LEFT, padx=5)
        tk.Button(ch_frame, text="Process", command=lambda: self.on_ch_button_click(self.ch_var.get())).pack(side=tk.LEFT)

        # CN row
        cn_frame = tk.Frame(root)
        cn_frame.pack(pady=5)
        tk.Label(cn_frame, text="CN:").pack(side=tk.LEFT)
        self.cn_menu = ttk.Combobox(cn_frame, textvariable=self.cn_var, state="readonly", width=30)
        self.cn_menu.pack(side=tk.LEFT, padx=5)
        tk.Button(cn_frame, text="Process", command=lambda: self.on_cn_button_click(self.cn_var.get())).pack(side=tk.LEFT)

        # CO row
        co_frame = tk.Frame(root)
        co_frame.pack(pady=5)
        tk.Label(co_frame, text="CO:").pack(side=tk.LEFT)
        self.co_menu = ttk.Combobox(co_frame, textvariable=self.co_var, state="readonly", width=30)
        self.co_menu.pack(side=tk.LEFT, padx=5)
        tk.Button(co_frame, text="Process", command=lambda: self.on_co_button_click(self.co_var.get())).pack(side=tk.LEFT)


    def select_folder(self):
        folder_path = filedialog.askdirectory()
        self.path = folder_path
        print(folder_path)
        if folder_path:
            data = organize_files(folder_path)
            self.ch_list = data[0]
            self.cn_list = data[1]
            self.co_list = data[2]
            self.asc_files = data[3]
            
            self.update_dropdowns()

    def update_dropdowns(self):
        self.ch_menu['values'] = self.ch_list
        self.cn_menu['values'] = self.cn_list
        self.co_menu['values'] = self.co_list
        
        self.set_combobox_width(self.ch_menu, self.ch_list)
        self.set_combobox_width(self.cn_menu, self.cn_list)
        self.set_combobox_width(self.co_menu, self.co_list)
        
    #open spectrum window
    def process_spectrum(self, title, name, region):
        #find list of all files with this name
        all_sample_files = [file for file in self.asc_files if name == file.split('_')[0]]
        
        #find the SFG, bg, and calib files associated with this name
        if region == "CH":
            sfg_files = [file for file in all_sample_files if ((file.split('_')[-2] == 'CH') and ('bg' not in file))]
            bg_files = [file for file in all_sample_files if ((file.split('_')[-2] == 'CH') and ('bg' in file))]
            calib_files = [file for file in all_sample_files if ('_pp_' in file) or ('_ps_' in file)]
        elif region == 'CN':
            sfg_files = [file for file in all_sample_files if ((file.split('_')[-2] == 'CN') and ('bg' not in file) and ('4450' not in file) and ('calib' not in file))]
            bg_files = [file for file in all_sample_files if ((file.split('_')[-2] == 'CN') and ('bg' in file))]
            calib_files = [file for file in all_sample_files if ((file.split('_')[-2] == 'CN') and (('4450' in file) or (('calib' in file) and ('bg' not in file))))]
        elif region == 'CO':
            sfg_files  = [file for file in all_sample_files if ((file.split('_')[-2] == 'CO') and ('bg' not in file) and ('4450' not in file) and ('calib' not in file))]
            bg_files = [file for file in all_sample_files if ((file.split('_')[-2] == 'CO') and ('bg' in file))]
            calib_files = [file for file in all_sample_files if ((file.split('_')[-2] == 'CO') and (('4450' in file) or (('calib' in file) and ('bg' not in file))))]
        
        spectrum = SFGspectrumForGUI(self.path,region,name,sfg_files,bg_files,calib_files)
        
        ProcessingWindow(spectrum)
        

    def set_combobox_width(self,combobox, items):
        if items:
            max_len = max(len(str(item)) for item in items)
            combobox.config(width=max_len + 10)  # add a bit of padding
            combobox['values'] = items

    # process the spectrum that is selected in the dropdown menu
    def on_ch_button_click(self,name):
        self.process_spectrum("Processing CH Spectrum", name,'CH')

    def on_cn_button_click(self,name):
        self.process_spectrum("Processing CN Spectrum", name, 'CN')

    def on_co_button_click(self,name):
        self.process_spectrum("Processing CO Spectrum", name, "CO")



if __name__ == "__main__":
    root = tk.Tk()
    app = FolderOrganizerApp(root)
    root.mainloop()
