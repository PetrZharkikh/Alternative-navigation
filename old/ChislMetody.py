# -*- coding: utf-8 -*-
"""
Created on Mon Jul 26 17:12:27 2021

@author: Петросян

Некоторые численные методы.
"""

class ExChislMetod(Exception): pass

def bisection(a,b,f,e=0.001):
    #Метод половинного деления для решения нелинейных уравнений одной переменной.
    if f(a)*f(b)>0:
        raise ExChislMetod('Нет решения уравнения на отрезке ['+str(a)+','+str(b)+']')
    while b-a>=e:
        x=(a+b)/2
        a,b=(a,x) if f(a)*f(x)<0 else (x,b)
    return (a+b)/2