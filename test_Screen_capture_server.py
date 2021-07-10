import time
import socket


SCR_PC_IP = '141.109.106.5'	 # Screen Capture Server IP
SCR_PC_PORT = 54321		  # Screen Capture Server Port


# Client function to connect to TCP Server 
def persistent_connection(ip, port):
	
	# Establish TCP Connection
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((ip, port))
	
	return sock 


scr_cap_sock = persistent_connection(SCR_PC_IP, SCR_PC_PORT)

print("Starting For Loop")

for i in range(5):
	
	
	scr_cap_sock.send(b"start")
	print("Sent start")
	#Keep the cpu idle for exec_time
	time.sleep(5)

	
	scr_cap_sock.send(b"stop")
	print("Sent stop")
	
	
	energy = float(scr_cap_sock.recv(32))
	print("Energy consumed sleeping :", energy)
    
    
scr_cap_sock.send(b"exit")	

scr_cap_sock.close()
	
	


