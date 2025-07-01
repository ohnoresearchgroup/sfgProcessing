import os
import tkinter as tk
from tkinter import filedialog, ttk, Toplevel, Label
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sfgSpectrumForGUI import SFGspectrumForGUI


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
            
        spectrum_processing_win = Toplevel()
        spectrum_processing_win.title(title)
        spectrum_processing_win.geometry("800x1600")
        Label(spectrum_processing_win, text=f"{title} selected: {name}", font=("Arial", 14)).pack(pady=20)
        
        # Create a parent frame to hold 4 panels
        grid_frame = tk.Frame(spectrum_processing_win)
        grid_frame.pack(fill=tk.BOTH, expand=True)

        # Define 2x2 layout
        panels = [[tk.Frame(grid_frame, bd=2, relief=tk.GROOVE) for j in range(2)] for i in range(2)]
        for i in range(2):
            for j in range(2):
                panels[i][j].grid(row=i, column=j, sticky="nsew", padx=5, pady=5)

        # Make the grid cells expand equally
        for i in range(2):
            grid_frame.rowconfigure(i, weight=1)
            grid_frame.columnconfigure(i, weight=1)
        
        #create the spectrum from this list
        spectrum = SFGspectrumForGUI(self.path,region,name,sfg_files,bg_files,calib_files)
        
        #initialize variable holding canvas
        self.canvas_calibplot = None
        self.canvas_allplot = None
        
        # ==== TOP LEFT: PLOT OF ALL SPECTRA ====
        
        def update_all_plot():        
            all_fig = spectrum.plot()
            
            #if 
            if self.canvas_allplot is not None:
                self.canvas_allplot.get_tk_widget().destroy()
        
            # Embed the plot into the Tkinter window
            self.canvas_allplot = FigureCanvasTkAgg(all_fig, master=panels[0][0])
            self.canvas_allplot.draw()
            self.canvas_allplot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        
        # ==== TOP RIGHT: CALIBRATION ====
        
        # Create subframe for layout within top-right panel
        top_right_inner = tk.Frame(panels[0][1])
        top_right_inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Entry fields for numeric input
        entry_frame = tk.Frame(top_right_inner)
        entry_frame.pack(pady=5)
        
        tk.Label(entry_frame, text="Lower Limit:").grid(row=0, column=0, padx=2)
        x1_entry = tk.Entry(entry_frame, width=6)
        x1_entry.grid(row=0, column=1, padx=2)
        x1_entry.insert(0, "2820")  # Default value for X Max
        
        tk.Label(entry_frame, text="Upper Limit:").grid(row=0, column=2, padx=2)
        x2_entry = tk.Entry(entry_frame, width=6)
        x2_entry.grid(row=0, column=3, padx=2)
        x2_entry.insert(0, "2875")  # Default value for X Max
        
        # Read-only Entry
        tk.Label(entry_frame, text="Shift:").grid(row=1, column=0, padx=2)
        shift_entry = tk.Entry(entry_frame, width=10, state="readonly")
        shift_entry.grid(row=1, column = 2, padx=2)
        shift_entry.insert(0, "0")
        
        def update_shift_entry(value):
            shift_entry.config(state="normal")     # Enable writing
            shift_entry.delete(0, tk.END)          # Clear current content
            shift_entry.insert(0, str(value))      # Insert new value
            shift_entry.config(state="readonly")   # Set back to read-only
            



        
        # Function to update the plot based on entry values
        def update_calib_plot():
            try:
                x1 = float(x1_entry.get())
                x2 = float(x2_entry.get())
                
                fig_calib = spectrum.fit_calib(region,(x1,x2))
                
                update_shift_entry(spectrum.shift)
                
                #if 
                if self.canvas_calibplot is not None:
                    self.canvas_calibplot.get_tk_widget().destroy()
                
                # Create second plot
                self.canvas_calibplot = FigureCanvasTkAgg(fig_calib, master=top_right_inner)
                self.canvas_calibplot.draw()
                self.canvas_calibplot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
            except ValueError:
                print("Invalid input — please enter numeric values.")
                return
        
        

            
        
        
        #apply calibration
        def apply_calibration(spectrum):
            spectrum.apply_calib()
            update_all_plot()
            return
        
        # Buttons
        button_frame = tk.Frame(top_right_inner)
        button_frame.pack(pady=5)
        
        tk.Button(button_frame, text="Update", command=update_calib_plot).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Apply", command=apply_calibration(spectrum)).pack(side=tk.LEFT, padx=5)
        
        update_all_plot()
        update_calib_plot()

        # ==== Other Panels ====
        tk.Label(panels[1][0], text="Bottom-Left Panel").pack()
        tk.Label(panels[1][1], text="Bottom-Right Panel").pack()
        
        
        

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
