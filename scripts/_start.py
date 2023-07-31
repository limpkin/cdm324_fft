from time import gmtime, strftime, localtime, sleep
from configparser import ConfigParser
from stream_visualizer import *
from cdm324_device import *
from subprocess import run
try:
	from tkinter import filedialog
	import tkFont as tkfont
	import Tkinter as tk
	import ttk
except ImportError:
	from tkinter import font as tkfont
	from tkinter import filedialog
	import tkinter.ttk as ttk
	import tkinter as tk
import serial
import cmath
import math
import sys


class CDM324MonitorApp(tk.Tk):
	def scan_available_com_ports(self):
		# Create a list of possible com ports
		ports = ['COM%s' % (i + 1) for i in range(2,256)]

		# Try to open them to see which ones are actually available
		available_ports = []
		for port in ports:
			try:
				s = serial.Serial(port)
				s.close()
				available_ports.append(port)
			except (OSError, serial.SerialException):
				pass
				
		# Return what we got
		return available_ports
		
	def select_update_file(self):
		# Query user
		file_path = filedialog.askopenfilename(filetypes=[("Binary files", "*.bin")])
		
		# Update string and store config
		self.update_file_path.set(file_path)
		self.config.set("main", "update_file", file_path)
		with open('config.ini', 'w') as f:
			self.config.write(f)
	
	def switch_speed_units(self):
		if self.kmh == False:
			self.refresh_speed_button.config(text="Switch to MPH")
			self.config.set("main", "kmh", "1")
			self.kmh = True
		else:
			self.refresh_speed_button.config(text="Switch to km/h")
			self.config.set("main", "kmh", "0")
			self.kmh = False
		with open('config.ini', 'w') as f:
			self.config.write(f)			
			
	def flash_update_file(self):		
		# Check for stm32loader presence
		data = run("stm32loader", capture_output=True, shell=True, text=True)
		if "STM32LOADER_SERIAL_PORT" not in data.stderr:
			self.output_to_console("stm32loader isn't installed")
			return
			
		# Disconnect from device
		self.disable_access_to_dev = True
		self.device.disconnect()
			
		# Start flashing!
		self.output_to_console("Flashing started...")
		data = run("stm32loader -b 115200 -p " + self.com_port + " -e -w -v -s -f F3 " + self.update_file_path.get(), capture_output=True, shell=True, text=True)
		
		# Success?
		if "Verification OK" in data.stdout:
			self.output_to_console("Flashing succesfull!")
		else:
			self.output_to_console("Flashing failed")
		
		# Reconnect to device
		self.connected_to_cdm = False
		self.disable_access_to_dev = False
		
	def start_debug_tool(self):
		# Disable access to com port
		self.disable_access_to_dev = True
		self.speed_label.config(text="")
		self.device.disconnect()
		
		# Force UI update
		self.update_idletasks()
		self.update()
		
		# Launch debug tool
		stream_vis_start(self.com_port)
				
		# Reconnect to device
		self.connected_to_cdm = False
		self.disable_access_to_dev = False
		
	def speed_query(self):
		if self.disable_access_to_dev == False and self.connected_to_cdm != False:
			if self.kmh == False:
				self.speed_label.config(text=str(self.device.query_mph()) + " MPH")
			else:
				self.speed_label.config(text=str(self.device.query_kmh()) + " km/h")
				
		# Launch the same routine later
		self.after(500, self.speed_query)
		
	def com_port_monitor(self):
		# No need if already connected
		if self.connected_to_cdm == False:
			# Get a list of available COM ports
			self.current_com_ports = self.scan_available_com_ports()
			self.com_port_choice['values'] = self.current_com_ports
			
			# Try to connect to device
			if len(self.current_com_ports) == 0:
				if self.no_ports_det_msg_disp == False:
					self.output_to_console("No COM ports detected!")			
					self.combostyle.theme_use('combostyle_red') 
					self.no_ports_det_msg_disp = True
			else:
				# Set default value
				self.com_port_choice.current(0)
				
				# Go through the list
				for com_port in self.current_com_ports:
					# Connection attempt
					(self.connected_to_cdm, cdm_version) = self.device.connect(com_port)
					
					# Success?
					if self.connected_to_cdm:
						# Set correct COM port selection, output to console received string
						self.com_port_choice.current(self.current_com_ports.index(com_port))	
						self.connect_status_label.config(text="Connected")
						self.combostyle.theme_use('combostyle_green') 
						self.output_to_console(cdm_version)
						self.com_port = com_port
						break
		
		# Launch the same routine in a second
		self.after(1000, self.com_port_monitor)
		
	def output_to_console(self, message):
		self.log_output_text.insert("end", message + "\r\n")
		self.log_output_text.see(tk.END)
		
		# Force UI update
		self.update_idletasks()
		self.update()
	
	def __init__(self, *args, **kwargs):
		tk.Tk.__init__(self, *args, **kwargs)
		self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold")
		self.configure(background='LightSteelBlue2')
		self.title("CDM324 Monitoring Tool")
		self.resizable(0,0)
		self.focus_set()
		self.bind("<Escape>", lambda e: e.widget.quit())
		
		# Vars
		self.no_ports_det_msg_disp = False
		self.disable_access_to_dev = False
		self.connected_to_cdm = False
		self.config = ConfigParser()
		self.current_com_ports = []
		self.com_port = ""
		
		# Read settings		
		self.config.read("config.ini")
		if self.config.has_section("main") == False:
			self.config.add_section('main')
		if self.config.has_option("main", "update_file") == False:
			self.config.set("main", "update_file", "")
		if self.config.has_option("main", "kmh") == False:
			self.config.set("main", "kmh", "0")
			self.kmh = False
		else:
			self.kmh = False if self.config.get('main', 'kmh') == "0" else True
		
		# Vars
		self.monitoring_bool = False
		self.log_file_opened = False
		self.laser_temp_word = -1
		self.log_counter = 0
		self.polarity = 0
		
		# combobox style		
		self.combostyle = ttk.Style()
		self.combostyle.theme_create('combostyle_red', parent='alt', settings = {'TCombobox': {'configure': {'selectbackground': 'blue', 'fieldbackground': 'red', 'background': 'green' }}})
		self.combostyle.theme_create('combostyle_green', parent='alt', settings = {'TCombobox': {'configure': {'selectbackground': 'blue', 'fieldbackground': 'green', 'background': 'green' }}})
		
		# Top left: connection status & com port list
		self.connect_status_label = tk.Label(self, text="Not Connected", background="LightSteelBlue2", font=tkfont.Font(family='Helvetica', size=12, weight=tkfont.BOLD), anchor="e")
		self.connect_status_label.grid(row=0, column=0, pady=(5,2), padx=5)
		self.com_port_choice = ttk.Combobox(self, state="readonly", values=self.current_com_ports, width=20)
		self.com_port_choice.grid(row=0, column=1, pady=(0,2), padx=5)
		self.com_port_choice.set("")
		
		# Update file path
		self.update_file_path = tk.StringVar()
		self.update_file_path.set(self.config.get('main', 'update_file'))
		self.update_file_path_entry = ttk.Entry(self, width="46", textvariable=self.update_file_path)
		self.update_file_path_entry.grid(row=1, column=0, columnspan=2, pady=(5,2), padx=5)		
				
		# Update file action buttons
		self.select_file_button = tk.Button(self, text="Select Firmware", font=tkfont.Font(family='Helvetica', size=9), width="18", command=lambda:[self.select_update_file()])
		self.select_file_button.grid(row=2, column=0, pady=(5,2), padx=(15,15))		
		self.update_fw_button = tk.Button(self, text="Update Firmware", font=tkfont.Font(family='Helvetica', size=9), width="18", command=lambda:[self.flash_update_file()])
		self.update_fw_button.grid(row=2, column=1, pady=(5,2), padx=(15,15))	
		
		# Speed display
		self.speed_label = tk.Label(self, text="", background="LightSteelBlue2", font=tkfont.Font(family='Helvetica', size=26, weight=tkfont.BOLD), anchor="e")
		self.speed_label.grid(row=0, column=2, columnspan=2, rowspan=2, pady=(5,2), padx=5)
				
		# Speed action buttons
		self.refresh_speed_button = tk.Button(self, text="Switch to km/h", font=tkfont.Font(family='Helvetica', size=9), width="18", command=lambda:[self.switch_speed_units()])
		if self.kmh != False:
			self.refresh_speed_button.config(text="Switch to MPH")
		self.refresh_speed_button.grid(row=2, column=2, pady=(5,2), padx=(15,15))		
		self.update_fw_button = tk.Button(self, text="Start Debug Tool", font=tkfont.Font(family='Helvetica', size=9), width="18", command=lambda:[self.start_debug_tool()])
		self.update_fw_button.grid(row=2, column=3, pady=(5,2), padx=(15,15))	
				
		# Log output
		self.log_output_text = tk.Text(self, width=80, height=8, wrap=tk.WORD)
		self.log_output_text.grid(row=3, column=0, columnspan=4, pady=(15,20), padx = 20)
		
		# Blank cdm324 device
		self.device = cdm324_device()
		
		# Trigger com ports monitor to trigger connection
		self.com_port_monitor()
		
		# Trigger speed query
		self.speed_query()


if __name__ == "__main__":
	app = CDM324MonitorApp()
	app.mainloop()