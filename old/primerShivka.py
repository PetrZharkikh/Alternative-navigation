# -*- coding: utf-8 -*-
"""
Created on Mon May 22 19:58:15 2023

@author: peter
"""

import serialImage as sim
import skimage.io as io

print('Запущен процесс создания монтажа')
sim=sim.serialImage('f2\\')
r=sim.calcMontage()
io.imsave('montag.jpg', r)
print('Записан файл montag.jpg')
