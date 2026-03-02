#!/usr/bin/env python
"""CDM324 Monitoring Tool - macOS-friendly GUI."""

from configparser import ConfigParser
from stream_visualizer import stream_vis_start
from cdm324_device import cdm324_device, list_serial_ports
from subprocess import run
from tkinter import filedialog, font as tkfont
import tkinter.ttk as ttk
import tkinter as tk
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.ini")

# Colors
BG = "#1e1e2e"
BG_CARD = "#2a2a3d"
FG = "#cdd6f4"
FG_DIM = "#6c7086"
ACCENT = "#89b4fa"
GREEN = "#a6e3a1"
RED = "#f38ba8"
YELLOW = "#f9e2af"
SURFACE = "#313244"


class CDM324MonitorApp(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("CDM324 Speed Sensor")
		self.configure(bg=BG)
		self.resizable(False, False)
		self.bind("<Escape>", lambda e: self.quit())

		# State
		self.no_ports_det_msg_disp = False
		self.disable_access_to_dev = False
		self.connected_to_cdm = False
		self.current_com_ports = []
		self.com_port = ""
		self.device = cdm324_device()

		# Config
		self.config = ConfigParser()
		self.config.read(CONFIG_PATH)
		if not self.config.has_section("main"):
			self.config.add_section("main")
		if not self.config.has_option("main", "update_file"):
			self.config.set("main", "update_file", "")
		if not self.config.has_option("main", "kmh"):
			self.config.set("main", "kmh", "0")
			self.kmh = False
		else:
			self.kmh = self.config.get("main", "kmh") != "0"

		self._build_ui()
		self.com_port_monitor()
		self.speed_query()

	def _build_ui(self):
		pad = {"padx": 16, "pady": 8}

		# --- Connection section ---
		conn_frame = tk.Frame(self, bg=BG_CARD, highlightbackground=SURFACE, highlightthickness=1)
		conn_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))

		tk.Label(conn_frame, text="CONNECTION", font=("Helvetica", 10), fg=FG_DIM, bg=BG_CARD).grid(
			row=0, column=0, sticky="w", padx=12, pady=(10, 2)
		)

		self.status_indicator = tk.Label(conn_frame, text="\u25cf", font=("Helvetica", 14), fg=RED, bg=BG_CARD)
		self.status_indicator.grid(row=1, column=0, sticky="w", padx=(12, 4), pady=4)

		self.connect_status_label = tk.Label(
			conn_frame, text="Not Connected", font=("Helvetica", 13), fg=FG, bg=BG_CARD
		)
		self.connect_status_label.grid(row=1, column=1, sticky="w", pady=4)

		self.com_port_var = tk.StringVar()
		self.com_port_choice = ttk.Combobox(
			conn_frame, textvariable=self.com_port_var, state="readonly", values=[], width=28
		)
		self.com_port_choice.grid(row=1, column=2, padx=(20, 12), pady=4)

		# Bottom padding
		tk.Frame(conn_frame, bg=BG_CARD, height=8).grid(row=2, column=0, columnspan=3)

		# --- Speed display ---
		speed_frame = tk.Frame(self, bg=BG_CARD, highlightbackground=SURFACE, highlightthickness=1)
		speed_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
		speed_frame.grid_columnconfigure(0, weight=1)

		tk.Label(speed_frame, text="SPEED", font=("Helvetica", 10), fg=FG_DIM, bg=BG_CARD).grid(
			row=0, column=0, sticky="w", padx=12, pady=(10, 0)
		)

		self.speed_label = tk.Label(
			speed_frame, text="---", font=("Menlo", 48, "bold"), fg=ACCENT, bg=BG_CARD, anchor="center"
		)
		self.speed_label.grid(row=1, column=0, pady=(4, 4))

		self.unit_label = tk.Label(
			speed_frame, text="km/h" if self.kmh else "mph", font=("Helvetica", 14), fg=FG_DIM, bg=BG_CARD
		)
		self.unit_label.grid(row=2, column=0, pady=(0, 10))

		unit_btn = tk.Button(
			speed_frame, text="Switch Unit", font=("Helvetica", 11),
			fg=BG, bg=ACCENT, activebackground=ACCENT, activeforeground=BG,
			relief="flat", padx=16, pady=4, command=self.switch_speed_units
		)
		unit_btn.grid(row=1, column=1, rowspan=2, padx=(0, 12))

		# --- Tools section ---
		tools_frame = tk.Frame(self, bg=BG_CARD, highlightbackground=SURFACE, highlightthickness=1)
		tools_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=4)

		tk.Label(tools_frame, text="TOOLS", font=("Helvetica", 10), fg=FG_DIM, bg=BG_CARD).grid(
			row=0, column=0, sticky="w", padx=12, pady=(10, 4), columnspan=3
		)

		debug_btn = tk.Button(
			tools_frame, text="Stream Visualizer", font=("Helvetica", 11),
			fg=BG, bg=GREEN, activebackground=GREEN, activeforeground=BG,
			relief="flat", padx=16, pady=6, command=self.start_debug_tool
		)
		debug_btn.grid(row=1, column=0, padx=12, pady=(0, 12))

		# Firmware update row
		self.update_file_path = tk.StringVar(value=self.config.get("main", "update_file"))
		fw_entry = tk.Entry(
			tools_frame, textvariable=self.update_file_path, font=("Menlo", 11),
			bg=SURFACE, fg=FG, insertbackground=FG, relief="flat", width=30
		)
		fw_entry.grid(row=2, column=0, columnspan=2, padx=12, pady=(0, 4), sticky="ew")

		btn_row = tk.Frame(tools_frame, bg=BG_CARD)
		btn_row.grid(row=3, column=0, columnspan=3, padx=12, pady=(0, 12))

		sel_btn = tk.Button(
			btn_row, text="Select Firmware", font=("Helvetica", 11),
			fg=FG, bg=SURFACE, activebackground=SURFACE, activeforeground=FG,
			relief="flat", padx=12, pady=4, command=self.select_update_file
		)
		sel_btn.pack(side="left", padx=(0, 8))

		flash_btn = tk.Button(
			btn_row, text="Flash Firmware", font=("Helvetica", 11),
			fg=BG, bg=YELLOW, activebackground=YELLOW, activeforeground=BG,
			relief="flat", padx=12, pady=4, command=self.flash_update_file
		)
		flash_btn.pack(side="left")

		# --- Log section ---
		log_frame = tk.Frame(self, bg=BG_CARD, highlightbackground=SURFACE, highlightthickness=1)
		log_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(4, 16))

		tk.Label(log_frame, text="LOG", font=("Helvetica", 10), fg=FG_DIM, bg=BG_CARD).grid(
			row=0, column=0, sticky="w", padx=12, pady=(10, 4)
		)

		self.log_output_text = tk.Text(
			log_frame, width=60, height=6, wrap=tk.WORD,
			font=("Menlo", 11), bg=SURFACE, fg=FG, insertbackground=FG,
			relief="flat", borderwidth=0, padx=8, pady=8
		)
		self.log_output_text.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="ew")

	def output_to_console(self, message):
		self.log_output_text.insert("end", message + "\n")
		self.log_output_text.see(tk.END)
		self.update_idletasks()
		self.update()

	def switch_speed_units(self):
		self.kmh = not self.kmh
		self.config.set("main", "kmh", "1" if self.kmh else "0")
		self.unit_label.config(text="km/h" if self.kmh else "mph")
		with open(CONFIG_PATH, "w") as f:
			self.config.write(f)

	def select_update_file(self):
		file_path = filedialog.askopenfilename(filetypes=[("Binary files", "*.bin")])
		if file_path:
			self.update_file_path.set(file_path)
			self.config.set("main", "update_file", file_path)
			with open(CONFIG_PATH, "w") as f:
				self.config.write(f)

	def flash_update_file(self):
		data = run("stm32loader", capture_output=True, shell=True, text=True)
		if "STM32LOADER_SERIAL_PORT" not in data.stderr:
			self.output_to_console("stm32loader isn't installed")
			return

		self.disable_access_to_dev = True
		self.device.disconnect()

		self.output_to_console("Flashing started...")
		data = run(
			"stm32loader -b 115200 -p " + self.com_port + " -e -w -v -s -f F3 " + self.update_file_path.get(),
			capture_output=True, shell=True, text=True,
		)

		if "Verification OK" in data.stdout:
			self.output_to_console("Flashing successful!")
		else:
			self.output_to_console("Flashing failed")

		self.connected_to_cdm = False
		self.disable_access_to_dev = False

	def start_debug_tool(self):
		self.disable_access_to_dev = True
		self.speed_label.config(text="---")
		if self.connected_to_cdm:
			self.device.disconnect()
		self.update_idletasks()
		self.update()

		stream_vis_start(self.com_port)

		self.connected_to_cdm = False
		self.disable_access_to_dev = False

	def speed_query(self):
		if not self.disable_access_to_dev and self.connected_to_cdm:
			try:
				if self.kmh:
					val = self.device.query_kmh()
					self.speed_label.config(text=f"{val:.1f}")
				else:
					val = self.device.query_mph()
					self.speed_label.config(text=f"{val:.1f}")
			except Exception:
				self.speed_label.config(text="---")
		self.after(500, self.speed_query)

	def com_port_monitor(self):
		if not self.connected_to_cdm:
			self.current_com_ports = list_serial_ports()
			self.com_port_choice["values"] = self.current_com_ports

			if len(self.current_com_ports) == 0:
				if not self.no_ports_det_msg_disp:
					self.output_to_console("No serial ports detected")
					self.status_indicator.config(fg=RED)
					self.no_ports_det_msg_disp = True
			else:
				self.no_ports_det_msg_disp = False
				self.com_port_choice.current(0)

				for com_port in self.current_com_ports:
					(self.connected_to_cdm, cdm_version) = self.device.connect(com_port)
					if self.connected_to_cdm:
						self.com_port_choice.set(com_port)
						self.connect_status_label.config(text="Connected")
						self.status_indicator.config(fg=GREEN)
						if isinstance(cdm_version, bytes):
							cdm_version = cdm_version.decode(errors="replace")
						self.output_to_console(cdm_version)
						self.com_port = com_port
						break

		self.after(1000, self.com_port_monitor)


if __name__ == "__main__":
	app = CDM324MonitorApp()
	app.mainloop()
