# -*- coding: utf-8 -*-
"""
Начато: 28 июня 2023

Автор: Петросян Я.В.

Модуль предназначен для работы с тайловыми изображениями аэрофотоландшафта.
"""

import os
import os.path as osp
import glob
import numpy as np
from skimage import io, util, transform
import configparser as cp
import trMatrix

class exTilesAero(Exception): pass

class tiles:
    '''
Класс предназначен для работы с тайловыми изображениями аэрофотоландшафта.
    '''
    
    def __init__(self,dirTiles,z=None):
        '''
Конструктор класса принимает в качестве параметра строку с названием папки, в
которой записаны тайловые покрытия. Производится чтение структуры папок и
файлов для выяснения общего размера тайлового покрытия.

Исходные данные:

|begin{itemize}
|item |texttt{dirTiles} -- строка с названием папки, в которой лежит файловая
      структура тайлов;
|item |texttt{z} -- целое число с масштабом тайлов, если не указано, то
      берётся самый мелкий масштаб, который будет найден.
|end{itemize}

Созданный объект будет иметь атрибуты:

|begin{itemize}
|item |texttt{dirTiles} -- строка с именем папки, в которой лежит файловая
      структура тайлов;
|item |texttt{minX} -- минимальный индекс тайла по оси $x$;
|item |texttt{maxX} -- максимальный индекс тайла по оси $x$;
|item |texttt{minY} -- минимальный индекс тайла по оси $y$;
|item |texttt{maxY} -- максимальный индекс тайла по оси $y$;
|item |texttt(shapeTile) -- размер тайлового покрытия (кортеж по строкам,
      колонкам);
|item |texttt{shape} -- размер всего изображения в пикселах (кортеж (строки,
      колонки)).
|end{itemize}
        '''
        lz=os.listdir(dirTiles)
        for i in lz:
            if i.find('.')>=0:
                lz.remove(i)
        if len(lz)==0:
            raise exTilesAero('В папке '+dirTiles+' нет других папок.')
        if z is None: #Если масштаб тайла не был указан,
            lz.sort()
            self.z=int(lz[0][1:]) #то взять самый мелкий
        else:
            if 'z'+str(z) in lz: #Проверяем, присутствует ли указанный масштаб в списке
                self.z=z
            else:
                raise exTilesAero('В папке '+dirTiles+' нет тайлов масштаба z'+str(z)+'.')
        self.dirTiles=dirTiles
        dirTilesZ=osp.join(self.dirTiles, 'z'+str(self.z))
        lzi=os.listdir(dirTilesZ) #Получаем список папок с номерами внутри zn (обычно '0')
        self.minX=100000000000000000000000000
        self.maxX=0
        self.minY=100000000000000000000000000
        self.maxY=0
        zi=lzi[0]
        dirTilesZi=osp.join(dirTilesZ, zi)
        lx=os.listdir(dirTilesZi) #Получаем список папок внутри zn/i. Это тайловые координаты x
        x=[int(i[1:]) for i in lx] #Выделяем номера тайлов
        self.minX=min(x)
        self.maxX=max(x)
        for xn in lx:
            dirTilesZiXn=osp.join(dirTilesZi, xn)
            lxi=os.listdir(dirTilesZiXn) #Получаем список папок внутри xn/i (обычно 0).
            xi=lxi[0]
            dirTilesZiXni=osp.join(dirTilesZiXn, xi)
            ly=glob.glob(dirTilesZiXni+'/*.jpg')
            if len(ly)==0:
                continue
            a=[osp.basename(i) for i in ly]
            a=[i.split('.')[0] for i in a]
            y=[int(i[1:]) for i in a]
            minY=min(y)
            maxY=max(y)
            if self.minY>minY:
                self.minY=minY
            if self.maxY<maxY:
                self.maxY=maxY
        self.shapeTile=(self.maxY+1, self.maxX+1)
        self.shape=((self.maxY+1)*256, (self.maxX+1)*256)
        fnIni=osp.join(dirTiles, 'z'+str(self.z)+'.ini')
        self.m_geo=None
        if osp.isfile(fnIni):
            iniParam=cp.ConfigParser()
            iniParam.read(fnIni)
            sm=iniParam.get('matrix', 'm_geo')
            self.m_geo=eval('np.array('+sm+')')
        
    
    def xy2filename(self,xy):
        '''
Метод вычисляет имя файла в структуре тайлов по его координатам, которые
передаются как кортеж |texttt{(x, y)}.
        '''
        x,y=xy
        return osp.join(self.dirTiles, 'z'+str(self.z),'0','x'+str(x),
                        '0','y'+str(y)+'.jpg')
    
    def xyPix2tiles(self,xy):
        '''
Метод пересчитывает пиксельные координаты тайлового покрытия (ортофотоплана) в
координаты тайла и пиксельные координаты внутри него.

Исходные данные: |texttt{xy} -- кореж пиксельных координат (строка, колонка).

Результат: кортеж вида: |texttt{((xt, yt), (x, y))}, где |texttt{xе} и
|texttt{yt} -- координаты тайла, |texttt{x} и |texttt{y} -- пиксельные
координаты внутри тайла.
        '''
        x,y=xy
        xt=int(x/256)
        yt=int(y/256)
        x=x-xt*256
        y=y-yt*256
        return ((xt,yt),(x,y))
    
    def xyTiles2xy(self, xyTile, xy):
        '''
Метод вычисляет координаты тайлового покрытия (ортофотоплана) по координатам
тайла |texttt{xyTile} и пиксельным координатам внутри него |texttt{xy}.
        '''
        return (xyTile[0]*256+xy[0], xyTile[1]*256+xy[1])
    
    def xy2geo(self, xy, xyTile=None):
        '''
Метод вычисляет географические координаты пиксела.

Входные данные:

|begin{itemize}
|item |texttt{xy} -- кортеж |texttt{(x, y)} координат тайлового покрытия
      (ортофотоплана), если отсутствует параметр |texttt{xyTile}, иначе это
      координаты внутри тайла |texttt{xyTile};
|item |texttt{xyTile} -- кортеж |texttt{(x, y)} координат тайла.
|end{itemize}

Результат: кортеж |texttt{(долгота, широта)}. Если отсутствует матрица привязки
к географическим координатам |texttt{m|_geo}, то возвращается |texttt{None}.
        '''
        if not(xyTile is None):
            xy=self.xyTiles2xy(xyTile, xy)
        return trMatrix.pix2M_pix(xy, self.m_geo)
    
    def readTile(self,xyT,empty=True):
        '''
Метод возвращает изображение тайла по его координатам.

Исходные данные:

|begin{itemize}
|item |texttt{xyT} -- кортеж тайловых координат |texttt{(x, y)};
|item |texttt{empty} -- если |texttt{empty=True} (по умолчанию), то в случае
      отсутствия тайла будет возвращён пустой чёрный тайл; если
      |texttt{empty=False}, то -- значение |texttt{None}.
|end{itemize}
        '''
        fn=self.xy2filename(xyT)
        try:
            r=io.imread(fn)
        except:
            if empty:
                r=np.zeros((256,256,3), dtype=np.uint8)
            else:
                r=None
        return r
    
    def createImage(self,xy,shape):
        '''
Метод создаёт изображение, формируя его из тайлового покрытия.

Исходные данные:

|begin{itemize}
|item |texttt{xy} -- левый верхний угол в пиксельном пространстве тайлового
      покрытия (кортеж: $x$, $y$);
|item |texttt{shape} -- кортеж с количеством строк и колонок формируемого
      изображения.
|end{itemize}

Результат: изображение в формате |texttt{ndarray}.
        '''
        xyt0,xy0=self.xyPix2tiles(xy)
        xyt4,xy4=self.xyPix2tiles((xy[0]+shape[1], xy[1]+shape[0]))
        shapeT=((xyt4[1]-xyt0[1]+1)*256, (xyt4[0]-xyt0[0]+1)*256, 3)
        im=np.zeros(shapeT)
        x=0
        for xt in range(xyt0[0],xyt4[0]+1):
            y=0
            for yt in range(xyt0[1],xyt4[1]+1):
                imT=self.readTile((xt,yt), empty=False)
                if im is None:
                    continue
                im[y:y+255, x:x+255, :]=imT[0:255, 0:255, :]
                y+=255
            x=x+255
        im=im[xy0[1]:xy0[1]+shape[0], xy0[0]:xy0[0]+shape[1], :]
        return im
    
    def saveImage(self, xy, shape, filename):
        '''
Метод формирует изображение из тайорвого покрытия и записывает его в файл.
Если имеется матрица привязки к географической системе координат, то
записывается файл конфигурации, который позволяет создать экземпляр
класса |texttt{oneImage.tmImage} |sstr{oneImagetmImage}.

В файле конфигурации будут записаны: матрица привязки к географической системе
координат, географические координаты центра изображения, ширина и высота
изображения в пикселах. Параметр |texttt{camera=calctiles} показывает, что
изображение вычислено по тайловому покрытию.

Исходные данные:

|begin{itemize}
|item |texttt{xy}, |texttt{shape} -- как в методе |texttt{createImage}
      |sstr{tilesAerotilescreateImage};
|item |texttt{filename} -- строка с именем файла, в который нужно записать
      изображение.
|end{itemize}

Результат: изображение в формате |texttt{ndarray}, а также файлы на диске.
        '''
        im=self.createImage(xy, shape)
        io.imsave(filename, im)
        #Записываем файл конфигурации >>>
        if not(self.m_geo is None):
            iniFn=''.join(filename.split('.')[:-1])+'.ini'
            iniF=cp.ConfigParser()
            iniF.add_section('matrix')
            m=np.matmul(self.m_geo, np.array([[0, 0, xy[0]],[0, 0, xy[1]],[0, 0, 1]]))
            xyGeo=trMatrix.pix2M_pix((shape[1]/2, shape[0]/2), m)
            iniF.set('matrix', 'm_geo', np.array2string(m,separator=',').replace('\n', ''))
            iniF.add_section('params')
            iniF.set('params', 'camera', 'calctiles')
            iniF.set('params', 'latitude', str(xyGeo[1]))
            iniF.set('params', 'longitude', str(xyGeo[0]))
            iniF.set('params', 'height', str(shape[0]))
            iniF.set('params', 'width', str(shape[1]))
            with open(iniFn, "w") as config_file:
                iniF.write(config_file)
        #<<< Записываем файл конфигурации
        return im

def tileMinus(dirTiles):
    '''
Функция создаёт тайловое покрытие с более мелким масштабом.

Исходные данные: |texttt{dirTiles} -- строка с именем папки, в которой
находится хотя бы одно тайловое покрытие.

Функция находит тайловое покрытие с минимальным существующим масштабом и
создаёт на одну ступень меньше. В этом случае результат функции |texttt{True}.

Самый мелкий масштаб -- |texttt{z0}. Если функция находит этот масштаб, то
меньший масштаб не создаётся и возвращается результат |texttt{False}.
    '''
    T=tiles(dirTiles)
    z=T.z
    if z==0:
        print('Тайловое покрытие меньшего масштаба создать нельзя.')
        return False
    th,tw=T.shapeTile
    th=int(2**np.ceil(np.log2(th)))
    tw=int(2**np.ceil(np.log2(tw)))
    z-=1
    print('Создаю тайловое покрытие масштаба',z)
    dirZi='z'+str(z)
    dirZi=osp.join(dirTiles,dirZi)
    os.mkdir(dirZi) #Создаём папку для меньшего масштаба
    dirZi0=osp.join(dirZi, '0')
    os.mkdir(dirZi0) #Создаём вложенную папку 0
    for xi in range(0,tw,2):
        xs='x'+str(int(xi/2))
        dirZi0Xi=osp.join(dirZi0, xs)
        os.mkdir(dirZi0Xi) #Создаём вложенную папку xi
        dirZi0Xi0=osp.join(dirZi0Xi, '0')
        os.mkdir(dirZi0Xi0) #Создаём вложенную папку 0
        for yi in range(0,th,2):
            ys='y'+str(int(yi/2))
            fn=osp.join(dirZi0Xi0, ys+'.jpg') #Создаём имя файла
            a=T.readTile((xi,yi))
            b=T.readTile((xi+1,yi))
            c=T.readTile((xi,yi+1))
            d=T.readTile((xi+1,yi+1))
            im=util.montage([a,b,c,d], multichannel=True)
            im=transform.resize(im, (256, 256))
            if im.max()>0:
                io.imsave(fn, util.img_as_ubyte(im))
    #Записываем файл конфигурации >>>
    if not(T.m_geo is None): #Файл конфигурации есть смысл записывать если есть матрица географической привязки
        iniFn=osp.join(dirTiles, 'z'+str(z)+'.ini')
        iniF=cp.ConfigParser()
        iniF.add_section('matrix')
        m_geoMinus=np.matmul(T.m_geo,np.array([[2, 0, 0],[0, 2, 0],[0, 0, 1]]))
        iniF.set('matrix', 'm_geo', np.array2string(m_geoMinus,separator=',').replace('\n', ''))
        with open(iniFn, "w") as config_file:
            iniF.write(config_file)
    #<<< Записываем файл конфигурации
    print('Готово')
    return True
            
def tileToZero(dirTiles):
    '''
Функция создаёт тайловые покрытия от минимального найденного до нулевого.

Входные данные как в функции |texttt{tileMinus} |sstr{tilesAerotileMinus}.
    '''
    while tileMinus(dirTiles):
        continue

#r=tiles('tilesf_0')#'tiles22.06.23 Pole_0')
#tileToZero('tilesf_0')
#im=r.createImage((1000, 1000), (4000, 4000))
#io.imsave('fromTiles.jpg', im)