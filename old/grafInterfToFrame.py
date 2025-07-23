# -*- coding: utf-8 -*-
"""
Создан: среда 7 июня 2023 19:36:53

Автор: Петросян Я.В.

В модуле описан класс, который создаёт интерфейс для работы с изображением и
встраивается во фрейм tkinter.
"""

import tkinter as tk
from PIL import ImageTk

class grafI2frame:
    '''
Класс создаёт интерфейс для работы с изображением на фрейме tkinter.

Класс имеет атрибуты, которыми можно пользоваться для его настройки и обмена
данными:

|begin{itemize}
|item |texttt{panelSost} -- фрейм под изображением, на котором можно размещать
      данные для отображения;
|item |texttt{canvas} -- холст, на котором производится отображение графики;
|item |texttt{X} -- пиксельная координата |texttt{x} курсора мыши на
      изображении (обновляется при перемещении мыши);
|item |texttt{Y} -- пиксельная координата |texttt{y} курсора мыши на
      изображении (обновляется при перемещении мыши).
|end{itemize}
    '''
    
    def __init__(self, image):
        self.image=image
        self.Frame=tk.Frame()
        self.width, self.height=self.image.size
        self.photo = ImageTk.PhotoImage(self.image)
        self.canvas = tk.Canvas(self.Frame) #, height=self.height, width=self.width)
        self.canvas.create_image(0, 0, anchor='nw',image=self.photo)
        self.panelSost=tk.Frame(self.Frame)
        self.panelSost.pack(side=tk.BOTTOM, fill=tk.X)
        self.sbV=tk.Scrollbar(self.Frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.sbV.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas["yscrollcommand"]=self.sbV.set
        self.sbH=tk.Scrollbar(self.Frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.sbH.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas["xscrollcommand"]=self.sbH.set
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.config(scrollregion=(0, 0, self.width, self.height))
        self.X=0
        self.Y=0
        def canxymouse(event):
            self.X=round(self.canvas.canvasx(event.x)/self.intScale*100,1)
            self.Y=round(self.canvas.canvasy(event.y)/self.intScale*100,1)
        self.canvas.bind('<Motion>', canxymouse)
        self.varScale=tk.IntVar(value=100)
        self.intScale=100
        def onScale(val):
            val=int(val)
            self.intScale=val
            self.width, self.height=self.image.size
            self.width=int(self.width*val/100)
            self.height=int(self.height*val/100)
        def scaleRelease(e):
            im=self.image.resize((self.width, self.height))
            self.photo = ImageTk.PhotoImage(im)
            self.canvas.create_image(0, 0, anchor='nw',image=self.photo)
            self.canvas.config(scrollregion=(0, 0, self.width, self.height))
        self.scale=tk.Scale(self.panelSost, from_=10, to=200, length=190,
         orient=tk.HORIZONTAL, command=onScale, variable=self.varScale)
        self.scale.grid(row=0, column=0, sticky='e')
        self.scale.bind('<ButtonRelease-1>',scaleRelease,'+')
