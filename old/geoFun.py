# -*- coding: utf-8 -*-
'''
Модуль содержит функции для работы с геодезическими системами координат.
'''

import math

radEarth = 6372795 #Радиус Земли в метрах

def dlinaDugiNachAzimut(a,b):
    '''
Функция для вычисления длины дуги и начального азимута между двумя точками.
Взято с сайта http://gis-lab.info/qa/great-circles.html и адаптировано под
функцию.

Используется формула гаверсинусов модифицированная для антиподов:

|begin{equation}|label{def_dlinaDugiNachAzimut}
|Delta\sigma=|arctan|frac{|sqrt{(|cos|phi_2|sin|Delta|lambda)^2+
(|cos|phi_1|sin|phi_2-|sin|phi_1|cos|phi_2|cos|Delta|lambda)^2}}
{|sin|phi_1|sin|phi_2+|cos|phi_1|cos|phi_2|cos|Delta|lambda}.
|end{equation}

Исходные данные:

|begin{itemize}
|item |texttt{a}, |texttt{b} -- точки на сфере. Движение производится из точки
      |texttt{a} в точку |texttt{b}. Каждая точка задана как кортеж (долгота,
      широта).
|end{itemize}

Результат: кортеж, в котором первое значение (индекс 0) -- кратчайшее
расстояние на сфере между точками в метрах; второе -- начальный азимут при
движение из точки |texttt{a} в точку |texttt{b}.
    '''
    #координаты двух точек
    llat1 = a[1]
    llong1 = a[0]
    
    llat2 = b[1]
    llong2 = b[0]
    
    #в радианах
    lat1 = llat1*math.pi/180.
    lat2 = llat2*math.pi/180.
    long1 = llong1*math.pi/180.
    long2 = llong2*math.pi/180.
    
    #косинусы и синусы широт и разницы долгот
    cl1 = math.cos(lat1)
    cl2 = math.cos(lat2)
    sl1 = math.sin(lat1)
    sl2 = math.sin(lat2)
    delta = long2 - long1
    cdelta = math.cos(delta)
    sdelta = math.sin(delta)
    
    #вычисления длины большого круга
    y = math.sqrt(math.pow(cl2*sdelta,2)+math.pow(cl1*sl2-sl1*cl2*cdelta,2))
    x = sl1*sl2+cl1*cl2*cdelta
    ad = math.atan2(y,x)
    dist = ad*radEarth
    
    #вычисление начального азимута
    x = (cl1*sl2) - (sl1*cl2*cdelta)
    y = sdelta*cl2
    z = math.degrees(math.atan(-y/x))
    
    if (x < 0):
        z = z+180.
    
    z2 = (z+180.) % 360. - 180.
    z2 = - math.radians(z2)
    anglerad2 = z2 - ((2*math.pi)*math.floor((z2/(2*math.pi))) )
    angledeg = (anglerad2*180.)/math.pi
    return (dist, angledeg)

#dist, angledeg=dlinaDugiNachAzimut((39,56),(39.1,56.1))
#print('Расстояние >> %.0f' % dist, ' [meters]')
#print('Начальный азимут >> ', angledeg, '[degrees]')