# -*- coding: utf-8 -*-
"""
Created on Tue Jul  1 16:10:05 2025

@author: peo0005
"""


import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


class ProcessingWindow:
    def __init__(self, spectrum,root):
        
        ## ==== SETUP CODE ======
        self.root = root
        
        #associate the spectrum with the window
        self.spectrum = spectrum
        
        #create the window and label
        self.window = tk.Toplevel()
        self.window.geometry("1200x800")
        tk.Label(self.window, text=f"{self.spectrum.name}", font=("Arial", 10)).grid(row=0, column=0, pady=2)
        
        # Create a parent frame to hold 6 panels
        grid_frame = tk.Frame(self.window)
        grid_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        
        self.window.rowconfigure(1, weight=1)
        self.window.columnconfigure(0, weight=1)
        
        # Define 2x3 layout
        panels = [[tk.Frame(grid_frame, bd=2, relief=tk.GROOVE) for j in range(3)] for i in range(2)]
        for i in range(2):
            for j in range(3):
                panels[i][j].grid(row=i, column=j, sticky="nsew", padx=5, pady=5)
        # Make the grid cells expand equally
        for i in range(2):
            grid_frame.rowconfigure(i, weight=1, minsize = 100)
        for j in range(3):
            grid_frame.columnconfigure(j, weight=1, minsize = 100)
            
        #initialize variable holding canvases for figures
        self.canvas_calibplot = None
        self.canvas_allplot = None
        self.canvas_oneplot = None
        self.canvas_fitgaussianplot = None
        self.canvas_summaryplot = None
        
        #initialize variable holding the fit window
        self.fit_window = None
        self.fit_figure = None
        
        # ==== TOP LEFT: PLOT OF ALL SPECTRA ====
        
        def update_all_plot():                  
            if self.canvas_allplot is not None:
                #close canvas if one already exists
                self.canvas_allplot.get_tk_widget().destroy()
                #close previous figure
                plt.close(self.canvas_allplot.figure)
                
            all_fig = self.spectrum.plot()
            
            # Embed the plot into the Tkinter window
            self.canvas_allplot = FigureCanvasTkAgg(all_fig, master=panels[0][0])
            self.canvas_allplot.draw()
            self.canvas_allplot.get_tk_widget().pack()
            
        update_all_plot()
        
        
        # ==== TOP MIDDLE: CALIBRATION ====
        
        # Create subframe for layout within top-right panel
        top_right_inner = tk.Frame(panels[0][1])
        top_right_inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Entry fields for numeric input
        entry_frame = tk.Frame(top_right_inner)
        entry_frame.pack(pady=2)
        
        tk.Label(entry_frame, text="Low Lim:").grid(row=0, column=0, padx=2)
        x1_entry = tk.Entry(entry_frame, width=6)
        x1_entry.grid(row=0, column=1, padx=2)
    
        tk.Label(entry_frame, text="Up Lim:").grid(row=0, column=2, padx=2)
        x2_entry = tk.Entry(entry_frame, width=6)
        x2_entry.grid(row=0, column=3, padx=2)
        
        #read-only entry to display calibration offset
        tk.Label(entry_frame, text="Offset:").grid(row=0, column=4, padx=2)
        shift_entry = tk.Entry(entry_frame, width=8, state="readonly")
        shift_entry.grid(row=0, column = 5, padx=2)
        shift_entry.insert(0, "0")
        
        #set default values
        if self.spectrum.region == 'CH':
            x1_entry.insert(0, "2820")  # Default value for lower lim
            x2_entry.insert(0, "2860")  # Default value for upper lim
        elif self.spectrum.region == 'CN':
            x1_entry.insert(0,"2200")
            x2_entry.insert(0,"2300")          
        

        
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
                
                fig_calib = self.spectrum.fit_calib((x1,x2))
                
                update_shift_entry(self.spectrum.shift)
                
                #if previous version exists
                if self.canvas_calibplot is not None:
                    #close canvas
                    self.canvas_calibplot.get_tk_widget().destroy()
                    #close old version of figure
                    plt.close(self.canvas_calibplot.figure)
                           
                #create calib plot
                self.canvas_calibplot = FigureCanvasTkAgg(fig_calib, master=top_right_inner)
                self.canvas_calibplot.draw()
                self.canvas_calibplot.get_tk_widget().pack()
                
            except ValueError:
                print("Invalid input — please enter numeric values.")
                return

        
        
        #apply calibration
        def apply_calibration():
            self.spectrum.apply_calib()
            update_all_plot()
            update_one_plot()
            update_fitguassian_plots()
            return
        
        # Buttons for performing fit and applying the calibration
        button_frame = tk.Frame(top_right_inner)
        button_frame.pack(pady=5)       
        tk.Button(button_frame, text="Update Fit", command=update_calib_plot).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Apply Calib", bg="yellow", command=apply_calibration).pack(side=tk.LEFT, padx=5)
 
        
        update_calib_plot()

        # ============ LOWER LEFT =========================
        def on_int_dropdown(event):
            update_one_plot()
        
        lower_left_inner = tk.Frame(panels[1][0])
        lower_left_inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        #lower_left_inner.rowconfigure(1, weight=1)
        #lower_left_inner.columnconfigure(0, weight=1)
        
        # Entry fields for numeric input
        ll_entry_frame = tk.Frame(lower_left_inner)
        ll_entry_frame.pack(pady=5)
        
        # List of integers to choose from
        integer_options = list(range(0, self.spectrum.num_scans))  # 0 through number of scans
        int_dropdown_var = tk.StringVar(value=str(integer_options[0]))  # default is first

        # Create read-only dropdown menu
        int_dropdown = ttk.Combobox(ll_entry_frame,textvariable=int_dropdown_var,values=[str(i) for i in integer_options],
            state='readonly',width=10,justify='center')
        int_dropdown.grid(row=0, column=0, padx=2)
        #bind function of new plot
        int_dropdown.bind("<<ComboboxSelected>>",on_int_dropdown)
        
        tk.Label(ll_entry_frame, text="Lower Limit:").grid(row=0, column=1, padx=2)
        one_x1_entry = tk.Entry(ll_entry_frame, width=6)
        one_x1_entry.grid(row=0, column=2, padx=2)
     
        tk.Label(ll_entry_frame, text="Upper Limit:").grid(row=0, column=3, padx=2)
        one_x2_entry = tk.Entry(ll_entry_frame, width=6)
        one_x2_entry.grid(row=0, column=4, padx=2)
     
        #default plot limits for one plot
        if self.spectrum.region == 'CH':
            one_x1_entry.insert(0, "2700")  # Default value for lower x
            one_x2_entry.insert(0, "3100")  # Default value for upper x
        if self.spectrum.region =='CN':
            one_x1_entry.insert(0, "2000")  # Default value for lower x
            one_x2_entry.insert(0, "2300")  # Default value for upper x
            
        def update_one_plot():
            scan = int(int_dropdown_var.get())
            x1 = float(one_x1_entry.get())
            x2 = float(one_x2_entry.get())
            
            one_fig = self.spectrum.plotScan(scan,xlim = [x1,x2])
            
            #if previous version exists
            if self.canvas_oneplot is not None:
                #close canvas
                self.canvas_oneplot.get_tk_widget().destroy()
                #close old version of figure
                plt.close(self.canvas_oneplot.figure)
        
            # Embed the plot into the Tkinter window
            self.canvas_oneplot = FigureCanvasTkAgg(one_fig, master=lower_left_inner)
            self.canvas_oneplot.draw()
            self.canvas_oneplot.get_tk_widget().pack()

        
        update_one_plot()
        
        # ====== UPPER AND LOWER RIGHT ======
        def update_fitguassian_plots():
            
            #clear canvas if one already exists
            if self.canvas_fitgaussianplot is not None:
                #close canvases
                self.canvas_fitgaussianplot.get_tk_widget().destroy()
                self.canvas_summaryplot.get_tk_widget().destroy()
                
                #close old versions of figures
                plt.close(self.canvas_fitgaussianplot.figure)
                plt.close(self.canvas_summaryplot.figure)
                
            (fig_fg,fig_sum) = self.spectrum.fitgaussians()
            
            # Embed the plot into the Tkinter window
            self.canvas_fitgaussianplot = FigureCanvasTkAgg(fig_fg, master=panels[0][2])
            self.canvas_fitgaussianplot.draw()
            self.canvas_fitgaussianplot.get_tk_widget().pack()
            
            # Embed the plot into the Tkinter window
            self.canvas_summaryplot = FigureCanvasTkAgg(fig_sum, master=panels[1][2])
            self.canvas_summaryplot.draw()
            self.canvas_summaryplot.get_tk_widget().pack()
        
        
        update_fitguassian_plots()
        
        
        # ========= LOWER MIDDLE ====================
        lower_middle_inner = tk.Frame(panels[1][1])
        lower_middle_inner.pack(padx=10, pady=10)

        #dropdown to select spectrum
        fit_dropdown_label = tk.Label(lower_middle_inner, text="Spectrum #:")
        fit_dropdown_label.grid(row=0, column=0, padx=2, pady=2, sticky="w")
        fit_dropdown_var = tk.StringVar(value=0)
        fit_dropdown = tk.OptionMenu(lower_middle_inner, fit_dropdown_var, *range(0, self.spectrum.num_scans))
        fit_dropdown.grid(row=0, column=1, padx=2, pady=2, sticky="w")
        
        #dropdown for oscillator number in fit
        oscnum_dropdown_var = tk.StringVar(value=1)
        oscnum_dropdown = tk.OptionMenu(lower_middle_inner, oscnum_dropdown_var, *range(1,3))
        oscnum_dropdown.grid(row=7, column=0, padx=2, pady=2, sticky="w")

        # --- Extra Parameters (left column) ---
        tk.Label(lower_middle_inner, text="Plot Lim").grid(row=1, column=0, padx=2, pady=(5, 2), sticky="w")
        plotlim_entry1 = tk.Entry(lower_middle_inner, width=8)
        plotlim_entry1.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        plotlim_entry2 = tk.Entry(lower_middle_inner, width=8)
        plotlim_entry2.grid(row=3, column=0, sticky="w", padx=5, pady=2)

        tk.Label(lower_middle_inner, text="Fit Lim:").grid(row=4, column=0, padx=2, pady=(5, 2), sticky="w")
        fitlim_entry1 = tk.Entry(lower_middle_inner, width=8)
        fitlim_entry1.grid(row=5, column=0, sticky="w", padx=5, pady=2)
        fitlim_entry2 = tk.Entry(lower_middle_inner, width=8)
        fitlim_entry2.grid(row=6, column=0, sticky="w", padx=5, pady=2)
        
        #default plot limits for fit plot
        if self.spectrum.region == 'CH':
            plotlim_entry1.insert(0, "2700")  # Default value for lower x
            plotlim_entry2.insert(0, "3100")  # Default value for upper x
        if self.spectrum.region =='CN':
            plotlim_entry1.insert(0, "2000")  # Default value for lower x
            plotlim_entry2.insert(0, "2300")  # Default value for upper x
   
        #default plot limits for fit plot
        if self.spectrum.region == 'CH':
            fitlim_entry1.insert(0, "2800")  # Default value for lower x
            fitlim_entry2.insert(0, "2860")  # Default value for upper x
        if self.spectrum.region =='CN':
            fitlim_entry1.insert(0, "2150")  # Default value for lower x
            fitlim_entry2.insert(0, "2200")  # Default value for upper x

        # --- Submit Button (also in left column) ---
        def perform_fit():
            scan_num_fit = int(fit_dropdown_var.get())
            
            plotlims = [float(plotlim_entry1.get()), float(plotlim_entry2.get())]
            fitrange = [float(fitlim_entry1.get()),float(fitlim_entry2.get())]
            gold_params = [[float(x.strip()) for x in entries[0].get().strip("[]").split(",")],
                           [float(x.strip()) for x in entries[1].get().strip("[]").split(",")],
                           [float(x.strip()) for x in entries[2].get().strip("[]").split(",")]]
            
            num_oscs = int(oscnum_dropdown_var.get())
            
            osc_params = []
            for i in range(num_oscs):
                one_osc_params = [[float(x.strip()) for x in entries[4*i+3].get().strip("[]").split(",")],
                                  [float(x.strip()) for x in entries[4*i+4].get().strip("[]").split(",")],
                                  [float(x.strip()) for x in entries[4*i+5].get().strip("[]").split(",")],
                                  [float(x.strip()) for x in entries[4*i+6].get().strip("[]").split(",")]]
                osc_params.append(one_osc_params)
            
            #do the actual fit
            self.current_fit = self.spectrum.fitLorentzians(scan_num_fit,
                                                            gold_params,
                                                            osc_params,
                                                            scaling=None,
                                                            xlim=plotlims,
                                                            fitrange=fitrange)
            
            
            #close window if it already exists
            if self.fit_figure is not None:
                plt.close(self.fit_figure)
                self.fit_window.destroy()
                
            
            #get figure from fit
            self.fit_figure = self.current_fit[0]      
            #make new window for fit
            self.fit_window = tk.Toplevel(self.window)
            
            self.canvas_figfit = FigureCanvasTkAgg(self.fit_figure, master=self.fit_window)
            self.canvas_figfit.draw()
            self.canvas_figfit.get_tk_widget().pack()
            
            #get the parameters and errors
            fitparams = self.current_fit[1]
            fitparams_error = self.current_fit[2]
            
            #update output entries
            for i in range(len(fitparams)):
                readonly_entries[i].config(state='normal')
                readonly_entries[i].delete(0, tk.END)
                readonly_entries[i].insert(0, round(fitparams[i],2))
                readonly_entries[i].config(state='readonly')           
            if len(fitparams) < 11:
                for i in range(11-len(fitparams)):
                    readonly_entries[i+len(fitparams)].config(state='normal')
                    readonly_entries[i+len(fitparams)].delete(0, tk.END)
                    readonly_entries[i+len(fitparams)].insert(0, "")
                    readonly_entries[i+len(fitparams)].config(state='readonly')
            
            #round the params and error
            fitparams_rd = np.round(fitparams,3)
            fitparams_error_rd = np.round(fitparams_error,3)
            
            #alternate params and error for output
            self.interleaved = np.empty(fitparams_rd.size + fitparams_error_rd.size,
                                        dtype=fitparams_rd.dtype)
            self.interleaved[0::2] = fitparams_rd   # Fill even indices with params
            self.interleaved[1::2] = fitparams_error_rd  # Fill odd indices with error
            #turn from numpy array to string list
            self.interleaved = [str(x) for x in self.interleaved]
            #pad with empty strings if only one osc
            if len(self.interleaved) < 22:
                self.interleaved = self.interleaved + [""] * max(0, 22 - len(self.interleaved))
            self.interleaved.insert(0,str(scan_num_fit))
            self.interleaved.insert(0,self.spectrum.name)
            #header
            self.output_header = ['Sample Name','Scan Num',
                                  'Gold Amp', 'Gold Amp Error',
                                  'Gold Center', 'Gold Center Error',
                                  'Gold Width', 'Gold Width Error',
                                  'Osc1 Amp', 'Osc1 Amp Error',
                                  'Osc1 Center', 'Osc1 Center Error',
                                  'Osc1 Gamma', 'Osc1 Gamma Error',
                                  'Osc1 Width', 'Osc1 Width Error',
                                  'Osc2 Amp', 'Osc2 Amp Error',
                                  'Osc2 Center',  'Osc2 Center Error',
                                  'Osc2 Gamma', 'Osc2 Gamma Error',
                                  'Osc2 Width','Osc2 Width Error']
                    
        #function to copy the fit to the clipboard    
        def output_fit():
            csv_string = "\t".join(self.interleaved)
            root.clipboard_clear()            # Clear the clipboard
            root.clipboard_append(csv_string)  # Append the variable value
            root.update()  # Keeps clipboard data after the window is closed (on Windows)              
            print('fit copied to clipboard.')
            
        #function to copy the header to the clipboard
        def copy_hdr():
            #copy output header
            csv_string = "\t".join(self.output_header)
            root.clipboard_clear()            # Clear the clipboard
            root.clipboard_append(csv_string)  # Append the variable value
            root.update()  # Keeps clipboard data after the window is closed (on Windows)
            print('header copied to clipboard.')
             

        fit_btn = tk.Button(lower_middle_inner, bg="yellow", text="Fit", command=perform_fit)
        fit_btn.grid(row=8, column=0, pady=(5, 5), padx=2, sticky="w")
        
        output_hdr_btn = tk.Button(lower_middle_inner, text="Copy Hdr", command=copy_hdr)
        output_hdr_btn.grid(row=9, column=0, pady=(5, 5), padx=2, sticky="w")
        
        output_btn = tk.Button(lower_middle_inner, text="Copy Fit", command=output_fit)
        output_btn.grid(row=10, column=0, pady=(5, 5), padx=2, sticky="w")

        # --- Column Header Labels ---
        tk.Label(lower_middle_inner, text="[Lower, Guess, Upper]", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, pady=5)
        tk.Label(lower_middle_inner, text="Output", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=5, pady=5)

        # --- Entry Fields with Row Labels ---
        row_labels = ['Gold Amp', 'Gold Center', 'Gold Width',
                      'Osc1 Amp', 'Osc1 Center', 'Osc1 Gamma', 'Osc1 Width',
                      'Osc2 Amp', 'Osc2 Center', 'Osc2 Gamma', 'Osc2 Width']
        
        if self.spectrum.region == 'CH':
            defaults = ["[0, 1, 2]", "[2820, 2880, 2950]", "[10, 100, 1000]",
                        "[0.01, 1.5, 50]", "[2820, 2880, 2950]", "[1, 10, 30]", "[0, 3.1415, 6.2830]",
                        "[0.01, 1.5, 50]", "[2820, 2880, 2950]", "[1, 10, 30]", "[0, 3.1415, 6.2830]"]
        elif self.spectrum.region == 'CN':
            defaults = ["[0, 1, 2]", "[2000, 2100, 2300]", "[10, 100, 1000]",
                        "[0.01, 1.5, 50]", "[2000, 2100, 2300]", "[1, 10, 30]", "[0, 3.1415, 6.2830]",
                        "[0.01, 1.5, 50]", "[2000, 2100, 2300]", "[1, 10, 30]", "[0, 3.1415, 6.2830]"]            

        entries = []
        readonly_entries = []
        for i in range(11):
            # Row label
            tk.Label(lower_middle_inner, text=row_labels[i]).grid(row=i+1, column=1, padx=1, pady=1, sticky="e")

            # Editable entry
            entry = tk.Entry(lower_middle_inner, width=20)
            entry.grid(row=i+1, column=2, padx=1, pady=1)
            entry.insert(0, defaults[i])
            entries.append(entry)

            # Read-only entry
            ro_entry = tk.Entry(lower_middle_inner, width=8, state='readonly', justify='center')
            ro_entry.grid(row=i+1, column=3, padx=1, pady=1)
            ro_entry.insert(0, "")
            readonly_entries.append(ro_entry)        