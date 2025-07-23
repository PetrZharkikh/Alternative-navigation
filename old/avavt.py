# -*- coding: utf-8 -*-
"""
Создание: вторник, 6 июня 2023, 6 18:10

Автор: Петросян Я.В.

Модуль создаёт графический интерфейс пользователя для проекта
<<Авиаавтоматика>>.
"""

import tkinter as tk
import tkinter.filedialog as fd
import serialImage
import oneImage
import sys
import grafInterfToFrame as gri
from PIL import Image
import os.path as osp #Модуль для работы с именами файлов
import geoFun

class TextRedirect(object):
    '''
Класс перенаправляет вывод функции |texttt{print} в |texttt{object}.

В качестве |texttt{object} можно использовать |texttt{tkinter.text}. Например,

|begin{lstlisting}[language=python]
import tkinter
import sys
...
t=tkinter.text(root) #Создали виджет text
...
stdout=sys.stdout #Запомнили куда был вывод
sys.stdout=TextRedirector(t) #Перенаправили вывод
root.mainloop() #Цикл перехвата событий
sys.stdout=stdout #Нужно вернуть поток вывода на место
|end{lstlisting}
    '''
    def __init__(self, widget, tag='stdout'):
        self.widget=widget
        self.tag=tag
    def write(self, str):
        self.widget.configure(state='normal')
        self.widget.insert('end', str, (self.tag,))
        self.widget.configure(state='disabled')
        self.widget.see(tk.END) #Перемещает курсор в конец. Тестировалось с tkinter.text
        self.widget.update() #Обновляет виджет

imInWin=None
panorama=None
sIm=None
lObj=[] #Список с объектами изображений. Там могут быть серии и одиночные файлы.
w=tk.Tk()
w.title('Авиаавтоматика')
w.geometry("800x600")

mainmenu=tk.Menu(w)
filemenu=tk.Menu(mainmenu, tearoff=0)
w.config(menu=mainmenu)
svFiles=tk.StringVar()
listfiles=[] #Список всех открытых файлов

def openfile():
    fn=fd.askopenfilename(title='Открыть изображение')#, filetypes=(('Изображения','*.jpg')))
    tmIm=oneImage.tmImage(fn)
    lObj.append(tmIm)
    listfiles.append(osp.basename(fn))
    svFiles.set(listfiles)
filemenu.add_command(label='Открыть файл...', command=openfile)

def appendfileinseries():
    fn=fd.askopenfilename(title='Добавить изображение в серию...')#, filetypes=(('Изображения','*.jpg')))
    if len(fn>0):
        sIm.append(fn)
        listfiles.append(osp.basename(fn))
        svFiles.set(listfiles)
        ind=sIm.index(osp.basename(fn))
        sIm.calcMGeoOneImage(ind)
        print('Изображение ',fn,' включено в серию.')
        #Вычисление географических координат и ошибки центра изображения от GPS >>>
        lp=sIm.serial[ind].xy2geo((sIm.serial[ind].par['width']/2, sIm.serial[ind].par['height']/2))
        print('Рассчитанные координаты центра изображения: долгота=',lp[0],'широта=',lp[1])
        lp1=(sIm.serial[ind].par['longitude'], sIm.serial[ind].par['latitude'])
        print('Координаты БпЛА в exif-данных: долгота=',lp1[0],'широта=',lp1[1])
        d=geoFun.dlinaDugiNachAzimut(lp, lp1)
        print('Погрешность=',d[0],'м')
    #<<< Вычисление географических координат и ошибки центра изображения от GPS
filemenu.add_command(label='Добавить изображение в серию...', command=appendfileinseries)

def opendir(): #Открытие папки для чтения серии изображений
    global sIm
    dirSerial=fd.askdirectory()
    if len(dirSerial)>0:
        sIm=serialImage.serialImage(dirSerial)
        lObj.append(sIm)
        listfiles.extend(sIm.listFiles())
        svFiles.set(listfiles)
        sIm.mGeoToIniFiles()
        filemenu.entryconfig('Создать панораму', state=tk.NORMAL)
        filemenu.entryconfig('Создать тайловое покрытие (перебор тайлов)', state=tk.NORMAL)
        filemenu.entryconfig('Создать тайловое покрытие (перебор изображений)', state=tk.NORMAL)
        print('Готово')
filemenu.add_command(label='Открыть папку...', command=opendir)

def createPanorama():
    global sIm
    sIm.calcMontage()
    d=osp.dirname(sIm.dirFiles) #Поднимаемся на одну папку вверх
    if not(d is None):
        sIm.saveMontage()
filemenu.add_command(label='Создать панораму', command=createPanorama, state=tk.DISABLED)

def createTilesPanoramaMetodTiles():
    sIm.calcMontageTiles(metod='tiles', modeIntersection='diag')
filemenu.add_command(label='Создать тайловое покрытие (перебор тайлов)',
                     command=createTilesPanoramaMetodTiles, state=tk.DISABLED)

def createTilesPanoramaMetodImages():
    sIm.calcMontageTiles(metod='images', modeIntersection='diag')
filemenu.add_command(label='Создать тайловое покрытие (перебор изображений)',
                     command=createTilesPanoramaMetodImages, state=tk.DISABLED)

mainmenu.add_cascade(label='Файл', menu=filemenu)

frame1=tk.Frame(w)
frame1.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
frameGraf=tk.Frame(frame1)
frameGraf.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

varX=tk.DoubleVar()
varY=tk.DoubleVar()
varLon=tk.DoubleVar()
varLat=tk.DoubleVar()

def clickLbFiles(event):
    global imInWin
    ind=lbFiles.curselection()
    fn=lbFiles.get(ind)
    if len(fn)>0:
        print('Выбран файл: ',fn)
        for i in lObj: #Поиск объекта, который содержит указанное имя файла
            if isinstance(i, oneImage.tmImage):
                print(i.filename)
                if osp.basename(i.filename)==fn:
                    tmIm=i
                    break
            if isinstance(i, serialImage.serialImage):
                k=i.index(fn)
                if not(k is None):
                    tmIm=i.serial[k]
                    break
        # ind=ind[0] #Индекс выбранного файла в списке
        # tmIm=sIm.serial[ind] #Выбранный объект tmImage
        image=Image.fromarray(tmIm.imCorrect)
        if not(imInWin is None):
            imInWin.Frame.destroy()
        imInWin=gri.grafI2frame(image)
        imInWin.Frame.pack(in_=frameGraf, side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tk.Label(imInWin.panelSost, text='x=').grid(row=0, column=1)
        tk.Label(imInWin.panelSost, text='y=').grid(row=1, column=1)
        tk.Label(imInWin.panelSost, textvariable=varX).grid(row=0, column=2)
        tk.Label(imInWin.panelSost, textvariable=varY).grid(row=1, column=2)
        tk.Label(imInWin.panelSost, text='Долгота=').grid(row=0, column=3)
        tk.Label(imInWin.panelSost, text='Широта=').grid(row=1, column=3)
        tk.Label(imInWin.panelSost, textvariable=varLon).grid(row=0, column=4)
        tk.Label(imInWin.panelSost, textvariable=varLat).grid(row=1, column=4)
        def canxymouse(event):
            varX.set(imInWin.X)
            varY.set(imInWin.Y)
            lp=tmIm.xy2geo((imInWin.X, imInWin.Y))
            if lp is None:
                lp=('Нет данных', 'Нет данных')
            varLon.set(lp[0])
            varLat.set(lp[1])
        imInWin.canvas.bind('<Motion>', canxymouse,'+')
    
lbFiles=tk.Listbox(frame1, width=16, selectmode=tk.SINGLE, listvariable=svFiles)
lbFiles.bind("<<ListboxSelect>>", clickLbFiles)
lbFiles.pack(side=tk.LEFT, fill=tk.Y)
sbFiles=tk.Scrollbar(frame1, orient=tk.VERTICAL, command=lbFiles.yview)
sbFiles.pack(side=tk.LEFT, fill=tk.Y)
lbFiles["yscrollcommand"]=sbFiles.set

frame2=tk.Frame(w)
frame2.pack(side=tk.BOTTOM, fill=tk.BOTH)
text=tk.Text(frame2, height=6, wrap=tk.WORD)
text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
sbText=tk.Scrollbar(frame2, orient=tk.VERTICAL, command=text.yview)
sbText.pack(side=tk.LEFT, fill=tk.Y,)
text["yscrollcommand"]=sbText.set

stdout=sys.stdout
sys.stdout=TextRedirect(text)
w.mainloop()
sys.stdout=stdout