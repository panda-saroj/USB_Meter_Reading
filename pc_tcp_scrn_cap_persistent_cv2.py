import socket

# import _thread
import threading

#New way of implementing Trhead in Python
import concurrent.futures

# from multiprocessing.pool import ThreadPool


import time
import datetime
import os

# Python Package to capture screen
import pyautogui as pg

import cv2

# Python binding to tesseract OCR engine
import pytesseract

from imutils.object_detection import non_max_suppression
import numpy as np

# Use to move files where we have energy capturing issue to a different folder
from shutil import copyfile

# Folder Path to keep captured images, which encounter issues in extracting the energy reading for future investigation
issue_file_folder = "C:\\STFX\\Thesis\\RaspBerryPi\\Screen_Capture\\dq_learning\\file_issues\\"

# Path to tesseract.exe on the Windows machine
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


PC_IP = '141.109.106.5'	 # This Application Server IP
PC_PORT = 54321		  # This Application Server Port


method = cv2.TM_SQDIFF_NORMED


# Function to get energy information from the captured screen passed though image_name
# by using the green circle as the reference point

def get_energy_info_green_circle(image_name):

	# Read the image file
	image = cv2.imread(image_name)
	
	original = image.copy()
	
    # Load the green_circle.jpg stored locally as a separate image 
	green_circle = cv2.imread('green_circle.jpg')
	
	result = cv2.matchTemplate(green_circle, image, method)

	# We want the minimum squared difference
	mn,_,mnLoc,_ = cv2.minMaxLoc(result)

	# Extract the coordinates of our best match for the green_circle
	MPx,MPy = mnLoc

	# print("MPx :", MPx)
	# print("MPy :", MPy)


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
	
	# Convert to Gray
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
	
	return int(energy_reading)
	
	
	
	

# Get Command from Client
def get_data(client_sock, addr):
	print ("\nAccepted connection from " + str(addr))
	
	start_img = None
	end_img = None
  
	try:
	
		# while True:
		#Receive start/stop msg from client 
		while True:
			
			print("Receiving command from client")
			
			data = client_sock.recv(32)
			
			encoding = 'utf-8'
			data = str(data, encoding)
			
			# If the command is capture, Capture the screen
			if(data == "start"):
				
				fileName = str(time.time()) + ".jpg"	
				pg.screenshot(fileName)
				start_img = fileName
				print("Captured start_img :", start_img)
				
			elif(data == "stop"):
				
				fileName = str(time.time()) + ".jpg"
				pg.screenshot(fileName)
				
				end_img = fileName
				print("Captured stop_img :", end_img)
				
	
				try:
					meter_at_start = get_energy_info_green_circle(start_img)
				
				except:
					print("Exception while extracting meter_at_start")
					# Send -1 as energy consumption to notify the client of problem
					client_sock.send(str(-1).encode())
					
					# Move the start_img to the issue_file_folder 
					# to investigate what caused this problem in extracting the energy reading
					dst_file = issue_file_folder + start_img
					copyfile(start_img, dst_file)
					
					# Set meter_at_start to indicate the error
					meter_at_start = None
					
				
				
				try:
					meter_at_end = get_energy_info_green_circle(end_img)
					
					# This should never happen.
					# Keeping it as an error scenario
					# Exception situation while parsing energy from image
					if (meter_at_end < meter_at_start):
					
						# Move the start_img and end_img to the issue_file_folder to investigate separately
						dst_file = issue_file_folder + start_img
						copyfile(start_img, dst_file)
						

						dst_file = issue_file_folder + end_img
						copyfile(end_img, dst_file)
						
						raise ValueError("meter_at_end < meter_at_start")
						
						
				
				except:
					print("Exception while extracting meter_at_end")
					# Send -1 as energy consumption to notify the client of problem
					client_sock.send(str(-1).encode())
					
					# Move the end_img to the issue_file_folder 
					# to investigate what caused this problem in extracting the energy reading
					
					dst_file = issue_file_folder + end_img
					copyfile(end_img, dst_file)
					
					# Set meter_at_end to indicate the error
					meter_at_end = None
		
				if (meter_at_start != None and meter_at_end !=None):
					energy_consumed = meter_at_end - meter_at_start
					
					print("Total Energy Consumed by this client :{} mWh".format(energy_consumed))
					
					encoded_data = str(energy_consumed).encode()
					
					client_sock.send(encoded_data)
				
				
				# Delete the Image files as keeping them will fill up the disk space for long running applications
				os.remove(start_img)
				os.remove(end_img)
			
			
			# return 'success'
			else:
				print("Received End of experiment from client, Exit Thread...")
				client_sock.close()
				return
		
	# except:
	except:
		print("Exception while handling client Request :")
		
		client_sock.close()
		

		

def pc_server():

	# Create a TCP Socket
	
	server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	server_sock.bind((PC_IP, PC_PORT))
	
	print("Server Started waiting for client to connect ")
	
	
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