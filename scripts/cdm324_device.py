import serial
import time


class cdm324_device:
	# Device constructor
	def __init__(self):
		pass
		
	# Disconnect from device
	def disconnect(self):
		self.serial.close()
		
	# Query speed
	def query_kmh(self):
		self.serial.write(b'k')
		return float(self.serial.read_until(b'\n').decode().strip())/10
		
	# Query speed
	def query_mph(self):
		self.serial.write(b'm')
		return float(self.serial.read_until(b'\n').decode().strip())/10
		
	# Connect to device
	def connect(self, COM_port):
		self.com_port = COM_port	

		# Open COM port
		self.serial = serial.Serial(self.com_port, 1000000)
		self.serial.set_buffer_size(rx_size = 1000000, tx_size = 1000000)
		
		# Disable RTS to release RESET
		self.serial.rts = False
		time.sleep(.1)
		
		# Did we get smth from device boot?
		if self.serial.in_waiting > 5:
			# Read input buffer
			self.cdm324_version = self.serial.read(self.serial.in_waiting)
			
			# First bytes may be garbage
			for i in range(len(self.cdm324_version)):
				if self.cdm324_version[i] == ord('C'):
					self.cdm324_version = self.cdm324_version[i:-2].decode('utf-8')
					break
			
			# Return
			return (True, self.cdm324_version)
		else:
			return (False, "")