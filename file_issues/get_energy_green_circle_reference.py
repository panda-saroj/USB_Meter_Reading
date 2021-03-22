import socket

import _thread
import threading

#New way of implementing Trhead in Python
import concurrent.futures

# from multiprocessing.pool import ThreadPool


import time
import datetime

import pyautogui as pg

import cv2
import pytesseract

from imutils.object_detection import non_max_suppression
import numpy as np

# Use to move files where we have energy capturing issue to a different folder
from shutil import copyfile

issue_file_folder = "C:\\STFX\\Thesis\\RaspBerryPi\\Screen_Capture\\dq_learning\\file_issues\\"

# Path to tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


method = cv2.TM_SQDIFF_NORMED

def get_energy_info_green_circle(image_name):

	# Read the image file
	image = cv2.imread(image_name)
	
	original = image.copy()
	
	green_circle = cv2.imread('green_circle.jpg')
	
	result = cv2.matchTemplate(green_circle, image, method)

	# We want the minimum squared difference
	mn,_,mnLoc,_ = cv2.minMaxLoc(result)

	# Draw the rectangle:
	# Extract the coordinates of our best match
	MPx,MPy = mnLoc

	# print("MPx :", MPx)
	# print("MPy :", MPy)


	# Step 2: Get the size of the template. This is the same size as the match.
	trows,tcols = green_circle.shape[:2]

	# Step 3: Draw the rectangle on large_image
	cv2.rectangle(image, (MPx,MPy),(MPx+tcols,MPy+trows),(0,0,255),1)

	# Display the original image with the rectangle around the match.
	cv2.imshow('output',image)

	# The image is only displayed if we call this
	cv2.waitKey(0)

	energy_area = original[MPy + 4 :MPy + 25, MPx + 135 : MPx + 197]
	
	# (H, W) = energy_area.shape[:2]

	# print("Height :", H)
	# print("Width :", W)
	
	cv2.imshow('energy_area',energy_area)
	cv2.waitKey(0)
	
	
	# image preprocessing to improve the accuracy of Tesseract - rescale, Blur, Thresholding
	# Rescale 
	# energy_area = cv2.resize(energy_area, None, fx=3, fy=3, interpolation=cv2.INTER_AREA)
	energy_area = cv2.resize(energy_area, None, fx=3, fy=3)
	
	cv2.imshow('Rescale energy_area',energy_area)
	cv2.waitKey(0)
	
	energy_area = cv2.cvtColor(energy_area, cv2.COLOR_BGR2GRAY)
	
	#Blur
	energy_area = cv2.GaussianBlur(energy_area, (3, 3), 0)
	
	cv2.imshow('Blur energy_area',energy_area)
	cv2.waitKey(0)
	
	# Thresholding
	# ret,energy_area = cv2.threshold(energy_area,160,200,cv2.ADAPTIVE_THRESH_MEAN_C)
	
	# energy_area = cv2.adaptiveThreshold(energy_area,255,cv2.ADAPTIVE_THRESH_MEAN_C,\
            # cv2.THRESH_BINARY, 11, 2)
			
	# ret,energy_area = cv2.threshold(energy_area,150,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
	ret,energy_area = cv2.threshold(energy_area,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
	
	# ret,energy_area = cv2.threshold(energy_area,0,255,50)
	
	cv2.imshow('Thres energy_area',energy_area)
	cv2.waitKey(0)
	cv2.destroyAllWindows()
	
	# Extract the Energyreading from the image
	energy_reading = pytesseract.image_to_string(energy_area)
	
	print("type(energy_reading) :", type(energy_reading))
	
	print("energy_reading :", energy_reading)
	
	# energy_reading = ((energy_reading.split()[0]).strip('o')).strip('O')
	
	energy_reading = (energy_reading.split()[0]).replace('o', '0')
	
	energy_reading = energy_reading.replace('O', '0')
	
	# # Sometimes 7 is being extracted as /7. Replace / by blank
	# # Sometimes 7 is being extracted as /. In that case Replace / by blank
	# if(len(energy_reading) > 5):
		# energy_reading = energy_reading.replace('/', '')
	# else:
		# energy_reading = energy_reading.replace('/', '7')
	
	# # Sometimes 7 is being extracted as /7. Replace /7 by 7
	# # Sometimes 7 is being extracted as /. In that case Replace / by 7
	if(len(energy_reading) > 5):
		energy_reading = energy_reading.replace('/7', '7')
	# else:
	energy_reading = energy_reading.replace('/', '7')
	
	
	print("cv2.THRESH_BINARY ", cv2.THRESH_BINARY)
	print("cv2.THRESH_OTSU ", cv2.THRESH_OTSU)
	# print(energy_reading.split())
	
	# print("type(energy_reading.split()[0]) :", type(energy_reading.split()[0]))
	
	# str = 'O7774'
	
	# print("float(str) :", float(str))
	
	# print([int(s) for s in energy_reading.split() if s.isdigit()])
	
	# energy_reading = int(s) for s in energy_reading.split() if s.isdigit()
	
	return int(energy_reading)
	
	
energy = get_energy_info_green_circle("1608314387.958925.jpg")

print("energy :", energy)