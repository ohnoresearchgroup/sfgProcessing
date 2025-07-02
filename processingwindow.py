# -*- coding: utf-8 -*-
"""
Created on Tue Jul  1 16:10:05 2025

@author: peo0005
"""

import os
import tkinter as tk
from tkinter import filedialog, ttk, Toplevel, Label
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sfgSpectrumForGUI import SFGspectrumForGUI

class ProcessingWindow:
    def __init__(self, spectrum):
        
        ## ==== SETUP CODE ======
        
        #associate the spectrum with the window
        self.spectrum = spectrum
        
        #create the window and label
        self.window = tk.Toplevel()
        self.window.geometry("800x1600")
        Label(self.window, text=f"{self.spectrum.name}", font=("Arial", 14)).pack(pady=20)
        
        # Create a parent frame to hold 4 panels
        grid_frame = tk.Frame(self.window)
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
        

        #initialize variable holding canvases for figures
        self.canvas_calibplot = None
        self.canvas_allplot = None
        self.canvas_oneplot = None
        
        # ==== TOP LEFT: PLOT OF ALL SPECTRA ====
        
        def update_all_plot():
            #clear canvas if one already exists
            #should update to delete figure
            if self.canvas_allplot is not None:
                self.canvas_allplot.get_tk_widget().destroy()
                
            all_fig = self.spectrum.plot()
            
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

        
        tk.Label(entry_frame, text="Upper Limit:").grid(row=0, column=2, padx=2)
        x2_entry = tk.Entry(entry_frame, width=6)
        x2_entry.grid(row=0, column=3, padx=2)
        
        #set default values
        if self.spectrum.region == 'CH':
            x1_entry.insert(0, "2820")  # Default value for lower lim
            x2_entry.insert(0, "2860")  # Default value for upper lim
        elif self.spectrum.region == 'CN':
            x1_entry.insert(0,"2200")
            x2_entry.inser(0,"2300")
            
        
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
                
                fig_calib = self.spectrum.fit_calib((x1,x2))
                
                update_shift_entry(self.spectrum.shift)
                
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
        def apply_calibration():
            self.spectrum.apply_calib()
            update_all_plot()
            update_one_plot()
            return
        
        # Buttons for performing fit and applying the calibration
        button_frame = tk.Frame(top_right_inner)
        button_frame.pack(pady=5)       
        tk.Button(button_frame, text="Perform Fit", command=update_calib_plot).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Apply Calib", bg="yellow", command=apply_calibration).pack(side=tk.LEFT, padx=5)
        
        update_all_plot()
        #update_calib_plot()

        # === LOWER LEFT ====
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
            
            #if 
            if self.canvas_oneplot is not None:
                self.canvas_oneplot.get_tk_widget().destroy()
        
            # Embed the plot into the Tkinter window
            self.canvas_oneplot = FigureCanvasTkAgg(one_fig, master=lower_left_inner)
            self.canvas_oneplot.draw()
            self.canvas_oneplot.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        
        update_one_plot()
        
        
        # ==== LOWER RIGHT ====
        tk.Label(panels[1][1], text="Bottom-Right Panel").pack()