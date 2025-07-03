# -*- coding: utf-8 -*-
"""
Created on Tue Jul  1 16:10:05 2025

@author: peo0005
"""


import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ProcessingWindow:
    def __init__(self, spectrum):
        
        ## ==== SETUP CODE ======
        
        #associate the spectrum with the window
        self.spectrum = spectrum
        
        #create the window and label
        self.window = tk.Toplevel()
        self.window.geometry("1200x800")
        tk.Label(self.window, text=f"{self.spectrum.name}", font=("Arial", 14)).grid(row=0, column=0, pady=10)
        
        # Create a parent frame to hold 6 panels
        grid_frame = tk.Frame(self.window)
        grid_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
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
            self.canvas_allplot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        update_all_plot()
        
        
        # ==== TOP MIDDLE: CALIBRATION ====
        
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
        
        #read-only entry to display calibration offset
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
                
                #if previous version exists
                if self.canvas_calibplot is not None:
                    #close canvas
                    self.canvas_calibplot.get_tk_widget().destroy()
                    #close old version of figure
                    plt.close(self.canvas_calibplot.figure)
                           
                #create calib plot
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
        int_dropdown = tk.ttk.Combobox(ll_entry_frame,textvariable=int_dropdown_var,values=[str(i) for i in integer_options],
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
            self.canvas_oneplot.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        
        update_one_plot()
        
        
        # # ==== LOWER MIDDLE ====
        # lower_middle_inner = tk.Frame(panels[1][1])
        # lower_middle_inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # lm_entry_frame = tk.Frame(lower_middle_inner)
        # lm_entry_frame.pack(pady=5)
        # tk.Label(lower_middle_inner, text="Bottom-Middle Panel").pack()
        
        
        
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
            self.canvas_fitgaussianplot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Embed the plot into the Tkinter window
            self.canvas_summaryplot = FigureCanvasTkAgg(fig_sum, master=panels[1][2])
            self.canvas_summaryplot.draw()
            self.canvas_summaryplot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        
        update_fitguassian_plots()