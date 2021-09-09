# Millimanipulation Mark 3 driver script
# written by Jheng-Han Tsai, February 2021
#================================================================
import time
import threading

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

from ximc import StageControl

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from scipy import signal, stats, mean


import csv
import ctypes
import os
import sys
import cv2

import nidaqmx
from nidaqmx.constants import TerminalConfiguration, VoltageUnits


# ------ global variables ------
a = 54
b = -5.4
frameWidth = 640
frameHeight = 480
xm = [0]
ym = [0]
xc = [0]
yc = [0]
filFreq = 50
operation = False
cameraSelected = False
recordImage = False
ImagePath = ''
img = [[0]*frameWidth for _ in range(frameHeight)] # Use camera frame size to setup figure size
niport = 'Dev2/ai0'


# font size for title
LARGEFONT = ('Helvetica', 36)

class tkinterApp(tk.Tk):

    # __init__ function for class tkinterApp
    def __init__(self, *args, **kwargs):
        
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)
        
        # creating a container
        container = tk.Frame(self)
        container.pack(side = 'top', fill = 'both', expand = True)

        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)

        # initializing frames to an empty array
        self.frames = {}

        # iterating through a tuple consisting
        # of the different page layouts
        for F in (SetPositionPage, MillimanipulationPage,
                  RelaxationTestsPage, ConfigurationPage,
                  ForceCalibrationPage):

            frame = F(container, self)

            # initializing frame of that object from pages with for loop
            self.frames[F] = frame

            frame.grid(row = 0, column = 0, sticky ='nsew')

        self.show_frame(SetPositionPage)

    
    def show_frame(self, cont):
        # display the current frame passed as parameter
        frame = self.frames[cont]
        frame.tkraise()
        
    
    def pass_on_text(self, page):
        # function to pass variables among frames
        return self.frames[page].getEntry()



class SetPositionPage(tk.Frame):
    # first window frame setpositionpage
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        
        # label of frame layout 
        label = tk.Label(self, text ='Set Position', font = LARGEFONT,
                         width = 20, height = 1,
                         anchor = 'nw')
        label.grid(row = 0, column = 0, columnspan = 3,
                   padx = 10, pady = 5)

        buttonExit = ttk.Button(self, text="Exit Window",
                                command = controller.destroy)
        buttonExit.grid(row = 0, column = 4, padx = 10, pady = 5)
        
        # buttons to go different pages
        button1 = ttk.Button(self, text ='Set Position',
                             width = 20)
        button1.grid(row = 1, column = 0, padx = 10, pady = 5)

        button2 = ttk.Button(self, text ='Millimanipulation',
        command = lambda : controller.show_frame(MillimanipulationPage), 
                             width = 20)
        button2.grid(row = 1, column = 1, padx = 10, pady = 5)
    
        button3 = ttk.Button(self, text ='Relaxation Tests',
        command = lambda : controller.show_frame(RelaxationTestsPage),
                             width = 20)
        button3.grid(row = 1, column = 2, padx = 10, pady = 5)
    
        button4 = ttk.Button(self, text ='Configuration',
        command = lambda : controller.show_frame(ConfigurationPage),
                             width = 20)
        button4.grid(row = 1, column = 3, padx = 10, pady = 5)
    
        button5 = ttk.Button(self, text ='Force Calibration',
        command = lambda : controller.show_frame(ForceCalibrationPage),
                             width = 20)
        button5.grid(row = 1, column = 4, padx = 10, pady = 5)

        # separation line
        separator1 = ttk.Separator(self, orient = 'horizontal')
        separator1.grid(row = 2, column = 0, pady = 10,
                        columnspan = 6, sticky = 'we')



        # labelframe of x-axis movement
        labelframeX = tk.LabelFrame(self,
                                    text = 'X-axis: Translational Movement')
        labelframeX.grid(row = 3, column = 1, columnspan = 3,
                         padx = 10, pady = 10, sticky = 'w')

        lfX_labelframe1 = tk.LabelFrame(labelframeX,
                                    text = 'Distance direction')
        lfX_labelframe1.grid(row = 0, column = 0, columnspan = 2,
                         padx = 10, pady = 10, sticky = 'w')

        lfX_lf1_label1 = tk.Label(lfX_labelframe1,
                               text = '"+" moves forward')
        lfX_lf1_label1.grid(row = 0, column = 0, padx = 10, sticky = 'w')

        lfX_lf1_label2 = tk.Label(lfX_labelframe1,
                               text = '"-" moves backward')
        lfX_lf1_label2.grid(row = 1, column = 0, padx = 10, sticky = 'w')

        lfX_label1 = ttk.Label(labelframeX,
                               text = 'Distance to move (mm):', width = 20)
        lfX_label1.grid(row = 1, column = 0, padx = 10, pady = 10,
                        sticky = 'w')

        
        self.entry1_var = tk.StringVar(value = '0')
        self.entry1 = ttk.Entry(labelframeX, textvariable = self.entry1_var)
        self.entry1.grid(row = 1, column = 1, padx = 10, pady = 10, sticky = 'w')

        lfX_label2 = ttk.Label(labelframeX,
                               text = 'Range: 100 mm', width = 20)
        lfX_label2.grid(row = 1, column = 2, padx = 10, pady = 10,
                        sticky = 'w')

        lfX_label3 = ttk.Label(labelframeX,
                               text = 'Current position (mm): ', width = 20)
        lfX_label3.grid(row = 0, column = 1, padx = 10, pady = 10,
                        sticky = 'e')

        # get current positions of X and Z and show on panel
        self.stcon = StageControl()
        positionX, positionZ = self.stcon.posXYVals_cal()
        
        self.positionX = tk.StringVar()
        self.positionX.set(positionX)
        self.positionZ = tk.StringVar()
        self.positionZ.set(positionZ)
        
        lfX_label4 = tk.Label(labelframeX, textvariable = self.positionX, width = 20,
                              height = 2, borderwidth = 2, relief = 'ridge')
        lfX_label4.grid(row = 0, column = 2, padx = 10, pady = 10,
                        sticky = 'w')

        lfX_label3 = ttk.Label(labelframeX,
                               text = 'Speed (mm/s):', width = 20)
        lfX_label3.grid(row = 2, column = 0, padx = 10, pady = 10,
                        sticky = 'w')

        
        self.entry2_var = tk.StringVar(value = '10')
        self.entry2 = ttk.Entry(labelframeX, textvariable = self.entry2_var)
        self.entry2.grid(row = 2, column = 1, padx = 10, pady = 10, sticky = 'w')

        lfX_label4 = ttk.Label(labelframeX,
                               text = 'Max: 20 mm/s', width = 20)
        lfX_label4.grid(row = 2, column = 2, padx = 10, pady = 10,
                        sticky = 'w')

        # buttons to run x-axis positioner
        button11 = ttk.Button(labelframeX, text ='Start (Translational)',
                              command = lambda : threading.Thread(target = Mark3.XmoveRight).start())
        button11.grid(row = 3, column = 0, padx = 10, pady = 10)

        button12 = ttk.Button(labelframeX, text ='Soft stop',
                              command = lambda : threading.Thread(target = self.stcon.softStopX).start())
        button12.grid(row = 3, column = 1, padx = 10, pady = 10)

        button13 = ttk.Button(labelframeX, text ='Set to zero',
                              command = lambda : threading.Thread(target = self.stcon.setZeroPositionX).start())
        button13.grid(row = 3, column = 2, padx = 10, pady = 10)

        button14 = ttk.Button(labelframeX, text ='Back to zero',
                              command = lambda : threading.Thread(target = self.stcon.moveToZeroX).start())
        button14.grid(row = 4, column = 0, padx = 10, pady = 10)

        button15 = ttk.Button(labelframeX, text ='Go home',
                              command = lambda : threading.Thread(target = self.stcon.moveContinuousLeft).start())
        button15.grid(row = 4, column = 1, padx = 10, pady = 10)

        
        # labelframe of z-axis movement
        labelframeZ = tk.LabelFrame(self,
                                    text = 'Z-axis: Vertical Movement')
        labelframeZ.grid(row = 4, column = 1, columnspan = 3,
                         padx = 10, pady = 10, sticky = 'w')

        lfZ_labelframe1 = tk.LabelFrame(labelframeZ,
                                    text = 'Distance direction')
        lfZ_labelframe1.grid(row = 0, column = 0, columnspan = 2,
                         padx = 10, pady = 10, sticky = 'w')

        lfZ_lf1_label1 = tk.Label(lfZ_labelframe1,
                               text = '"+" moves upwards')
        lfZ_lf1_label1.grid(row = 0, column = 0, padx = 10, sticky = 'w')

        lfZ_lf1_label2 = tk.Label(lfZ_labelframe1,
                               text = '"-" moves downwards')
        lfZ_lf1_label2.grid(row = 1, column = 0, padx = 10, sticky = 'w')

        lfZ_label3 = ttk.Label(labelframeZ,
                               text = 'Current position (mm): ', width = 20)
        lfZ_label3.grid(row = 0, column = 1, padx = 10, pady = 10,
                        sticky = 'e')

        lfZ_label4 = tk.Label(labelframeZ, textvariable = self.positionZ, width = 20,
                              height = 2, borderwidth = 2, relief = 'ridge')
        lfZ_label4.grid(row = 0, column = 2, padx = 10, pady = 10,
                        sticky = 'w')

        lfZ_label1 = ttk.Label(labelframeZ,
                               text = 'Distance to move (mm):', width = 20)
        lfZ_label1.grid(row = 1, column = 0, padx = 10, pady = 10,
                        sticky = 'w')


        self.entry3_var = tk.StringVar(value = '0')
        self.entry3 = ttk.Entry(labelframeZ, textvariable = self.entry3_var)
        self.entry3.grid(row = 1, column = 1, padx = 10, pady = 10, sticky = 'w')

        lfZ_label2 = ttk.Label(labelframeZ,
                               text = 'Range: 13 mm', width = 20)
        lfZ_label2.grid(row = 1, column = 2, padx = 10, pady = 10,
                        sticky = 'w')

        lfZ_label3 = ttk.Label(labelframeZ,
                               text = 'Speed (mm/s):', width = 20)
        lfZ_label3.grid(row = 2, column = 0, padx = 10, pady = 10,
                        sticky = 'w')


        self.entry4_var = tk.StringVar(value = '0.200')
        self.entry4 = ttk.Entry(labelframeZ, textvariable = self.entry4_var)
        self.entry4.grid(row = 2, column = 1, padx = 10, pady = 10, sticky = 'w')

        lfZ_label4 = ttk.Label(labelframeZ,
                               text = 'Max: 0.416 mm/s', width = 20)
        lfZ_label4.grid(row = 2, column = 2, padx = 10, pady = 10,
                        sticky = 'w')

        # buttons to run z-axis positioner
        button16 = ttk.Button(labelframeZ, text ='Start (Vertical)',
                              command = lambda : threading.Thread(target = Mark3.ZmoveUp).start())
        button16.grid(row = 3, column = 0, padx = 10, pady = 10)

        button17 = ttk.Button(labelframeZ, text ='Soft stop',
                              command = lambda : threading.Thread(target = self.stcon.softStopY).start())
        button17.grid(row = 3, column = 1, padx = 10, pady = 10)

        button18 = ttk.Button(labelframeZ, text ='Set to zero',
                              command = lambda : threading.Thread(target = self.stcon.setZeroPositionY).start())
        button18.grid(row = 3, column = 2, padx = 10, pady = 10)

        button19 = ttk.Button(labelframeZ, text ='Back to zero',
                              command = lambda : threading.Thread(target = self.stcon.moveToZeroY).start())
        button19.grid(row = 4, column = 0, padx = 10, pady = 10)

        button20 = ttk.Button(labelframeZ, text ='Go home',
                              command = lambda : threading.Thread(target = self.stcon.moveContinuousDown).start())
        button20.grid(row = 4, column = 1, padx = 10, pady = 10)
        
        
    def updatePosition(self):
        # update current positions of X and Z showed
        positionX, positionZ = self.stcon.posXYVals_cal()
        positionX, positionZ = '10', '20'
        self.positionX.set(positionX)
        self.positionZ.set(positionZ)

    def getEntry(self):
        # function to collect entry variables for sending to other classes
        distanceX = float(self.entry1.get())
        speedX = float(self.entry2.get())
        distanceZ = float(self.entry3.get())
        speedZ = float(self.entry4.get())
        
        return [distanceX, speedX, distanceZ, speedZ]
        


class MillimanipulationPage(tk.Frame):
    # second window frame millimanipulation
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        # label of frame layout 
        label = tk.Label(self, text ='Millimanipulation', font = LARGEFONT,
                         width = 20, height = 1, anchor = 'nw')
        label.grid(row = 0, column = 0, columnspan = 3,
                   padx = 10, pady = 5)

        buttonExit = ttk.Button(self, text="Exit Window",
                                command = controller.destroy)
        buttonExit.grid(row = 0, column = 4, padx = 10, pady = 5)
        
        # buttons to go to different pages
        button1 = ttk.Button(self, text ='Set Position',
        command = lambda : controller.show_frame(SetPositionPage), 
                             width = 20)
        button1.grid(row = 1, column = 0, padx = 10, pady = 5)

        button2 = ttk.Button(self, text ='Millimanipulation', width = 20)
        button2.grid(row = 1, column = 1, padx = 10, pady = 5)
    
        button3 = ttk.Button(self, text ='Relaxation Tests',
        command = lambda : controller.show_frame(RelaxationTestsPage),
                             width = 20)
        button3.grid(row = 1, column = 2, padx = 10, pady = 5)
    
        button4 = ttk.Button(self, text ='Configuration',
        command = lambda : controller.show_frame(ConfigurationPage),
                             width = 20)
        button4.grid(row = 1, column = 3, padx = 10, pady = 5)
    
        button5 = ttk.Button(self, text ='Force Calibration',
        command = lambda : controller.show_frame(ForceCalibrationPage),
                             width = 20)
        button5.grid(row = 1, column = 4, padx = 10, pady = 5)

        # separation line
        separator1 = ttk.Separator(self, orient = 'horizontal')
        separator1.grid(row = 2, column = 0, pady = 10,
                        columnspan = 6, sticky = 'we')


        # labelframe of x-axis movement
        labelframeX = tk.LabelFrame(self,
                                    text = 'X-axis: Translational Movement')
        labelframeX.grid(row = 3, column = 0, rowspan = 2, columnspan = 2,
                         padx = 10, pady = 10, sticky = 'nw')

        lfX_labelframe1 = tk.LabelFrame(labelframeX,
                                    text = 'Warning:')
        lfX_labelframe1.grid(row = 0, column = 0, columnspan = 2,
                         padx = 10, pady = 10, sticky = 'w')

        lfX_lf1_label2 = tk.Label(lfX_labelframe1,
                               text = 'Max moving range: 100 mm')
        lfX_lf1_label2.grid(row = 1, column = 0, padx = 5, sticky = 'w')

        lfX_lf1_label2 = tk.Label(lfX_labelframe1,
                               text = 'Max moving speed: 20 mm/s')
        lfX_lf1_label2.grid(row = 2, column = 0, padx = 5, sticky = 'w')

        lfX_label1 = ttk.Label(labelframeX,
                               text = 'Distance to move (mm):', width = 20)
        lfX_label1.grid(row = 1, column = 0, padx = 10, pady = 10,
                        sticky = 'w')


        self.entry1_var = tk.StringVar(value = '5')
        self.entry1 = ttk.Entry(labelframeX, textvariable = self.entry1_var)
        self.entry1.grid(row = 1, column = 1, padx = 10, pady = 10, sticky = 'w')

        lfX_label3 = ttk.Label(labelframeX,
                               text = 'Speed (mm/s):', width = 20)
        lfX_label3.grid(row = 2, column = 0, padx = 10, pady = 10,
                        sticky = 'w')


        self.entry2_var = tk.StringVar(value = '1')
        self.entry2 = ttk.Entry(labelframeX, textvariable = self.entry2_var)
        self.entry2.grid(row = 2, column = 1, padx = 10, pady = 10, sticky = 'w')

        
        def browseButton():
            # function to browse saving path
            fileSelected = filedialog.askdirectory()
            folderPath.set(fileSelected)

        button6 = ttk.Button(labelframeX, text = 'Browse saved path:',
        command = browseButton, width = 15)
        button6.grid(row = 3, column = 0, padx = 10, pady = 5)

        self.entry3_var = tk.StringVar(value = '')
        self.entry3 = ttk.Entry(labelframeX, textvariable = self.entry3_var, width = 20)
        self.entry3.grid(row = 3, column = 1, padx = 10, pady = 5, sticky = 'w')


        lfX_label4 = ttk.Label(labelframeX,
                               text = 'File name:', width = 20)
        lfX_label4.grid(row = 4, column = 0, padx = 10, pady = 10,
                        sticky = 'w')


        self.entry4_var = tk.StringVar(value = '')
        self.entry4 = ttk.Entry(labelframeX, textvariable = self.entry4_var)
        self.entry4.grid(row = 4, column = 1, padx = 10, pady = 10, sticky = 'w')


        self.entry5 = tk.IntVar(value = 0)
        checkButton1 = ttk.Checkbutton(labelframeX, text ='Record image',
                                  variable = self.entry5, onvalue = 1, offvalue = 0,
                                  command = lambda : self.checkImageRecordButton())
        checkButton1.grid(row = 5, column = 0, padx = 10, pady = 10, sticky = 'w')


        # buttons to run x-axis positioner
        self.stcon = StageControl()
        
        button11 = ttk.Button(labelframeX, text ='Start (Measurement)',
                             command = lambda : threading.Thread(target = Mark3().Millimanipulation).start())
        button11.grid(row = 6, column = 0, padx = 10, pady = 10)

        button12 = ttk.Button(labelframeX, text ='Soft stop',
                              command = lambda : threading.Thread(target = self.stcon.softStopY).start())
        button12.grid(row = 6, column = 1, padx = 10, pady = 10)
        
        button13 = ttk.Button(labelframeX, text ='Back to zero',
                              command = lambda : threading.Thread(target = self.stcon.moveToZeroX).start())
        button13.grid(row = 7, column = 1, padx = 10, pady = 10)


        # labelframe of figures
        self.labelframeFig = tk.LabelFrame(self, text = 'Results Taken from Camera and Force Transducer')
        self.labelframeFig.grid(row = 3, column = 2, rowspan = 5, columnspan = 3,
                         padx = 10, pady = 10, sticky = 'w')
        
        # add figure canvas to show results
        self.fig = plt.Figure(figsize = (6, 6))
        
        # create variable to control capture of video frames
        self.entry0 = tk.IntVar(value = 0)
        self.axImg = self.fig.add_subplot(211)

        global img
        self.im = self.axImg.imshow(img)
        self.axImg.axis('off')
        
        checkButton2 = ttk.Checkbutton(self.labelframeFig, text ='Connect to camera',
                                  variable = self.entry0, onvalue = 1, offvalue = 0,
                                  command = lambda : self.checkCameraButton())
        checkButton2.grid(row = 0, column = 0, padx = 0, pady = 0)


        self.axFig = self.fig.add_subplot(212) 
        self.canvas = FigureCanvasTkAgg(self.fig, self.labelframeFig)
        self.canvas.get_tk_widget().grid(row = 1, column = 0, rowspan = 3, columnspan = 3, 
                         padx = 10, pady = 10, sticky = 'w')

        self.canvas.draw()
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval = 100)

        # labelframe of z-axis movement
        labelframeZ = tk.LabelFrame(self,
                                    text = 'Z-axis: Vertical Movement')
        labelframeZ.grid(row = 5, column = 0, columnspan = 2,
                         padx = 10, pady = 10, sticky = 'nw')


        lfZ_label1 = ttk.Label(labelframeZ,
                               text = 'Back to zero position', width = 20)
        lfZ_label1.grid(row = 0, column = 0, padx = 10, pady = 10,
                        sticky = 'w')
        
        button14 = ttk.Button(labelframeZ, text ='Back to zero',
                              command = lambda : threading.Thread(target = self.stcon.moveToZeroY).start())
        button14.grid(row = 0, column = 1, padx = 10, pady = 10)


		
    def animate(self, i):
        # define function to show real time figure 
        global xm, ym, img

        self.axFig.clear()
        self.axFig.plot(xm, ym)
        self.axFig.set_xlabel('Time (s)')
        self.axFig.set_ylabel('Force (N)')
        
        if self.entry0.get() == 1:
            self.im.set_data(img)
    
    def getEntry(self):
        # define function to collect entry variables for sending to other classes
        distance = float(self.entry1.get())
        speed = float(self.entry2.get())
        folderPath = self.entry3.get()
        fileName = self.entry4.get()

        # create saving path
        if not fileName:
            path = folderPath+time.strftime('%Y%m%d%H%M')
        else:
            path = folderPath+fileName
        
        return [distance, speed, path]

    def checkImageRecordButton(self):
        global recordImage
        
        if self.entry0.get() == 1:
            recordImage = True if self.entry5.get() == 1 else False
        else:
            self.entry5.set(0)
                
    def checkCameraButton(self):
        global cameraSelected, recordImage
        
        if self.entry0.get() == 1:
            cameraSelected = True
            threading.Thread(target = Mark3().grabImage).start()
            app.frames[RelaxationTestsPage].entry0.set(1)
            
        else:
            cameraSelected = recordImage = False
            self.entry5.set(0)
            app.frames[RelaxationTestsPage].entry0.set(0)
            
            
class RelaxationTestsPage(tk.Frame):
    # third window frame relaxationtests
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        # label of frame layout 
        label = tk.Label(self, text ='Relaxation Tests', font = LARGEFONT,
                         width = 20, height = 1, anchor = 'nw')
        label.grid(row = 0, column = 0, columnspan = 3,
                   padx = 10, pady = 5)

        buttonExit = ttk.Button(self, text="Exit Window",
                                command = controller.destroy)
        buttonExit.grid(row = 0, column = 4, padx = 10, pady = 5)
        
        # buttons to go to different pages
        button1 = ttk.Button(self, text ='Set Position',
        command = lambda : controller.show_frame(SetPositionPage), 
                             width = 20)
        button1.grid(row = 1, column = 0, padx = 10, pady = 5)

        button2 = ttk.Button(self, text ='Millimanipulation',
        command = lambda : controller.show_frame(MillimanipulationPage), 
                             width = 20)
        button2.grid(row = 1, column = 1, padx = 10, pady = 5)
    
        button3 = ttk.Button(self, text ='Relaxation Tests', width = 20)
        button3.grid(row = 1, column = 2, padx = 10, pady = 5)
    
        button4 = ttk.Button(self, text ='Configuration',
        command = lambda : controller.show_frame(ConfigurationPage),
                             width = 20)
        button4.grid(row = 1, column = 3, padx = 10, pady = 5)
    
        button5 = ttk.Button(self, text ='Force Calibration',
        command = lambda : controller.show_frame(ForceCalibrationPage),
                             width = 20)
        button5.grid(row = 1, column = 4, padx = 10, pady = 5)

        # separation line
        separator1 = ttk.Separator(self, orient = 'horizontal')
        separator1.grid(row = 2, column = 0, pady = 10,
                        columnspan = 6, sticky = 'we')
        


        # labelframe of x-axis movement
        labelframeX = tk.LabelFrame(self,
                                    text = 'X-axis: Translational Movement')
        labelframeX.grid(row = 3, column = 0, rowspan = 2, columnspan = 2,
                         padx = 10, pady = 10, sticky = 'nw')

        lfX_labelframe1 = tk.LabelFrame(labelframeX,
                                    text = 'Warning:')
        lfX_labelframe1.grid(row = 0, column = 0, columnspan = 2,
                         padx = 10, pady = 10, sticky = 'w')

        lfX_lf1_label2 = tk.Label(lfX_labelframe1,
                               text = 'Max moving range: 100 mm')
        lfX_lf1_label2.grid(row = 1, column = 0, padx = 5, sticky = 'w')

        lfX_lf1_label2 = tk.Label(lfX_labelframe1,
                               text = 'Max moving speed: 20 mm/s')
        lfX_lf1_label2.grid(row = 2, column = 0, padx = 5, sticky = 'w')


        lfX_label1 = ttk.Label(labelframeX,
                               text = 'Scrape interval (mm):', width = 20)
        lfX_label1.grid(row = 1, column = 0, padx = 10, pady = 10,
                        sticky = 'w')

        self.entry1_var = tk.StringVar(value = '1')
        self.entry1 = ttk.Entry(labelframeX, textvariable = self.entry1_var)
        self.entry1.grid(row = 1, column = 1, padx = 10, pady = 10, sticky = 'w')


        lfX_label2 = ttk.Label(labelframeX,
                               text = 'Speed (mm/s):', width = 20)
        lfX_label2.grid(row = 2, column = 0, padx = 10, pady = 10,
                        sticky = 'w')

        self.entry2_var = tk.StringVar(value = '1')
        self.entry2 = ttk.Entry(labelframeX, textvariable = self.entry2_var)
        self.entry2.grid(row = 2, column = 1, padx = 10, pady = 10, sticky = 'w')


        lfX_label3 = ttk.Label(labelframeX,
                               text = 'No. of scrape interval:',
                               width = 20)
        lfX_label3.grid(row = 3, column = 0, padx = 10, pady = 10,
                        sticky = 'w')

        self.entry3_var = tk.StringVar(value = '5')
        self.entry3 = ttk.Entry(labelframeX, textvariable = self.entry3_var)
        self.entry3.grid(row = 3, column = 1, padx = 10, pady = 10, sticky = 'w')


        lfX_label4 = ttk.Label(labelframeX,
                               text = 'Relaxation time of each steps (s):',
                               width = 20)
        lfX_label4.grid(row = 4, column = 0, padx = 10, pady = 10,
                        sticky = 'w')

        self.entry4_var = tk.StringVar(value = '1')
        self.entry4 = ttk.Entry(labelframeX, textvariable = self.entry4_var)
        self.entry4.grid(row = 4, column = 1, padx = 10, pady = 10, sticky = 'w')
        
        def browseButton():
            # function to browse saving path
            fileSelected = filedialog.askdirectory()
            folderPath.set(fileSelected)

        button6 = ttk.Button(labelframeX, text = 'Browse saved path:',
        command = browseButton, width = 15)
        button6.grid(row = 5, column = 0, padx = 10, pady = 5)

        
        self.entry5_var = tk.StringVar(value = '')
        self.entry5 = ttk.Entry(labelframeX, textvariable = self.entry5_var, width = 20)
        self.entry5.grid(row = 5, column = 1, padx = 10, pady = 5, sticky = 'w')


        lfX_label5 = ttk.Label(labelframeX,
                               text = 'File name:', width = 20)
        lfX_label5.grid(row = 6, column = 0, padx = 10, pady = 10,
                        sticky = 'w')

        self.entry6_var = tk.StringVar(value = '')
        self.entry6 = ttk.Entry(labelframeX, textvariable = self.entry6_var)
        self.entry6.grid(row = 6, column = 1, padx = 10, pady = 10, sticky = 'w')

        self.entry7 = tk.IntVar(value = 0)
        checkButton1 = ttk.Checkbutton(labelframeX, text ='Record image',
                                  variable = self.entry7, onvalue = 1, offvalue = 0,
                                  command = lambda : self.checkImageRecordButton())
        checkButton1.grid(row = 7, column = 0, padx = 10, pady = 10, sticky = 'w')

        
        
        # buttons to run x-axis positioner
        self.stcon = StageControl()
        
        button11 = ttk.Button(labelframeX, text ='Start (Measurement)',
                             command = lambda : threading.Thread(target = Mark3().RelaxationTests).start())
        button11.grid(row = 8, column = 0, padx = 10, pady = 10)

        button12 = ttk.Button(labelframeX, text ='Soft stop',
                              command = lambda : threading.Thread(target = self.stcon.softStopX).start())
        button12.grid(row = 8, column = 1, padx = 10, pady = 10)

        button13 = ttk.Button(labelframeX, text ='Back to zero',
                            command = lambda : threading.Thread(target = self.stcon.moveToZeroX).start())
        button13.grid(row = 9, column = 1, padx = 10, pady = 10)

         
        # labelframe of real time figure
        self.labelframeFig = tk.LabelFrame(self,
                                    text = 'Results Taken from Camera and Force Transducer')
        self.labelframeFig.grid(row = 3, column = 2, rowspan = 5, columnspan = 3,
                         padx = 10, pady = 10, sticky = 'w')


        # add figure canvas to show results
        self.fig = plt.Figure(figsize = (6, 6))
        
        # create variable to control capture of video frames
        self.entry0 = tk.IntVar(value = 0)
        self.axImg = self.fig.add_subplot(211)

        global img
        self.im = self.axImg.imshow(img)
        self.axImg.axis('off')
        
        buttonc = ttk.Checkbutton(self.labelframeFig, text ='Connect to camera',
                                  variable = self.entry0, onvalue = 1, offvalue = 0,
                                  command = lambda : self.checkCameraButton())
        buttonc.grid(row = 0, column = 0, padx = 0, pady = 0)


        self.axFig = self.fig.add_subplot(212) 
        self.canvas = FigureCanvasTkAgg(self.fig, self.labelframeFig)
        self.canvas.get_tk_widget().grid(row = 1, column = 0, rowspan = 3, columnspan = 3, 
                         padx = 10, pady = 10, sticky = 'w')

        self.canvas.draw()
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval = 100)

        # labelframe of z-axis movement
        labelframeZ = tk.LabelFrame(self,
                                    text = 'Z-axis: Vertical Movement')
        labelframeZ.grid(row = 5, column = 0, columnspan = 2,
                         padx = 10, pady = 10, sticky = 'nw')


        lfZ_label1 = ttk.Label(labelframeZ,
                               text = 'Back to zero position', width = 20)
        lfZ_label1.grid(row = 0, column = 0, padx = 10, pady = 10,
                        sticky = 'w')
        
        button14 = ttk.Button(labelframeZ, text ='Back to zero',
                              command = lambda : threading.Thread(target = self.stcon.moveToZeroY).start())
        button14.grid(row = 0, column = 1, padx = 10, pady = 10)

    def animate(self, i):
        # define function to show real time figure 
        global xm, ym, img

        self.axFig.clear()
        self.axFig.plot(xm, ym)
        self.axFig.set_xlabel('Time (s)')
        self.axFig.set_ylabel('Force (N)')
        
        if self.entry0.get() == 1:
            self.im.set_data(img)

    
    def getEntry(self):
        # function to collect entry variables and send to other classes
        interval = float(self.entry1.get())
        speed = float(self.entry2.get())
        noScrape = int(self.entry3.get())
        relaxTime = float(self.entry4.get())
        folderPath = self.entry5.get()
        fileName = self.entry6.get()

        # create saving path
        if not fileName:
            path = folderPath+time.strftime('%Y%m%d%H%M')
        else:
            path = folderPath+fileName

        return [interval, speed, noScrape, relaxTime, path]

    def checkImageRecordButton(self):
        # define function to turn on recording images
        global recordImage
        
        if self.entry0.get() == 1:
            recordImage = True if self.entry7.get() == 1 else False
        else:
            self.entry7.set(0)
                
    def checkCameraButton(self):
        # define function to connect camera
        global cameraSelected, recordImage
        
        if self.entry0.get() == 1:
            cameraSelected = True
            threading.Thread(target = Mark3().grabImage).start()
            app.frames[MillimanipulationPage].entry0.set(1)
            
        else:
            cameraSelected = recordImage = False
            self.entry7.set(0)
            app.frames[MillimanipulationPage].entry0.set(0)


class ConfigurationPage(tk.Frame):
    # fourth window frame configuration
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        # label of frame layout 
        label = tk.Label(self, text ='Configuration', font = LARGEFONT,
                         width = 20, height = 1, anchor = 'nw')
        label.grid(row = 0, column = 0, columnspan = 3,
                   padx = 10, pady = 5)

        buttonExit = ttk.Button(self, text="Exit Window",
                                command = controller.destroy)
        buttonExit.grid(row = 0, column = 4, padx = 10, pady = 5)
        
        # buttons to go to different pages
        button1 = ttk.Button(self, text ='Set Position',
        command = lambda : controller.show_frame(SetPositionPage), 
                             width = 20)
        button1.grid(row = 1, column = 0, padx = 10, pady = 5)

        button2 = ttk.Button(self, text ='Millimanipulation',
        command = lambda : controller.show_frame(MillimanipulationPage), 
                             width = 20)
        button2.grid(row = 1, column = 1, padx = 10, pady = 5)
    
        button3 = ttk.Button(self, text ='Relaxation Tests',
        command = lambda : controller.show_frame(RelaxationTestsPage),
                             width = 20)
        button3.grid(row = 1, column = 2, padx = 10, pady = 5)
    
        button4 = ttk.Button(self, text ='Configuration',
                             width = 20)
        button4.grid(row = 1, column = 3, padx = 10, pady = 5)
    
        button5 = ttk.Button(self, text ='Force Calibration',
        command = lambda : controller.show_frame(ForceCalibrationPage),
                             width = 20)
        button5.grid(row = 1, column = 4, padx = 10, pady = 5)

        # separation line
        separator1 = ttk.Separator(self, orient = 'horizontal')
        separator1.grid(row = 2, column = 0, pady = 10,
                        columnspan = 6, sticky = 'we')

        
        # labelframe of configuration parameters
        labelFrame1 = tk.LabelFrame(self,
                                    text = 'Configuration parameters')
        labelFrame1.grid(row = 3, column = 1, columnspan = 3,
                         padx = 10, pady = 10, sticky = 'w')

        label1 = ttk.Label(labelFrame1,
                               text = 'Force calibration: y = ax + b (y: force(N); x: voltage(V)) - ')
        label1.grid(row = 0, column = 0, columnspan = 3, padx = 10, pady = 10,
                        sticky = 'w')

        global a, b
        label2 = ttk.Label(labelFrame1, text = 'a:', width = 20)
        label2.grid(row = 1, column = 0, padx = 10, pady = 0,
                        sticky = 'w')

        self.entry1_var = tk.StringVar(value = a)
        self.entry1 = ttk.Entry(labelFrame1, textvariable = self.entry1_var)
        self.entry1.grid(row = 1, column = 1, padx = 10, pady = 0, sticky = 'w')

        label3 = ttk.Label(labelFrame1, text = 'b:', width = 20)
        label3.grid(row = 2, column = 0, padx = 10, pady = 0,
                        sticky = 'w')

        self.entry2_var = tk.StringVar(value = b)
        self.entry2 = ttk.Entry(labelFrame1, textvariable = self.entry2_var)
        self.entry2.grid(row = 2, column = 1, padx = 10, pady = 0, sticky = 'w')


        label4 = ttk.Label(labelFrame1,
                               text = 'Camera frame size - ')
        label4.grid(row = 3, column = 0, columnspan = 3, padx = 10, pady = 10,
                        sticky = 'w')

        global frameWidth, frameHeight
        label5 = ttk.Label(labelFrame1, text = 'Frame width (pixel):', width = 20)
        label5.grid(row = 4, column = 0, padx = 10, pady = 0,
                        sticky = 'w')

        self.entry3_var = tk.StringVar(value = frameWidth)
        self.entry3 = ttk.Entry(labelFrame1, textvariable = self.entry3_var)
        self.entry3.grid(row = 4, column = 1, padx = 10, pady = 0, sticky = 'w')

        label3 = ttk.Label(labelFrame1, text = 'Frame height (pixel)', width = 20)
        label3.grid(row = 5, column = 0, padx = 10, pady = 0,
                        sticky = 'w')

        self.entry4_var = tk.StringVar(value = frameHeight)
        self.entry4 = ttk.Entry(labelFrame1, textvariable = self.entry4_var)
        self.entry4.grid(row = 5, column = 1, padx = 10, pady = 0, sticky = 'w')


        button1 = ttk.Button(labelFrame1, text ='Set and save parameters',
                              command = lambda : self.saveConfiguration())
        button1.grid(row = 6, column = 1, padx = 10, pady = 10)

        

    def saveConfiguration(self):
        # define function to save and set configuration parameters
        
        # collect parameters
        global a, b, frameWidth, frameHeight
        a = float(self.entry1.get())
        b = float(self.entry2.get())
        frameWidth = int(self.entry3.get())
        frameHeight = int(self.entry4.get())

        headers = ['a', 'b', 'frame width', 'frame height']
        parameters = [{'a': a,
                       'b': b,
                       'frame width': frameWidth,
                       'frame height': frameHeight}]
        
        # resave configuration file
        with open('config.csv', 'w', encoding = 'UTF8', newline = '') as f:
            writer = csv.DictWriter(f, headers)
            writer.writeheader()
            writer.writerows(parameters)

        
class ForceCalibrationPage(tk.Frame):
    # fifth window frame forcecalibration
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        # label of frame layout 
        label = tk.Label(self, text ='Force Calibration', font = LARGEFONT,
                         width = 20, height = 1, anchor = 'nw')
        label.grid(row = 0, column = 0, columnspan = 3,
                   padx = 10, pady = 5)

        buttonExit = ttk.Button(self, text="Exit Window",
                                command = controller.destroy)
        buttonExit.grid(row = 0, column = 4, padx = 10, pady = 5)
        
        # buttons to go to different pages
        button1 = ttk.Button(self, text ='Set Position',
        command = lambda : controller.show_frame(SetPositionPage), 
                             width = 20)
        button1.grid(row = 1, column = 0, padx = 10, pady = 5)

        button2 = ttk.Button(self, text ='Millimanipulation',
        command = lambda : controller.show_frame(MillimanipulationPage), 
                             width = 20)
        button2.grid(row = 1, column = 1, padx = 10, pady = 5)
    
        button3 = ttk.Button(self, text ='Relaxation Tests',
        command = lambda : controller.show_frame(RelaxationTestsPage),
                             width = 20)
        button3.grid(row = 1, column = 2, padx = 10, pady = 5)
    
        button4 = ttk.Button(self, text ='Configuration',
        command = lambda : controller.show_frame(ConfigurationPage),
                             width = 20)
        button4.grid(row = 1, column = 3, padx = 10, pady = 5)
    
        button5 = ttk.Button(self, text ='Force Calibration',
                             width = 20)
        button5.grid(row = 1, column = 4, padx = 10, pady = 5)

        # separation line
        separator1 = ttk.Separator(self, orient = 'horizontal')
        separator1.grid(row = 2, column = 0, pady = 10,
                        columnspan = 6, sticky = 'we')


        # labelframe of x-axis movement
        labelFrame1 = tk.LabelFrame(self,
                                    text = 'Measurement')
        labelFrame1.grid(row = 3, column = 0, rowspan = 2, columnspan = 2,
                         padx = 10, pady = 0, sticky = 'nw')

        label1 = ttk.Label(labelFrame1,
                               text = 'Actual force (N):', width = 20)
        label1.grid(row = 0, column = 0, padx = 10, pady = 10,
                        sticky = 'w')

        self.entry1_var = tk.StringVar(value = '0')
        self.entry1 = ttk.Entry(labelFrame1, textvariable = self.entry1_var)
        self.entry1.grid(row = 0, column = 1, padx = 10, pady = 10, sticky = 'w')

        button6 = ttk.Button(labelFrame1, text ='Get point',
                             command = lambda : threading.Thread(target = self.getPoint).start(),
                             width = 20)
        button6.grid(row = 1, column = 1, padx = 10, pady = 10)

        label2 = ttk.Label(labelFrame1,
                               text = 'Point list (Actural force):')
        label2.grid(row = 2, column = 0, columnspan = 2, padx = 10, pady = 0,
                        sticky = 'w')

        self.listBox = tk.Listbox(labelFrame1)
        self.listBox.grid(row = 3, column = 0, rowspan = 3, padx = 10, pady = 10)

        button7 = ttk.Button(labelFrame1, text ='Delete point',
                             command = lambda : self.deletePoint(),
                             width = 20)
        button7.grid(row = 3, column = 1, padx = 10, pady = 10, sticky = 'nw')

        button8 = ttk.Button(labelFrame1, text ='Delete all points',
                             command = lambda : self.deleteAll(),
                             width = 20)
        button8.grid(row = 4, column = 1, padx = 10, pady = 10, sticky = 'nw')
        

        # labelframe of calibration figure
        self.labelFrameFig = tk.LabelFrame(self,
                                    text = 'Calibration figure')
        self.labelFrameFig.grid(row = 3, column = 2, rowspan = 5, columnspan = 3,
                         padx = 10, pady = 10, sticky = 'w')


        # define variables for ploting
        self.xlist = []
        self.ylist = []
        self.slope = 0
        self.intercept = 0
        self.r_value = 0
        
        # add figure canvas to show results
        self.fig = plt.Figure(figsize = (6, 6))
        self.fig.tight_layout()

        self.axFig = self.fig.add_subplot(211)
        self.axCal = self.fig.add_subplot(212)
        self.fig.tight_layout(pad = 3)
        self.canvas = FigureCanvasTkAgg(self.fig, self.labelFrameFig)
        self.canvas.get_tk_widget().grid(row = 0, column = 0, rowspan = 3, columnspan = 3, 
                         padx = 10, pady = 10, sticky = 'w')

        self.canvas.draw()
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval = 100)
        
    def getPoint(self):
        force = float(self.entry1.get())
        self.listBox.insert('end', force)
        # measure 5 s
        fMean, fStd = Mark3().calibration()
        self.xlist.append(fMean)
        self.ylist.append(force)
        
        if len(self.xlist) > 1:
            self.slope, self.intercept, self.r_value, p_value, std_err = stats.linregress(self.xlist, self.ylist)

    def deletePoint(self):
        # define function to delete selected points
        selected = self.listBox.curselection()
        self.listBox.delete(selected)
        self.xlist.pop(selected[0])
        self.ylist.pop(selected[0])

    def deleteAll(self):
        # define function to delete all points
        self.listBox.delete(0, 'end')
        self.xlist = []
        self.ylist = []
        self.slope = 0
        self.intercept = 0
        self.r_value = 0

    def animate(self, i):
        # define function to show real time figure 
        global xc, yc

        self.axFig.clear()
        self.axFig.plot(xc, yc)
        self.axFig.set_xlabel('Time (s)')
        self.axFig.set_ylabel('Measured voltage (V)')
        self.axFig.set_title('Force transducer data')

        self.axCal.clear()
        self.axCal.plot(self.xlist, self.ylist, 'o', color = 'blue', label = 'Measured')
        # define fitted line label
        labelFitted = 'Fitted line: y = '+str(self.slope)+'x + '+str(self.intercept)+r'$ (R^2$'+str(self.r_value**2)+')'
        
        self.axCal.plot(self.xlist, self.ylist, color = 'red', label = labelFitted)
        self.axCal.legend()
        self.axCal.set_xlabel('Measured voltage (V)')
        self.axCal.set_ylabel('Actual force (N)')
        self.axCal.set_title('Calibration data')


class Mark3():
    #Class to run Millimanipulation application
    def __init__(self):
        self.path = ''

    def XmoveRight(self):
        # function to run x-axis movement
        distanceX, speedX, distanceZ, speedZ = app.pass_on_text(SetPositionPage)

        # prepare parameters for setting x-axis positioner 
        stepsX = int(distanceX*200)
        stepSpeedX = int(speedX*200) # steps/s
        settingsX = {"Speed":stepSpeedX, "uSpeed":0, "Accel":10000, "Decel":10000, "AntiplaySpeed":50, "uAntiplaySpeed":0}

        
        try:
            with StageControl() as stcon:
                # set up x-axis movement parameters
                stcon.setMoveParameters(stcon.lrDevId, settingsX)
                print ('Set up x-axis movement parameters.')
                stcon.getMoveParameters(stcon.lrDevId)

                # run x-axis positioner
                stcon.moveRelativeRight(stepsX)
                stcon.waitForStopXY()
                time.sleep(0.3)
                # set parameters to original
                stcon.setMoveParameters(stcon.lrDevId, {"Speed":2000, "uSpeed":0, "Accel":2000,
                                                        "Decel":5000, "AntiplaySpeed":50, "uAntiplaySpeed":0})
		

        except KeyboardInterrupt:
            print('Exiting scan early!')
            
        except:
            print('Error thrown in XmoveRight()')
        
        # update current positions of x and z
        app.frames[SetPositionPage].updatePosition()
    

    def ZmoveUp(self):
        # function to run z-axis movement
        distanceX, speedX, distanceZ, speedZ = app.pass_on_text(SetPositionPage)

        # prepare parameters for setting z-axis positioner 
        stepsZ = int(distanceZ*12000)
        stepSpeedZ = int(speedZ*12000) # steps/s

        try:
            with StageControl() as stcon:
                # set up z-axis movement parameters
                stcon.setMoveParameters(stcon.udDevId, settingsZ)
                print ('Set up z-axis movement parameters.')
                stcon.getMoveParameters(stcon.udDevId)

                # run z-axis positioner
                stcon.moveRelativeUp(stepsZ)
                stcon.waitForStopXY()
                time.sleep(0.3) # pause time: 0.3 s
		

        except KeyboardInterrupt:
            print("Exiting scan early")		
        except:
            print("Error thrown in XmoveRight()")
        
        # update current positions of x and z
        app.frames[SetPositionPage].updatePosition()


    def Millimanipulation(self):
        # define function to run millimanipulation
        app.frames[MillimanipulationPage].animate()
        
        # get all entry variables
        distance, speed, path = app.pass_on_text(MillimanipulationPage)

        # create a folder to save images
        global recordImage, ImagePath
        if recordImage:
            ImagePath = path
            if not os.path.isdir(ImagePath): os.mkdir(ImagePath)

        # add extra 1 sec to capture relaxation
        targetTime = int(distance/speed)+1
        
        # prepare parameters for setting x-axis positioner 
        steps = int(distance*200)
        stepSpeed = int(speed*200) # steps/s
        settings = {"Speed":stepSpeed, "uSpeed":0, "Accel":10000, "Decel":10000, "AntiplaySpeed":50, "uAntiplaySpeed":0}

        try:
            with StageControl() as stcon:
                # set up x-axis movement parameters
                stcon.setMoveParameters(stcon.lrDevId, settings)
                print ('Set up x-axis movement parameters.')
                stcon.getMoveParameters(stcon.lrDevId)

                # start to record force
                trans = threading.Thread(target = self.recordForce(targetTime))
                trans.start()
                
                # run x-axis positioner
                stcon.moveRelativeRight(steps)
                stcon.waitForStopXY()
                time.sleep(0.3) # pause time: 0.3 s
                
                trans.join()

                # set parameters to original
                stcon.setMoveParameters(stcon.lrDevId, {"Speed":2000, "uSpeed":0, "Accel":2000,
                                                        "Decel":5000, "AntiplaySpeed":50, "uAntiplaySpeed":0})
                
        except KeyboardInterrupt:
            print('Exiting scan early!')		
        except:
            print('Error thrown in Millimanipulation()')

        # filter results using low-pass
        yf = self.filter(ym)
        
        # save results as csv
        self.save(path, xm, ym, yf)
            
    
    def RelaxationTests(self):
        # define function to run relaxation tests

        # get all entry variables
        interval, speed, noScrape, relaxTime, path = app.pass_on_text(RelaxationTestsPage)

        # create a folder to save images
        global recordImage, ImagePath
        if recordImage:
            ImagePath = path
            if not os.path.isdir(ImagePath): os.mkdir(ImagePath)

        # calculate required time
        targetTime = int((interval/speed+relaxTime+1)*noScrape)

        # prepare parameters for setting x-axis positioner 
        steps = int(interval*200)
        stepSpeed = int(speed*200) # steps/s
        settings = {"Speed":stepSpeed, "uSpeed":0, "Accel":10000, "Decel":10000, "AntiplaySpeed":50, "uAntiplaySpeed":0}

        try:
            with StageControl() as stcon:
                # set up x-axis movement parameters
                stcon.setMoveParameters(stcon.lrDevId, settings)
                print ('Set up x-axis movement parameters.')
                stcon.getMoveParameters(stcon.lrDevId)

                # start to record force
                trans = threading.Thread(target = self.recordForce(targetTime))
                trans.start()

                # run x-axis positioner
                for _ in range(noScrape):
                    stcon.moveRelativeRight(steps)
                    stcon.waitForStopXY()
                    time.sleep(relaxTime) 

                trans.join()

                # set parameters to original
                stcon.setMoveParameters(stcon.lrDevId, {"Speed":2000, "uSpeed":0, "Accel":2000,
                                                        "Decel":5000, "AntiplaySpeed":50, "uAntiplaySpeed":0})


        except KeyboardInterrupt:
            print('Exiting scan early!')		
        except:
            print('Error thrown in RelaxationTests()')

        # filter results using low-pass
        yf = self.filter(ym)
        
        # save results as csv
        self.save(path, xm, ym, yf)
        

    def calibration(self):
        # define function to get calibration point
        global xc, yc, operation
        xc = [0]
        yc = [0]
        
        try:
            operation = True

            with nidaqmx.Task() as task:
                task.ai_channels.add_ai_voltage_chan(niport,
                terminal_config=TerminalConfiguration.RSE,
                min_val=-5.0, max_val=5.0, units=VoltageUnits.VOLTS)
                
                startTime = time.perf_counter()
                
                while operation:
                    # read voltage
                    vol = task.read()
                    
                    # add x and y to lists              
                    xc.append(time.perf_counter()-startTime)
                    yc.append(vol) 

                    # stop measurement as reaching target time
                    if time.perf_counter()-startTime > 5: # run 5 sec for calibration
                        operation = False
                
        except KeyboardInterrupt:
            print('Exiting early!')
            operation = False
            return

        # filter results using low-pass
        yf = self.filter(yc)
        fMean = stats.tmean(yf)
        fStd = stats.tstd(yf)
        return [fMean, fStd]
        
    
    def recordForce(self, targetTime):
        # define function to record force
        global xm, ym, operation, a, b, niport
        
        try:
            xm = [0]
            ym = [0]
            operation = True

            with nidaqmx.Task() as task:
                task.ai_channels.add_ai_voltage_chan(niport,
                terminal_config=TerminalConfiguration.RSE,
                min_val=-5.0, max_val=5.0, units=VoltageUnits.VOLTS)
                
                startTime = time.perf_counter()
                
                while operation:
                    # read voltage
                    vol = task.read()
                    
                    # add x and y to lists              
                    xm.append(time.perf_counter()-startTime)
                    #ym.append(vol)
                    ym.append(a*vol+b)

                    # stop measurement as reaching target time
                    if time.perf_counter()-startTime > targetTime:
                        operation = False
                
        except KeyboardInterrupt:
            print('Exiting early!')
            operation = False
            return
    
    def grabImage(self):
        # define function to take images
        global frameWidth, frameHeight, img, cameraSelected, recordImage
        global ImagePath, operation, xm

        if cameraSelected: 
            cap = cv2.VideoCapture(0)
            # set up frame size
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, frameWidth)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frameHeight)
        
        try:
            while cameraSelected:      
                # get frames from camera and convert into images
                cap = cv2.VideoCapture(0)
                cvimage = cap.read()[1]
                img = cv2.cvtColor(cvimage, cv2.COLOR_BGR2RGB)

                # save images
                if operation and recordImage:
                    cv2.imwrite(ImagePath+'/{:.2f}.jpg'.format(xm[-1]),
                                cvimage, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    
        except KeyboardInterrupt:
            print('Exiting early!')
            return
        
        except:
            print('Error thrown in VideoCapture(). Check camera connection.')
            
        finally:
            cap.release()

    def filter(self, yy):
        # define function to filter results using low-pass
        
        global filFreq
        bb, aa = signal.butter(3, 1/max(1, filFreq), 'lowpass')
        return signal.filtfilt(bb, aa, yy)


    def save(self, path, xx, yy, yyf):
        # define function to save results as csv

        header = ['time (s)', 'Force (N)']
        with open(path+'.csv', 'w', encoding = 'UTF8', newline = '') as f:
            writer = csv.writer(f)
                
            # write the header and data
            writer.writerow(header)
            writer.writerows([[xx[i], yy[i], yyf[i]] for i in range(len(xx))])
                

# run GUI
if __name__ == '__main__':
    # import configuration parameters
    try:
        with open('config.csv', newline = '') as f:
            reader = csv.DictReader(f)
            column = [row for row in reader]
        dic = column[0]

        # ------ global variables ------
        a = float(dic['a'])
        b = float(dic['b'])
        frameWidth = int(dic['frame width']) 
        frameHeight = int(dic['frame height'])

    except:
        print ('Cannot find "config.csv" file, use default parameters.')

    app = tkinterApp()
    app.title('Millimanipulation Mark3 Driver')
    app.geometry('1100x800')
    app.mainloop() # ready to run

