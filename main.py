'''
Created on Jun 28, 2022

@author: noaht
'''
#!/usr/bin/env python
import pathlib
import os
import math
from math import ceil
import tifffile as tf
import numpy as np
import tkinter as tk
from tkinter import filedialog as fd 
import tkinter.messagebox as tkmb

'''
TODO:
-consider more options for app
-color or grayscale

'''

def reslice(file):
    #converts given array into a list (B,R,G) of arrays representing a reslice 
    #in the desired plane
    resultList = []
    arr = tf.imread(file)
    if app.planeChoice > 1 :
        arr = np.swapaxes(arr, 0,2)
    if app.planeChoice ==2:
        arr = np.swapaxes(arr, 0,3)
    arr = compress(arr)
    resultList = colorTransform(arr, resultList)
    return resultList

def colorTransform(arr, resultList):
    if app.chromeChoice == 1:
        for stack in np.split(arr, 3, axis=1):
            resultList.append(np.squeeze(stack))
        return resultList
    if app.chromeChoice == 2:
        template = np.array(np.zeros(arr.shape))
        blue = np.stack((arr[:,0,:,:], template[:,0,:,:], template[:,0,:,:]), axis=1)       
        red = np.stack((template[:,0,:,:], arr[:,1,:,:], template[:,0,:,:]), axis=1)
        green = np.stack((template[:,0,:,:], template[:,0,:,:], arr[:,2,:,:]), axis=1)
        resultList.append(blue)
        resultList.append(red)
        resultList.append(green)
        return resultList
    if app.chromeChoice == 3:
        resultList.append(arr)
        return resultList
                        
def compress(arr):
    #compresses the given array along the current axis to the degree specified 
    #in the spinbox  
    compression = int(app.slices.get())
    Zframes = ceil((arr.shape)[0] / compression)
    arrCompressed = np.zeros((Zframes, (arr.shape)[1], (arr.shape)[2], (arr.shape)[3]))
    frame = 0
    count = 1
    while count <= Zframes:
        if (compression*count-1 > (arr.shape)[0]):
            tmp = arr[frame:,:,:,:]
        else:
            tmp = arr[frame:(compression*count-1),:,:,:]
        if app.styleChoice==1:
            frameCondensed = np.maximum.reduce(tmp, axis=0)
        if app.styleChoice==2:
            frameCondensed = np.minimum.reduce(tmp, axis=0)
        if app.styleChoice==3:
            frameCondensed = np.add.reduce(tmp, axis=0)        
        arrCompressed[(count-1),:,:,:] = frameCondensed
        frame = frame + compression
        count = count + 1
    return arrCompressed

def save(fileList):
    #calls reslice and saves the return as .tif files in appropriate locations
    reslicedList = []
    modes = ['[B]','[R]','[G]']
    file = 0
    for LSM in fileList:
        directory = app.dirList[file]
        reslicedList.append(reslice(directory))
        mode = 0
        tmp = directory.split('.lsm')[0] 
        folderPath = addFolder(tmp)        
        for arr in reslicedList[file]:
            name = LSM.split('.lsm')[0] + modes[mode] + '.tif'
            path = os.path.join(folderPath, name)
            print(arr.shape)
            tf.imwrite(path, arr.astype('uint8'), dtype='uint8', imagej=True)
        file = file+1
   
    
def addFolder(name):
    #adds a folder with the given name to the root directory
    curDir = pathlib.Path().resolve()
    finalDir = os.path.join(curDir, name)
    if not os.path.exists(finalDir):
        os.makedirs(finalDir)
    return finalDir
    
def main():
    #executes with the helper methods above; returns R,G,B .tif files in folders in the same directory as the .lsm file
    if app.planeChoice == 0:
        tkmb.showerror('ERROR', 'Please choose a slicing plane')
        return
    if app.styleChoice == 0:
        tkmb.showerror('ERROR', 'Please choose a condensation style')
        return
    if app.chromeChoice == 0:
        tkmb.showerror('ERROR', 'Please choose a color style')
        return
    fileList = app.Listbox.get(0, tk.END)
    save(fileList)

class Application(tk.Frame):
    #initializes the frame from which he application runs
    
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)   
        self.grid(sticky=tk.N+tk.S+tk.E+tk.W)
        self.createWidgets()
        self.planeChoice=0
        self.styleChoice=0
        self.chromeChoice=0
        self.dirList=[]

    #creates the initial window upon launch
    def createWidgets(self):
        
        #configures the grid in which the widgets will sit
        top=self.winfo_toplevel()                
        top.rowconfigure(0, weight=1)            
        top.columnconfigure(0, weight=1)         
        self.rowconfigure(0, weight=1)           
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1) 
        self.columnconfigure(1, weight=1)          
        self.columnconfigure(2, weight=1)      
        
        #CHOOSE FILE
        self.Button = tk.Button(self, text='Choose Experimental Confocals (.lsm)', command=openFile)
        self.Button.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W, padx=10, pady=10)
        
        #SCROLLBAR
        self.xScroll = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.xScroll.grid(row=2, column=0, sticky=tk.E+tk.W)
        
        #LISTBOX
        self.Listbox = tk.Listbox(self, height = 5, xscrollcommand=self.xScroll.set, width=50, selectmode=tk.MULTIPLE)
        self.Listbox.grid(row=1, column=0, rowspan=1)
        self.xScroll['command'] = self.Listbox.xview
        
        #GO
        self.Button = tk.Button(self, text='Go', command=main, width=5, height=1, bd=4)
        self.Button.grid(row=1, column=1, sticky=tk.W+tk.S, pady=10)
        
        #DELETE
        self.Button = tk.Button(self, text='Delete', command=delete, width=5, height=1, bd=4)
        self.Button.grid(row=1, column=1, sticky=tk.W+tk.S, padx=60, pady=10)          
        
        #PLANE
        entries = ['XY', 'YZ', 'XZ']
        plane = tk.StringVar()
        plane.set('select plane')
        self.Plane = tk.OptionMenu(self, plane, *entries, command=planeSelect)
        self.Plane.grid(row=0, column=1, sticky=tk.N, pady=15)
        
        #CONDENSATION
        entries = ['maximum', 'minimum', 'composite']
        style = tk.StringVar()
        style.set('condensation style')
        self.Style = tk.OptionMenu(self, style, *entries, command=styleSelect)
        self.Style.grid(row=0, column=1, sticky=tk.S, pady=35) 
        
        #COLOR
        entries = ['greyscale', 'color', 'composite']
        color = tk.StringVar()
        color.set('color style')
        self.Color = tk.OptionMenu(self, color, *entries, command=chromeSelect)
        self.Color.grid(row=0, column=1, sticky=tk.N, pady=50)               
 
        #SPINBOX LABEL
        self.labelslices = tk.LabelFrame(self, text='condensation factor', labelanchor='n', width=125, height=50)
        self.labelslices.grid(row=1, column=1, sticky=tk.N) 
        
        #SPINBOX
        self.slices = tk.Spinbox(self, increment=1, width=10, from_=1, to=math.inf)
        self.slices.grid(row=1, column=1, sticky=tk.N, pady=20)

    
#callback function for selecting files to be manipulated
def openFile():    
    directory = fd.askopenfilename() 
    file = os.path.basename(os.path.normpath(directory))
    if file!='.':
        if '.lsm' not in file:
            tkmb.showerror('ERROR', 'Selected files must be in .lsm format')
        if file in app.Listbox.get(0, tk.END):
            tkmb.showerror('ERROR', 'File already selected')
        else:
            app.Listbox.insert(tk.END, file)
    app.dirList.append(directory)
    
#helper methods to the menu methods                              
def planeSelect(plane):
    if plane == 'XY':
        app.planeChoice=1
    if plane == 'YZ':
        app.planeChoice=2
    if plane == 'XZ':
        app.planeChoice=3

def styleSelect(style):
    if style == 'maximum':
        app.styleChoice=1
    if style == 'minimum':
        app.styleChoice=2
    if style == 'composite':
        app.styleChoice=3 

def chromeSelect(chrome):
    if chrome == 'greyscale':
        app.chromeChoice=1
    if chrome == 'color':
        app.chromeChoice=2
    if chrome == 'composite':
        app.chromeChoice=3

#helper method to the listbox menu; deletes entries        
def delete():
    selectedTup = app.Listbox.curselection()
    descending = sorted(selectedTup, reverse=True)
    for line in descending:
        app.Listbox.delete(line)
        del app.dirList[line]
        

#configurations for the application frame
app = Application()
app.master.geometry('500x300')
app.master.title('396 Application')
app.mainloop()   
