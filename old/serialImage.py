# -*- coding: utf-8 -*-
"""
Автор: Петросян Я.В.

Начало работы: 27.04.2023.

Модуль предназначен для работы с последовательностью изображений
аэрофотоландшафта. Обработка каждого отдельного изображения
осуществляется экземплярами класса |texttt{tmImage} в модуле |texttt{oneImage}
|sstr{oneImagetmImage}.

В этом модуле описан класс |texttt{serialImage}, который управляет экземплярами
класса |texttt{trImage} как списком.
"""

import oneImage
import trMatrix
import numpy as np
from skimage import transform, util
import glob
import os.path as osp #Модуль для работы с именами файлов
import os
import skimage.io as io
import configparser as cp #Импорт модуля для работы с ini-файлом
import geometriya

class serialImage:
    '''
Класс для управления последовательностью изображений аэрофотоландшафта.

Изображения в последовательности являются связными, поэтому класс предназначен
для того, чтобы работать с ними как с одним большим изображением, хотя оно и
состоит из фрагментов. При этом каждое изображнение является экземпляром класса
|texttt{tmImage} |sstr{oneImagetmImage}, который <<знает>> все параметры
каждого отдельного изображения и производит с ним все действия.
    '''
    
    @property
    def m_previous(self, i_im=None):
        '''
Свойство возвращает матрицу для сшивки двух последовательных изображений.

Если эта матрица рассчитывалась ранее, то она находится в файле конфигурации
изображения и будет взята оттуда. Вычисление этой матрицы достаточно
ресурсоёмкий процесс.

Входные данные:

|texttt{i|_im} является индексом в списке изображений |texttt{serial}.
Данный индекс указывает номер изображения, который нужно сшить с предыдущим.
Если |texttt{i|_im} опущен, то берётся последнее изображение. Индексация
начинается с нуля.

Результат: матрица размером 3|texttimes 3 формата |texttt{ndarray}.

Данная матрица позволяет трансформировать и перенести изображение с номером
|texttt{i|_im} на холст предыдущего изображения в списке. Таким образом,
можно сшить два изображения.

Матрица также помещается в словарь параметров экземпляра класса
|texttt{tmImage} |texttt{par} с ключом |texttt{'m|_previous'}, поэтому она
сохраняется между сессиями и не требует повторных вычислений.

При вычислении матрицы используются скорректированные изображения экземпляра
класса |texttt{tmImage} в свойстве |texttt{imCorrect}
|sstr{oneImagetmImageimCorrect}.
        '''
        n=len(self.serial)
        if n==0:
            self.serial[i_im].m_previous=np.eye(3)
        if i_im is None:
            i_im=n-1
        if self.serial[i_im].m_previous is None:
            if i_im==0:
                self.serial[i_im].m_previous=np.eye(3)
            else:
                a=self.serial[i_im-1].imCorrect
                b=self.serial[i_im].imCorrect
                print('Вычисление матрицы для сшивки между',
                      self.serial[i_im-1].par['filename'],
                      'и',self.serial[i_im].par['filename'])
                #Вычисление матрицы трансформации (гомографии). Запоминаем обычную матрицу (не обратную).
                self.serial[i_im].m_previous=np.linalg.inv(trMatrix.m_Shivka(a, b))
            self.serial[i_im].saveIni()
        return self.serial[i_im].m_previous
    
    def shapeCorrect(self,oIm):
            '''
Подфункция. Возвращает размер скорректированного изображения. Если его нет,
то исходного. При этом сами изображения не вызываются и размер берётся из
словаря с параметрами.
            '''
            if 'widthcorrect' in oIm.par:
                return (int(oIm.par['heightcorrect']), int(oIm.par['widthcorrect']))
            else:
                return (int(oIm.par['height']), int(oIm.par['width']))
    
    @property
    def unitedShape(self):
        '''
Свойство пересчитывает размер холста, на который должны поместиться все
сшиваемые изображения.

Имена файлов изображений хранятся в списке |texttt{serial}
|sstr{serialImageserailImageappend}. Если их необходимо сшить в одно изображение, то
потребуется холст большего размера, на который уместятся все сшиваемые
изображения с учётом их перекрытия и траектории полёта БпЛА.

Результат:

|begin{itemize}
|item размер изображения как кортеж |texttt{(height, width)} --
      высота и ширина изображения соответственно;
|item положение левого-верхнего угла первого изображения в серии на новом
      холсте в виде кортежа |texttt{(y, x)} -- координаты в действительных
      числах.
|end{itemize}
        '''
        if not(self._unitedShape is None):
            return (self._unitedShape, self.yxFirstImage)
        print('Вычисление общего холста для монтажа')
        m_relative=np.eye(3)
        xmin=xmax=ymin=ymax=0
        for i in self.serial:
            m_relative=np.matmul(m_relative, i.m_previous)
            t=trMatrix.cornersXY(self.shapeCorrect(i), m_relative)
            xymin=np.min(t, axis=0)
            xymax=np.max(t, axis=0)
            xmin=min([xymin[0], xmin])
            ymin=min([xymin[1], ymin])
            xmax=max([xymax[0], xmax])
            ymax=max([xymax[1], ymax])
        self._unitedShape=(int(ymax-ymin+1), int(xmax-xmin+1))
        self.yxFirstImage=(-ymin, -xmin)
        print('Размер холста=',self._unitedShape)
        self.height=self._unitedShape[0]
        self.width=self._unitedShape[1]
        return (self._unitedShape, self.yxFirstImage)

    def append(self, fileName):
        '''
Метод, добавляющий новое изображение к списку открытых изображений.

Входные параметры:

|texttt{filename} -- имя файла с изображением.

Имя файла с изображением передаётся конструктору класса |texttt{tmImage}
|sstr{oneImagetmImage}, экземпляр которого добавляется к списку экземпляра
класса |texttt{serialImage} |texttt{serial}. Так как используется класс
|texttt{tmImage}, то он уже всё <<знает>> о добавляемом изображнении.

В словарь параметров изображения также заносятся данные об имени предыдущего
и следующего файла с изображением в последовательности. Эти данные также
сохраняются в файле конфигурации изображения |sstr{oneImagetmImagesaveIni} с
ключами |texttt{previous} и |texttt{next} соответственно.

Для первого изображения в серии параметр |texttt{previous} имеет значение
|texttt{None}, то же значение имеет параметр |texttt{next} для последнего
изображения в серии.

Указание этих связей позволяет сшивать изображения в различных сессиях в
произвольном порядке.

Если два изображения сшить невозможно, то алгоритм определения пар особых
точек может вернуть такие пары, которые приводят к большим искажениям
трансформируемого изображения. В этом случае масштабный коэффициент
(правый-нижний) матрицы трансформации сильно отличается от единицы.
Признаком невозможности привязки в программе является проверка условия:
если этот коэффициен больше 10 или меньше 0.1, то изображение нельзя сшить
с предыдущим и серия прерывается.

Результат:

|begin{itemize}
|item |texttt{True} -- изображение добавлено в серию;
|item |texttt{False} -- изображение не добавлено в серию по причине
      невозможности сшить его с предыдущим.
|end{itemize}
        '''
        if self.resizeImages is None:
            i=oneImage.tmImage(fileName)
        else:
            i=oneImage.resizeTmImage(fileName, n=self.resizeImages)
        n=len(self.serial)
        self.serial.append(i)
        if i.m_previous is None:
            #Добавить имя предыдущего файла в последовательности
            i.par['previous']='None' if n==0 else self.serial[n-1].par['filename']
            i.par['next']=None
            if n>0:
                self.serial[n-1].par['next']=osp.basename(fileName) #К предыдущему файлу добавить имя слудующего
                self.serial[n-1].saveIni()
            m=self.m_previous #Рассчитать матрицу привязки добавленного изображения к предыдущему
            if not(m is None): #Матрица может отсутствовать если предыдущего изображения нет
                if m[2,2]>10 or m[2,2]<0.1: #Проверка на возможность сшивки изображения с предыдущим
                    print('Изображение ',fileName,' нельзя сшить с предыдущим.')
                    self.serial.pop()
                    return False
        self._unitedShape=None #Сбрасываем размер холста при добавлении нового изображения
        return True
    
    def __init__(self, listFiles=None, ext='.jpg', resizeImages=None):
        '''
Конструктор класса.

Входные параметры:

|begin{itemize}
|item \texttt{listFiles} -- список имён файлов с изображениями, которые нужно
      открыть (может отсутствовать);
|item |texttt{ext} -- расширение файлов, которые нужно прочитать (по умолчанию
      |texttt{.jpg}). Данный параметр применяется только если
      |texttt{listFiles} -- строка. В этом случае считается что
      |texttt{listFiles} содержит имя папки в в ней необходимо прочитать все
      файлы с этим расширением;
|item |texttt{resizeImages} -- параметр указывает, нужно ли выполнять
      изменение размера изображения. Если |texttt{None}, то не нужно. В этом
      случае обработка изображений будет производиться через класс
      |texttt{tmImage}. Если указан действительный коэффициент или кортеж
      (см. описание |texttt{oneImage.tmImage.|_|_init|_|_}
      |sstr{oneImagetmImageinit}), то через класс |texttt{resizeTmImage}
      |sstr{oneImageresizeTmImage}.
|end{itemize}

Создаёт экземпляр класса |texttt{serialImage} для управления
последовательностью изображений. Если указан список имён файлов с изображениями
во входном параметре, то вызывается метод |texttt{append}
|sstr{serialImageserialImageappend} для каждого имени файла в списке. Если
список имён файлов не указан, то метод |texttt{append} можно вызывать в процессе
 работы с экземпляром класса и добавлять изображения по мере их появления.
        '''
        self.serial=[] #Список для хранения открытых изображений (экземпляры класса tmImage)
        self.resizeImages=resizeImages #Запоминаем изменение размера изображений
        self.yxFirstImage=[0,0] #Координаты левого-верхнего угла первого изображения в серии на расширенном холсте
        self._unitedShape=None #Служебная переменная для хранения размера холста, вмещающего все сшитые изображения в серии
        self._spaceOne=np.zeros((1,1))
        self._m_im2Canvas=[] #Матрица пересчёта i-го изображения в пространство холста
        self.montage=None
        self.m_geo=None
        self.dirFiles=None
        self.width=None
        self.height=None
        self.filename=None #Имя файла с панорамой серии
        self.NTiles=0 #Всего тайлов для покрытия панорамы
        if isinstance(listFiles, str): #Если listFiles строка,
            #то это папка и нужно получить список файлов из папки.
            fm=listFiles+'/*'+ext
            self.dirFiles=listFiles #Запоминаем папку, в которой лежали файлы
            print('Открывается группа файлов: '+fm)
            listFiles=glob.glob(fm)
            listFiles.sort()
        if not(listFiles is None):
            for i in listFiles:
                if not(self.append(i)):
                    break
        print('Создание серии завершено.')
    
    def spaceOne(self, shape):
        '''
Служебный метод. Создаёт пространство указателей одного изображения для
переноса пиксел изображения на общий холст при сшивке.

Входные параметры:

|texttt{shape} -- размер изображения как кортеж |texttt{(height, width)} --
высота и ширина изображения соответственно.

При сшике множества изображений возникает задача выбора: пиксел с какого
изображения ставить на холст панорамы при их взаимном пересечении? Очевидно,
что нужно выбирать пиксел с того изображения, на котором он ближе к центру.
Во-первых, ближе к центру меньше геометрических искажений. Во вторых, высокие
объекты, например здания или деревья сняты в нодир и закрывают собой меньшее
пространство как если бы находились на краю кадра.

При сшивке двух изображений для каждого пиксела холста панорамы можно было бы
рассчитать удаление от центра каждого изображения и взять пиксел с того
изображения, центр которого ближе. Но при сшивке множества изображений,
особенно, если БпЛА совершал полёт змейкой, и сопоставлять приходится не
только соседние изображения, но и изображения соседних витков такая задача
оказывается слишком сложной, учитывая ещё и геометрические трансформации.

Поэтому для каждого изобажения вычисляется пространство указателей. Это массив
действительных чисел формата |texttt{np.float16} (взят формат с минимальными
требованиями к памяти) такого же размера как и исходное изображение, в котором
для каждого пиксела изображения рассчитана близость к центру и пронормировано
в диапазон $(0, 0.9)$.

Для каждого изображения формируется такое пространство указателей, которое
подвергается тем же геометрическим трансформациям, что и изображение связанное
с ним. Это позволяет не только определять близость каждого пиксела к центру
своего изображения, но и иметь данные об области, занимаемом изображением
на холсте панорамы.

После получения панорамы массивы с пространствами указателей не сохраняются.
        '''
        if self._spaceOne.shape==(shape[0], shape[1]): #Если размер требуемого пространства совпадает с тем, которое уже расчитано,
            return self._spaceOne #то вернуть имеющееся
        x, y=np.meshgrid(range(shape[1]), range(shape[0]))
        md=np.sqrt(((shape[1]/2)**2+(shape[0]/2)**2))*0.9
        self._spaceOne=np.abs(np.sqrt((x-shape[1]/2)**2+(y-shape[0]/2)**2)-md)/md
        return self._spaceOne
    
    def spaceImages(self):
        '''
Метод создаёт пространство с указателями панорамного изображения.

Данный метод создаёт массив формата |texttt{np.floaf16} такого же размера как
панорамное изображение и выполняет те же трансформации как с изображениями,
но вместо них берёт массивы пространств указателей одиночных изображений
|sstr{serialImageserialImagespaceOne}. Каждому массиву указателей добавляется
целое число равное индексу номера изображения в списке |texttt{serial} плюс 1.
При трансформации пространств указателей на общий холст панорамного изображения
в местах наложения пространств берётся значение того элемента пространства,
для которого дробная часть больше. При этом целая часть элемента указывает на
изображение, с которого нужно взять пиксел для формирования элемента
панорамного изображения.

Таким образом достигается компромис между расходом памяти и сложностью
вычисления панорамы. В последствии данное пространство указателей панорамного
изображения может быть использовано для вычисления не всей панорамы из
серии изображений, а только заказанной её части.

Результат: массив формата |texttt{np.float16}
        '''
        unitedShape, yxFirstImage=self.unitedShape
        try:
            sIm=np.zeros(unitedShape, dtype=np.float16) #Создаём пустое пространство указателей
        except:
            print('Размер панорамы слишком велик для одного холста.\\nНеобходимо создавать тайловую панораму')
            return None
        k=0
        print('Вычисление положений изображений на холсте панорамы')
        for i in self.serial:
            k+=1
            sp=self.spaceOne(self.shapeCorrect(i))+k
            m=self.m_im2Canvas[self.serial.index(i)]
            sp=transform.warp(sp, np.linalg.inv(m), output_shape=unitedShape)
            b=(sp-np.int16(sp))>(sIm-np.int16(sIm))
            sIm[b]=sp[b]
            print(i.par['filename'])
        return sIm
    
    def calcMontage(self):
        '''
Метод собитает панорамное изображение из всех изображений в последовательности.

Вначале вычисляется общий холст для панорамного изображения с применением
метода |texttt{unitedShape} |sstr{serialImageserialImageunitedShape}.

Затем создаётся пространство указателей методом |texttt{spaceImages}
|sstr{serialImageserialImagespaceImages}

Далее производится трансформация каждого изображения на холст панорамы. Под
этим подразумевается выполнение трансформаций:

|begin{itemize}
|item связанных с приведением изображения к плановому виду (если есть данные о
      крене и тангаже воздушного судна);
|item сшивка с предыдущим изображением;
|item перенос на холст панорамы.
|end{itemize}

Общая матрица трансформации для каждого изображения вычисляется по формуле:

$$
m_k=m_p |prod|limits_{i=0}^k m_i
$$
где:

|begin{itemize}
|item $m_k$ -- матрица для переноса $k$-го изображения в списке
      |texttt{serial} на холст панорамы, учитывающая все трансформации;
|item $m_p$ -- матрица трансформации к плановой проекции и ориентации по
      сторонам света (находится в свойстве |texttt{m|_all} экземпляра класса
      |texttt{oneImage} |sstr{oneImagetmImagemall});
|item $m_i$ -- матрица сшивки с предыдущим изображением. Так как предыдущее
      изображение тоже <<пришивалось>> к своему предыдущему, то нужно
      учитывать и его трансформацию (находится в свойстве |texttt{m|_previous}
      экземпляра класса |texttt{oneImage} вычисляется данным классом
      |sstr{serialImageserialImagemprevious}). Для первого изображения в серии
      используется матрица переноса изображения на холст панорамы.
|end{itemize}

Для того чтобы получить панораму из четырёх изображений можно выполнить код

|begin{lstlisting}[language=python]
#Создание экземпляра класса serialImage с 4 изображениями
>>>sim=serialImage(['1.jpg', '2.jpg', '3.jpg', '4.jpg'])
>>>r=sim.montage() #Создание панорамы
>>>io.imsave('res.jpg',r) #Запись панорамы в файл res.jpg
|end{lstlisting}

Помимо этого панорама сохраняется в переменной экземпляра класса
|texttt{montage} и может быть сохранена методом |texttt{saveMontage}
|sstr{serialImageserialImagesaveMontage}.
        '''
        sIm=self.spaceImages()
        sh=list(self.unitedShape[0])
        sh.append(3)
        try:
            r=np.zeros(sh)
        except:
            print('Размер панорамы слишком велик для одного холста.\\nНеобходимо создавать тайловую панораму')
            return None
        k=0
        print('Перенос изображений на холст панорамы')
        for i in self.serial:
            m=self.m_im2Canvas[self.serial.index(i)]
            k+=1
            imt=transform.warp(i.imCorrect, np.linalg.inv(m),
                               output_shape=self.unitedShape[0])
            i.imClear()
            b=np.int16(sIm)==k
            r[b,:]=imt[b,:]
            print(i.par['filename'])
        self.montage=r
        return r
    
    @property
    def m_im2Canvas(self):
        '''
Свойство возвращает список матриц привязки изображений к холсту панорамы. Если
такого списка нет, то он вычисляется.
        '''
        if len(self._m_im2Canvas)==0:
            m=np.array([[1, 0, self.unitedShape[1][1]],
                        [0, 1, self.unitedShape[1][0]],
                        [0, 0, 1]]) #Матрица переноса первого изображения на общий холст
            self._m_im2Canvas=[] #Список содержит матрицы пересчёта пиксельных координат каждого изображения в серии на холс панорамы
            for i in self.serial: #Создание пар соответсвующих точек в двух различных системах координат
                m=np.matmul(m, i.m_previous) #Матрица пересчёта пространства i-го изображения на холст
                self._m_im2Canvas.append(m)
        return self._m_im2Canvas
    
    def xyImage2xyMontage(self, im, xy):
        '''
Метод пересчитывает пиксельные координаты изображения |texttt{tIm} класса
|texttt{tmImage} на холст панорамы.

Входные данные:

|begin{itemize}
|item |texttt{im} -- номер изображения в серии или экземпляр класса
      |texttt{tmImage};
|item |texttt{xy} -- кортеж с координатами холста |texttt{(x, y)}.
|end{itemize}

Результат: кортеж с координатами |texttt{(x, y)} на холсте панорамы.
        '''
        if isinstance(im, oneImage.tmImage):
            im=self.serial.index(im)
        m=self.m_im2Canvas[im]
        return trMatrix.pix2M_pix(xy, m)
    
    def calcMGeo(self):
        '''
Вычисление матрицы для пересчёта пиксельных координат в географические.

Связь пиксельных координат с географическими производится с применением
проективного преобразования. Для вычисления этой матрицы нужно не менее
четырёх изображений в последовательности лежащий не на одной прямой.

Система географических координат используется та, которая указана в exif-данных
файлов изображений или в файле телеметрии.

При вычислении матрицы трансформации ставятся в соответствие пары точек с
координатами: 1) координаты центров каждого изображения в серии на холсте
смонтированного изображения и 2) географические координаты из exif-данных
или телеметрии.

Если в серии менее четырёх изображений или центры имеющиехся изображений лежат
на одной прямой, то вычислить матрицу привязки невозможно и метод возвращает
значение |texttt{None} и выводится сообщение о невозможности создать матрицу
привязки к географической системе координат в стандартный поток вывода.

Матрица привязки к географической системе координат также записывается в
переменную экземпляра класса |texttt{m|_geo}.
        '''
        src=np.array([])
        dst=np.array([])
        for i in self.serial: #Создание пар соответсвующих точек в двух различных системах координат
            b=self.xyImage2xyMontage(i, (i.par['width']/2, i.par['height']/2))
            src=np.append(src, np.array([b[0], b[1]]))
            dst=np.append(dst, np.array([i.par['longitude'], i.par['latitude']]))
        if len(self.serial)<4: #Если в последовательности менее 4 изображений,
            return None #то вернуть пустое значение.
        src=src.reshape(len(self.serial),2)
        dst=dst.reshape(len(self.serial),2)
        try:
            m=transform.estimate_transform('projective', src, dst) #Матрица привязки холста к географическим координатам
            print('Создана привязка ортофотоплана к географической системе координат.')
        except:
            print('Невозможно создать матрицу привязки к географической системе координат.')
            return None
        self.m_geo=m.params
        return self.m_geo
    
    def xy2geo(self,i,xy):
        '''
Пересчёт пиксельных координат изображений в географические.

Входные данные:

|begin{itemize}
|item |texttt{i} -- номер изображения в серии (нумерация начинается от 0);
|item |texttt{(xy)} -- кортеж пиксельных координаты i-го на изображении, для
      которых нужно вычислить географические координаты.
|end{itemize}

Результат: |texttt{(lambda, phi)} -- кортеж действительных чисел с долготой и
           широтой указанного пиксела.

Если ранее вызывался метод |texttt{mGeoToIniFiles}, то для каждого изображения
вычислены матрицы для привязки пиксельных координат к географическим. В этом
случае результат вычисляется через матрицу |texttt{m|_geo}, сохранённую в файле
конфигурации.

Если ранее такая матрица не вычиялялась, то результат будет вычислен через
координаты пиксела изображения на панораме, к которой привязана географическая
система координат.
        '''
        m_Geo=self.serial[i].getM('m_geo')
        if m_Geo is None:
            m=self.calcMGeo()
            if m is None:
                return None
            xy2=self.xyImage2xyMontage(i, xy)
            pl=trMatrix.pix2M_pix(xy2, m)
        else:
            pl=trMatrix.pix2M_pix(xy, m_Geo)
        return pl
    
    def calcMGeoOneImage(self,i):
        '''
Вычисляет матрицу привязки к географической системе координат i-го изображения
в серии. Данной функцией можно пользоваться если к географической системе
координат уже привязана панорама (расчитан атрибут |texttt{m|_geo} методом
|texttt{calcMGeo} |sstr{serialImageserialImagecalcMGeo}).

Вызов этого метода при отсутствии матрицы привязки панорамы к географической
системе координат |texttt{m|_geo} вернёт значение |texttt{None}.

Данным методом следует пользоваться, если |texttt{m|_geo} уже рассчитана и
появляется новое изображение в серии. Тогда можно рассчитать его привязку к
географической системе координат по уже сформированной модели.
        '''
        if self.m_geo is None:
            return None
        tmIm=self.serial[i]
        m=np.matmul(self.m_im2Canvas[i-1],self.serial[i].m_previous)
        self.m_im2Canvas.append(m)
        if tmIm.getM('m_geo') is None:
            tmIm.m_geo=np.matmul(self.m_geo, m)
            tmIm.saveIni()
        return tmIm.m_geo
    
    def mGeoToIniFiles(self):
        '''
Метод вычисляет матрицу привязки к географической системе координат каждого
изображения в серии и записывает её в файлы конфигурации изображений.

Если матрица привязки уже есть, то повторно она не вычисляется.
        '''
        mG=self.calcMGeo() #Вычисляем матрицу привзяки географических координат к холсту
        ii=0
        flag=False
        for i in self.serial:
            if i.getM('m_geo') is None:
                i.m_geo=np.matmul(mG, self.m_im2Canvas[ii])
                i.saveIni()
                flag=True
            ii+=1
        if flag:
            print('Созданы матрицы привязки каждого изображения к географической системе координат')
    
    def listFiles(self):
        '''
Метод возвращает список файлов в серии изображений.
        '''
        r=[]
        for i in self.serial:
            r.append(i.par['filename'])
        return r
    
    def index(self, filename):
        '''
Возвращает индекс файла |texttt{filename} в серии. Если такого файла нет, то
возвращается |texttt{None}.
        '''
        lf=self.listFiles()
        try:
            i=lf.index(filename)
        except:
            i=None
        return i
    
    def saveMontage(self, filename=None):
        '''
Метод записывает панораму в файл |texttt{filename}.

|texttt{filename} может отсутствовать, тогда возможны два варианта:

1. Если серия изображений открывалась с указанием содержащей их папки, тогда
панорама будет записана в файл во внешней папке с именем папки, в которой
находится серия файлов с изображениями, и расширением |texttt{*.jpg}. Например,
серия файлов находилась в папке: |texttt{f1/f2/f3}, тогда панорама будет
записана в файл |texttt{f1/f2/f3.jpg}.

2. Если серия файлов открывалась передачей списка файлов, тогда панорама будет
сохранена в текущую папку с именем |texttt{montage.jpg}. Если такой файл был
ранее, то он будет заменён на новый.

Если панорама ранее не создавалась, то она будет создана.
        '''
        if self.montage is None:
            self.calcMontage()
        if filename is None:
            fn=osp.join(osp.dirname(self.dirFiles),osp.basename(self.dirFiles)+'.jpg') #Создаём имя файла во внешней папке
        else:
            fn=filename
        self.filename=fn
        io.imsave(fn,self.montage) #Запись панорамы в файл res.jpg
        fil, ext=osp.splitext(fn) #Разделяем имя и расширение файла
        fnini=fil+'.ini' #Создаём имя для ini-файла
        iniF=cp.ConfigParser() #Объект для работы с ini-файлом
        iniF.add_section('matrix')
        if not(self.m_geo is None):
            iniF.set('matrix', 'm_geo', np.array2string(self.m_geo,
             separator=',').replace('\n', ''))
        iniF.add_section('params')
        iniF.set('params', 'filename', self.filename)
        iniF.set('params', 'height', str(self.height))
        iniF.set('params', 'width', str(self.width))
        iniF.set('params', 'listfiles', str(self.listFiles()))
        iniF.set('params', 'dir', str(self.dirFiles))
        with open(fnini, "w") as config_file:
            iniF.write(config_file)
        print('Панорама записана в файл: ', fn)
        return True
        
    def tileShape(self):
        '''
Метод вычисляет количество тайлов по высоте и ширине панорамы.

Размер одного тайла 256 на 256 пиксел.

Результатом является кортеж с двумя кортежами:

|begin{itemize}
|item кортеж с количеством тайлов по высоте и ширине, которое необходимо для
      покрытия панорамного изображения;
|item кортеж с размерами тайлового изображения по высоте и ширине, кратные 256.
|end{itemize}
        '''
        shape, xy0=self.unitedShape
        h, w=shape #ширина и высота холста панорамы
        x0, y0=xy0 #Координаты левого-верхнего угла первого изображения на холсте панорамы
        w=int(np.ceil(w/256)*256) #Вычисление ширины
        h=int(np.ceil(h/256)*256) #и высоты холста кратные 256.
        nw=int(w/256) #Вычисление количества тайлов по шинине
        nh=int(h/256) #и высоте.
        self.NTiles=nw*nh
        print('Количество тайлов=',nw,'*',nh,'=',nw*nh,'\nРазмер тайлового покрытия=',(h, w))
        return ((nh, nw), (h, w))
    
    def xyMontageFromTile(self, xyTile):
        '''
Метод вычисляет координаты каждого угла тайла на холсте панорамы.

Исходные данные:

|begin{itemize}
|item |texttt{xyTile} -- кортеж с тайловыми координатами |texttt{x, y}.
|end{itemize}

Результат: кортеж с четыремя элементами, каждый из которых является кортежем
координат $(x, y)$. Первый элемент: координаты левого-верхнего угла; второй --
правого-верхнего; третий -- левого-нижнего; четвёртый -- правого-нижнего.
        '''
        xt, yt=xyTile
        x0=xt*256
        x1=x0+255
        y0=yt*256
        y1=y0+255
        return ((x0,y0),(x1,y0),(x0,y1),(x1,y1))
    
    def xyInTile(self, xy):
        '''
Метод вычисляет в какой тайл попадает пиксел с координатами $x$, $y$.

Исходные данные: кортеж |texttt{x, y} пиксела на холсте тайлового покрытия.

Результат: коортеж с координатами тайла. Метод вернёт координаты даже если они
выходят за пределы тайлового покрытия.
        '''
        return (int(xy[0]/256), int(xy[1]/256))
    
    def xyTileInMontage(self,xyTile,xy):
        '''
Метод пересчитывает пиксельные координаты точки $x$, $y$ на тайле в пиксельные
координаты панорамного изображения.

Исходные данные:

|begin{itemize}
|item{xyTile} -- кортеж координат тайла |texttt{x, y};
|item{xy} -- кортеж пиксельных координат внутри тайла |texttt{x, y}.
|end{itemize}

Результат: кортеж пиксельных координат |texttt{x, y} на холсте панорамы.
        '''
        return (xyTile[0]*256+xy[0], xyTile[1]*256+xy[1])
    
    def intersectionTile(self,i,xyTile,modeIntersection='height'):
        '''
Метод вычисляет пересекается ли |texttt{i}-ое изображение в серии с тайлом, заданным
кортежем координат |texttt{xyTile}.

Исходные данные:

|begin{itemize}
|item |texttt{i} -- индекс изображения в серии, либо экземпляр класса
      |texttt{tmImage};
|item |texttt{xyTile} -- кортеж с тайловыми координатами |texttt{(x, y)};
|item |texttt{modeIntersection} -- учитывает возможный вариант пересечения.
Возможные значения:
    |begin{itemize}
    |item |texttt{'diag'} -- по диагонали;
    |item |texttt{'width'} -- по ширине;
    |item |texttt{'height'} -- по высоте (по умолчанию).
    |end{itemize}
|end{itemize}

Результат: кортеж |texttt{l, f}, где: |texttt{l} -- рассстояние между центрами
тайла и |texttt{i}-го изображения в пикселах на холсте панорамы, |texttt{f} --
|texttt{True} -- если i-ое изображение входит в тайл, иначе |texttt{False}.

Вычисляется расстояние между центрами тайла и изображения на холсте панорамы
$l$ и сравнимается с некоторым отрезком $d$. Если $l<d$, то диагностируется
пересечение изображения с тайлом.

Тайл и изображение могут пересекаться на самом удалённом расстоянии, если
отрезок $d$ проходит по их диагонали (|texttt{modeIntersection='diag'}).
Если отрезок проходит по другому, то может быть диагностировано пересечение,
когда его нет. Ошибка первого рода -- минимальна, второго рода -- максимальна.
В этом случае будет создан пустой тайл. Количество тайлов будет максимально за
счёт появления пустых тайлов.

Нулевая гипотеза -- тайл и изображение пересекаются.

При |texttt{modeIntersection='width'} длина отрезка $d$ вычисляется по ширине
изображения и тайла (они лежат строго по горизонтали), это расстояние меньше
диагонального и будет диагностировано пересечение, если тайл и изображение
лежат на горизонтали или по диагонали.

При |texttt{modeIntersection='height'} длина отрезка $d$ вычисляется по
вертикали, это самое короткое расстояние. При этом ошибка первого рода --
максимальна, второго рода -- минимальна. В тайловое покрытие могут не войти
фрагменты изображений на углах, при этом количество тайлов будет минимально.

В середине тайлового покрытия, где есть перекрытия между исходными
изображениями данный параметр не играет особой роли.
        '''
        if isinstance(i, int):
            i=self.serial[i]
        w=i.par['width']
        h=i.par['height']
        if modeIntersection=='diag':
            t1=self.xyImage2xyMontage(i, (0,0))
            t2=self.xyImage2xyMontage(i, (w,h))
            d=geometriya.dlin(t1, t2)/2+181.02
        elif modeIntersection=='width':
            t1=self.xyImage2xyMontage(i, (0,h/2))
            t2=self.xyImage2xyMontage(i, (w,h/2))
            d=geometriya.dlin(t1, t2)/2+128
        else:
            t1=self.xyImage2xyMontage(i, (w/2,0))
            t2=self.xyImage2xyMontage(i, (w/2,h))
            d=geometriya.dlin(t1, t2)/2+128
        xy=self.xyImage2xyMontage(i, (w/2, h/2)) #Пиксельные координаты центра изображения на холсте панорамы
        xyp=self.xyTileInMontage(xyTile, (128, 128)) #Пиксельная координата центра тайла на холсте панорамы
        l=geometriya.dlin(xy, xyp) #Расстояние между центром тайла и изображения на холсте панорамы
        if l<d:
            return (l, True)
        else:
            return (l, False)
    
    def listImageInTile(self,xyTile,modeIntersection='height'):
        '''
Метод вычисляет список экземпляров класса |texttt{tmImage} в серии, которые
пересекаются с тайлом, имеющим тайловые координаты |texttt{xyTile}.

Исходные данные как в методе |texttt{intersectionTile}
|sstr{serialImageserialImageintersectionTile}.

Результат: список всех изображений, для которых диагностировано пересечение с
тайлом |texttt{xyTile}. Формат тот же, что и в методе
|texttt{intersectionTile}.
        '''
        lIm=[]
        for i in self.serial:
            lf=self.intersectionTile(i, xyTile, modeIntersection)
            if lf[1]:
                lIm.append((lf[0],i))
        return lIm
    
    def nearestImage(self,xyTile,modeIntersection='height'):
        '''
Метод возвращает изображение в серии имеющее самое близкое расстояние между его
центром и центром тайла с координатами |texttt{xyTile}.

Исходные данные как в методе |texttt{intersectionTile}
|sstr{serialImageserialImageintersectionTile}.

Результат: экземпляр класса |texttt{oneImage.tmImage} с изображением.
        '''
        lIm=self.listImageInTile(xyTile,modeIntersection)
        if len(lIm)==0:
            return None
        minL=lIm[0][0]
        im=lIm[0][1]
        for i in lIm:
            if minL>i[0]:
                minL=i[0]
                im=i[1]
        return im
    
    def listTilesInImage(self, im, num=11):
        '''
Метод вычисляет множество тайлов, в которое попадает изображение |texttt{i} в
серии.
        '''
        print('Вычисляются тайлы для изображения: ',im.par['filename'])
        if isinstance(im, int):
            im=self.serial[im]
        x=np.linspace(0,im.par['width'],num)
        y=np.linspace(0,im.par['height'],num)
        st=set()
        for i in x:
            for j in y:
                st.add(self.xyInTile(self.xyImage2xyMontage(im, (i,j))))
        return st
    
    def listTilesInSeries(self, num=11):
        '''
Метод вычисляет множество всех тайлов, которые попадают в изображения серии.

Входной параметр: |texttt{num} -- количество засечек, которые создаются по
ширине и высоте изображения (по умолчанию 11). При 11 засечках создаётся
$11|cdot 11=121$ узел на изображении. Для каждого узла определяется тайл, в
который он попадает. Таким образом определяется список тайлов входящих в
изображение. При увеличении количества засечек увеличивается количество
вычислений. Значение данного параметра следует увеличивать если изображение
слишком большое и между узлами может поместиться тайл.
        '''
        sts=set()
        for i in self.serial:
            a=self.listTilesInImage(i, num)
            sts=set.union(sts,a)
        return sts
    
    def calcTile(self, xyTile, modeIntersection='height'):
        '''
Метод вычисляет изображение тайла с координатами |texttt{xyTile}.

Исходные данные как в методе |texttt{intersectionTile}
|sstr{serialImageserialImageintersectionTile}.

Результат: изображение тайла формата |texttt{ndarray}. Если нет изображений,
которые пересекаются с тайлом, то возвращается |texttt{None}.
        '''
        tMontage=self.xyMontageFromTile(xyTile) #Рассчитываем координаты углов тайла на холсте монтажа
        im=self.nearestImage(xyTile,modeIntersection) #Получаем ближайшее изображение изображение
        if im is None:
            return None
        m=np.linalg.inv(self.m_im2Canvas[self.serial.index(im)])
        #Координаты углов тайла в пространстве панорамы пересчитываем на пространство исходного изображения
        tIm=[trMatrix.pix2M_pix(i, m) for i in tMontage]
        m1=trMatrix.m_Projective(tIm,((0,0),(255,0),(0,255),(255,255))) #Получаем матрицу трансформации изображения в тайл
        imt=transform.warp(im.imCorrect, np.linalg.inv(m1), output_shape=(256, 256))
        return imt
    
    def calcMontageTiles(self, dirTiles=None, metod='tiles', modeIntersection='diag', num=11):
        '''
Вычисление тайловой панорамы.

Исходные данные:

|begin{itemize}
|item |texttt{dirTiles} -- имя папки для сохранения талового покрытия. Если
      |texttt{None}, то рядом с папкой, в которой находится серия изображений
      будет создана папака с именем |texttt{tilesX|_n} для сохранения
      тайлового покрытия, где |texttt{X} -- имя папки с серией изображений, а
      |texttt{n} -- номер. Если создавать тайловое покрытие несколько раз, то
      номер будет увеличиваться (начинается с нуля).
|item |texttt{metod} -- может принимать значения: |texttt{tiles} -- перебор по
      тайлам, |texttt{images} -- перебор по изображениям;
|item |texttt{modeIntersection} -- описан в методе |texttt{intersectionTile}
      |sstr{serialImageserialImageintersectionTile} (используется при
      |texttt{metod='tiles'});
|item |texttt{num} -- описан в методе |texttt{listTilesInSeries}
      |sstr{serialImageserialImagelistTilesInSeries}.
|end{itemize}

Результат: папка на диске с тайловым покрытием. Если можно вычислить матрицу
географической привязки, то она вычисляется и записывается в файл конфигурации.
Файл конфигурации будет находиться вместе с папой тайлового покрытия
|texttt{zn} и иметь имя |texttt{zn.ini}, где |texttt{n} -- номер масштаба.
        '''
        def calcAndSaveTile(i,j):
            nonlocal k, dirTilesZi0Xi0, fn
            dirTilesZi0Xi=osp.join(dirTiles, z,'0','x'+str(i))
            dirTilesZi0Xi0=osp.join(dirTiles, z,'0','x'+str(i),'0')
            r=self.calcTile((i,j),modeIntersection='diag')
            k+=1
            if r is None:
                return False
            fn='y'+str(j)+'.jpg'
            if not(osp.isdir(dirTilesZi0Xi)):
                os.mkdir(dirTilesZi0Xi)
            if not(osp.isdir(dirTilesZi0Xi0)):
                os.mkdir(dirTilesZi0Xi0)
            io.imsave(osp.join(dirTilesZi0Xi0, fn), util.img_as_ubyte(r))
            return True
            
        dirTilesZi0Xi0=''
        fn=''
        (nh, nw), (h, w)=self.tileShape()
        upDir=osp.dirname(self.dirFiles) #Внешняя папка
        if dirTiles is None:
            dirTiles=osp.join(upDir, 'tiles'+osp.basename(self.dirFiles)+'_')
            p=0
            while osp.isdir(dirTiles+str(p)):
                if osp.isdir(dirTiles+str(p)):
                    p+=1
                else:
                    break
        dirTiles+=str(p)
        os.mkdir(dirTiles)
        mhw=max((h,w))
        z='z'+str(int(np.ceil(np.log2(mhw/256)))) #Вычисление уровня z (приближение)
        dirTilesZi=osp.join(dirTiles, z)
        os.mkdir(dirTilesZi)
        dirTilesZi0=osp.join(dirTiles, z,'0')
        os.mkdir(dirTilesZi0)
        k=0
        if metod=='tiles':
            for i in range(nw):
                for j in range(nh):
                    if calcAndSaveTile(i,j):
                        print('Записан тайл:', 'x'+str(i)+'\\'+fn,', ',k,' из ',self.NTiles)
                    else:
                        print('Пропущен тайл',k,'из',self.NTiles,'Нет содержимого.')
        else:
            sts=self.listTilesInSeries(num)
            nT=len(sts)
            for i,j in sts:
                if calcAndSaveTile(i,j):
                    print('Записан тайл:', 'x'+str(i)+'\\'+fn,', ',k,' из ',nT)
                else:
                    print('Пропущен тайл',k,'из',nT,'Нет содержимого.')
        #Записываем файл конфигурации >>>
        if not(self.calcMGeo() is None): #Файл конфигурации есть смысл записывать если есть матрица географической привязки
            iniFn=osp.join(dirTiles, z+'.ini')
            iniF=cp.ConfigParser()
            iniF.add_section('matrix')
            iniF.set('matrix', 'm_geo', np.array2string(self.m_geo,separator=',').replace('\n', ''))
            with open(iniFn, "w") as config_file:
                iniF.write(config_file)
        #<<< Записываем файл конфигурации
        print('Создание тайлов завершено. Тайловое покрытие записано в ', dirTiles)
        return dirTiles

# =============================================================================
#sim=serialImage('f')
#r=sim.calcMontageTiles()
#l=sim.listImageInTile((0,4))
# for i in l:
#     print(i.par['filename'])
# =============================================================================