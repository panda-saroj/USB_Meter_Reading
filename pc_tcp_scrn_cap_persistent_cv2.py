import socket

# import _thread
import threading

#New way of implementing Trhead in Python
import concurrent.futures

# from multiprocessing.pool import ThreadPool


import time
import datetime
import os

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




PC_IP = '192.168.2.113'  # Server IP
PC_PORT = 54321       # Server Port

timestamp_type = "tt"

def get_time(t_type):
	
	if(t_type == "tt"):
		return time.time()
	
	if(t_type == "ut"):
		return datetime.datetime.utcnow().timestamp()




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


	# # Step 2: Get the size of the template. This is the same size as the match.
	# trows,tcols = small_image.shape[:2]

	# # Step 3: Draw the rectangle on large_image
	# cv2.rectangle(image, (MPx,MPy),(MPx+tcols,MPy+trows),(0,0,255),1)

	# # Display the original image with the rectangle around the match.
	# cv2.imshow('output',image)

	# # The image is only displayed if we call this
	# cv2.waitKey(0)

	energy_area = original[MPy + 4 :MPy + 25, MPx + 135 : MPx + 197]
	
	# (H, W) = energy_area.shape[:2]

	# print("Height :", H)
	# print("Width :", W)
	
	# cv2.imshow('energy_area',energy_area)
	# cv2.waitKey(0)
	
	
	# image preprocessing to improve the accuracy of Tesseract - rescale, Blur, Thresholding
	# Rescale 
	# energy_area = cv2.resize(energy_area, None, fx=3, fy=3, interpolation=cv2.INTER_AREA)
	energy_area = cv2.resize(energy_area, None, fx=3, fy=3)
	
	# cv2.imshow('Rescale energy_area',energy_area)
	# cv2.waitKey(0)
	
	energy_area = cv2.cvtColor(energy_area, cv2.COLOR_BGR2GRAY)
	
	#Blur
	energy_area = cv2.GaussianBlur(energy_area, (3, 3), 0)
	
	# cv2.imshow('Blur energy_area',energy_area)
	# cv2.waitKey(0)
	
	# Thresholding
	# ret,energy_area = cv2.threshold(energy_area,150,190,43)
	ret,energy_area = cv2.threshold(energy_area,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
	
	
	# cv2.imshow('Thres energy_area',energy_area)
	# cv2.waitKey(0)
	# cv2.destroyAllWindows()
	
	# Extract the Energyreading from the image
	energy_reading = pytesseract.image_to_string(energy_area, config='-c tessedit_char_whitelist=0123456789 -l eng' )
	
	print("energy_reading :", energy_reading)
	
	# energy_reading = ((energy_reading.split()[0]).strip('o')).strip('O')
	
	# Ignore any extra charecters extracted by tesseract
	# To handle 0 being sometimes interpreted as o, explicitly replace o as 0
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
	
	return int(energy_reading)
	
	
	
	

# Get Command from Client
def get_data(client_sock, addr):
	print ("\nAccepted connection from " + str(addr))
	
	start_img = None
	end_img = None
  
	try:
		#Receive msg from client till receive exit from client
		while True:
			data = client_sock.recv(32)
			
			encoding = 'utf-8'
			data = str(data, encoding)
			
			# If the command is capture, Capture the screen
			if(data == "start"):
				
				fileName = str(get_time(timestamp_type)) + ".jpg"	
				pg.screenshot(fileName)
				start_img = fileName
				print("Captured start_img :", start_img)
				
			elif(data == "end"):
				
				fileName = str(get_time(timestamp_type)) + ".jpg"
				pg.screenshot(fileName)
				
				end_img = fileName
				print("Captured end_img :", end_img)
				
			# elif(data == "exit"):		
				# break
			else:
				break
	
	
		try:
			meter_at_start = get_energy_info_green_circle(start_img)
		
		except:
			print("Exception while extracting meter_at_start")
			# Send -1 as energy consumption to notify the client of problem
			client_sock.send(str(-1).encode())
			client_sock.close()
			dst_file = issue_file_folder + start_img
			
			copyfile(start_img, dst_file)
			return
		
		
		# meter_at_start = get_energy_info(start_img)
		# print("meter_at_start :", meter_at_start)
		try:
			meter_at_end = get_energy_info_green_circle(end_img)
			
			# Exception situation while parsing energy from image
			if (meter_at_end < meter_at_start):
				dst_file = issue_file_folder + start_img
				copyfile(start_img, dst_file)
				
				dst_file = issue_file_folder + end_img
				copyfile(end_img, dst_file)
				
				raise ValueError("meter_at_end < meter_at_start")
				
				
		
		except:
			print("Exception while extracting meter_at_end")
			# Send -1 as energy consumption to notify the client of problem
			client_sock.send(str(-1).encode())
			client_sock.close()
			dst_file = issue_file_folder + end_img
			
			copyfile(end_img, dst_file)
			return
		# meter_at_end = get_energy_info(end_img)
		
		# print("meter_at_end :", meter_at_end)
		
		energy_consumed = meter_at_end - meter_at_start
		
		# Exception situation while parsing energy from image
		if (energy_consumed > 10000):
			dst_file = issue_file_folder + start_img
			copyfile(start_img, dst_file)
			
			dst_file = issue_file_folder + end_img
			copyfile(end_img, dst_file)
			
			raise ValueError("Unusual case energy_consumed > 100")
		
		print("Total Energy Consumed by this client :{} mWh".format(energy_consumed))
		
		encoded_data = str(energy_consumed).encode()
		
		client_sock.send(encoded_data)
		client_sock.close()
		
		# Delete the Image files as keeping them will fill up the disk space for long running applications
		os.remove(start_img)
		os.remove(end_img)
		
		
		# return 'success'
		
	except:
		print("Exception while handling client Request")
		# Send -1 as energy consumption to notify the client of problem
		client_sock.send(str(-1).encode())
		client_sock.close()
		
		# Move the 
		
		# return 'failure'
	
		

def pc_server():

	# Create a TCP Socket
	
	server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	server_sock.bind((PC_IP, PC_PORT))
	
	print("Server Started waiting for Raspberry client to connect ")
	
	
	while True:
		server_sock.listen(10)
	  
		client_sock,address = server_sock.accept()
		
		try:
			
						
			with concurrent.futures.ThreadPoolExecutor() as executor:
				thread = executor.submit(get_data, client_sock, address)
			# with concurrent.futures.ProcessPoolExecutor() as executor:
				# executor.submit(get_data, client_sock, address)
			
			# thread = threading.Thread(target=get_data, args=(client_sock, address, ))
			# thread.start()
			
			# _thread.start_new_thread( get_data, (client_sock, address, ) )
			# thread = threading.Thread(target=get_data, args = [client_sock, address])
			# thread.start()
			

		except:
			print ("Error: unable to start thread")
  
		# return_value = future.result()
		# print("Thread returned :", return_value)
  

# Start the Server
pc_server()