# -*- coding: utf-8 -*-
"""
Создан 19 июня 2023

Автор: Петросян Я.В.

Модуль содержит функции для решения геометрических задач.
"""

import math

def dlin(a,b):
    '''
Функция вычисляет длину отрезка $ab$.

Исходные данные: |texttt{a}, |texttt{b} -- кортежи координат в многомерном
пространстве.

Результат: скаляр расстояния между точками $a$ и $b$.
    '''
    return math.sqrt(sum([(i-j)**2 for i,j in zip(a,b)]))

def uravnPryamoy(a,b):
    '''
Функция рассчитывает коэффициенты уравнения прямой, проходящей через две точки.

Исходные данные: |texttt{a}, |texttt{b} -- две точки на плоскости, координаты
которых являются кортежами: |texttt{(x, y)}.

Через эти две точки можно провести прямую заданную уравнением:

$$
Ax+By+C=0
$$

Функция вычисляет коэффициенты $A$, $B$, $C$, которые возвращаются как кортеж
|texttt{A, B, C}.

Для вычислений используется формула:

$$
(y_1-y_2)x+(x_2-x_1)y+(x_1y_2-x_2y_1)=0
$$
    '''
    return (a[1]-b[1], b[0]-a[0], a[0]*b[1]-b[0]*a[1])

def peresechPryamyh(a,b):
    '''
Функция вычисляет точку пересечения прямых |texttt{a} и |texttt{b}, если они
заданы уравнениями вида $Ax+By+C=0$.

Исходные данные: |texttt{a}, |texttt{b} -- кортежи коэффициентов уравнения
прямой |texttt{(A, B, C)}

Результат: кортеж координат точки пересечения прямых |texttt{(x, y)}. Если
прямые параллельны, то возвращается |texttt{None}.

Для вычисления используются формулы:

$$
x=|frac{B_aC_b-B_bC_a}{A_aB_b-A_bB_a}
$$

$$
y=|frac{A_aC_b-A_bC_a}{A_aB_b-A_bB_a}
$$
    '''
    ch=a[0]*b[1]-b[0]*a[1]
    if ch==0:
        return None
    else:
        x=(a[1]*b[2]-b[1]*a[2])/ch
        y=(a[0]*b[2]-b[0]*a[2])/ch
    return (x, y)

def peresechOtrezkov(a,b):
    '''
Функция вычисляет пересекаются отрезки на плоскости или нет.

Исходные данные: |texttt{a}, |texttt{b} -- отрезки заданные как кортежи
координат их концов. Например, отрезок |texttt{a}, может быть задан как
|texttt{((a1x, a1y),(a2x, a2y))}, где |texttt{a1x}, |texttt{a1y} -- координаты
первого конца отрезка |texttt{a}, |texttt{a2x}, |texttt{a2y} -- координаты
второго конца. Так же и с отрезком |texttt{b}.

Результат: если кортеж из двух действительных чисел, то это точка пересечения
отрезков. Если |texttt{None}, то отрезки не пересекаются.
    '''
    pa=uravnPryamoy(a[0], a[1])
    pb=uravnPryamoy(b[0], b[1])
    t=peresechPryamyh(pa, pb)
    if t is None:
        return None
    else:
        #Если точка пересечения лежит внутри отрезка a, то она лежит и внутри отрезка b, значит они пересекаются
        if a[0][0]<=t[0]<=a[1][0] and a[0][1]<=t[1]<=a[1][1]:
            return t
        else:
            return None