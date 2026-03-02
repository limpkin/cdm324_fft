#!/usr/bin/env python
"""CDM324 Speed Sensor - Real-time Stream Visualizer (matplotlib version)."""

from cdm324_device import list_serial_ports
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec
from scipy import fft
import numpy as np
import platform
import datetime
import serial
import sys

# Number of ADC samples sent by the device
NUM_SAMPLES = 1024
# ADC sampling rate
SAMPLING_RATE = 35714
# Spectrogram length in # of FFTs
SPECTROGRAM_LENGTH = 500
# How many fft bins are sent by the platform
FFT_LGTH_TRUNCATE = 150

# Array for computing signal average
adc_average_array = [0] * 20
adc_average_fill_index = 0


class CDM324Visualizer:
	def __init__(self, com_port):
		self.serial_initialized = False
		self.ser = serial.Serial(com_port, 1000000)
		if platform.system() == "Windows":
			self.ser.set_buffer_size(rx_size=1000000, tx_size=1000000)
		self.ser.rts = False
		self.skip_low_freqs = False

		# Time axis
		self.times = np.linspace(0.0, float(NUM_SAMPLES) / SAMPLING_RATE, num=NUM_SAMPLES)
		# Speed axis (km/h)
		self.speeds = np.linspace(0.0, SAMPLING_RATE * 0.02262295 * FFT_LGTH_TRUNCATE / NUM_SAMPLES, num=FFT_LGTH_TRUNCATE)
		# Spectrogram data
		self.spectrogram_data = np.zeros((FFT_LGTH_TRUNCATE, SPECTROGRAM_LENGTH))

		# Setup plots
		self.fig = plt.figure(figsize=(12, 9))
		self.fig.suptitle("CDM324 Speed Sensor", fontsize=14, fontweight="bold")
		gs = GridSpec(3, 1, figure=self.fig, hspace=0.4)

		# Plot 1: Raw ADC
		self.ax_time = self.fig.add_subplot(gs[0])
		self.ax_time.set_title("Device Raw ADC Values")
		self.ax_time.set_xlabel("Time (seconds)")
		self.ax_time.set_ylabel("ADC word")
		self.ax_time.set_ylim(0, 5000)
		self.line_time, = self.ax_time.plot(self.times, np.zeros(NUM_SAMPLES), color="blue", linewidth=0.5)

		# Plot 2: Speed Spectrum
		self.ax_spectrum = self.fig.add_subplot(gs[1])
		self.ax_spectrum.set_title("Device Computed Speed Spectrum")
		self.ax_spectrum.set_xlabel("Speed (km/h)")
		self.ax_spectrum.set_ylabel("Amplitude")
		self.ax_spectrum.set_ylim(0, 300000)
		self.line_spectrum, = self.ax_spectrum.step(self.speeds, np.zeros(FFT_LGTH_TRUNCATE), color="red", linewidth=0.5)

		# Plot 3: Spectrogram
		self.ax_spectrogram = self.fig.add_subplot(gs[2])
		self.ax_spectrogram.set_title("Speed Spectrogram")
		max_time = float(SPECTROGRAM_LENGTH * NUM_SAMPLES) / SAMPLING_RATE
		max_speed = float(SAMPLING_RATE * 0.02262295 * FFT_LGTH_TRUNCATE / NUM_SAMPLES)
		self.img = self.ax_spectrogram.imshow(
			self.spectrogram_data,
			aspect="auto",
			origin="lower",
			extent=[0, max_time, 0, max_speed],
			cmap="hot",
			vmin=0,
			vmax=130,
		)
		self.ax_spectrogram.set_xlabel("Time (seconds)")
		self.ax_spectrogram.set_ylabel("Speed (km/h)")

		# Keyboard shortcuts via matplotlib key_press_event
		self.fig.canvas.mpl_connect("key_press_event", self._on_key)

	def _on_key(self, event):
		if event.key == "h":
			self.skip_low_freqs = not self.skip_low_freqs
			if self.skip_low_freqs:
				self.ser.write(b'h')
				print("Low frequencies removed")
			else:
				self.ser.write(b'l')
				print("Low frequencies restored")
		elif event.key == "r":
			self.serial_initialized = False
			print("Resynchronizing...")

	def _init_stream(self):
		# Stop stream, empty buffer
		self.ser.write(b's')
		import time
		time.sleep(0.1)
		self.ser.read(self.ser.in_waiting)
		self.ser.reset_input_buffer()
		# Start stream
		self.ser.write(b'a')
		self.serial_initialized = True

	def update(self, frame):
		global adc_average_array, adc_average_fill_index

		if not self.serial_initialized:
			self._init_stream()

		# Skip frames if buffer backs up
		if self.ser.in_waiting > 2 * (NUM_SAMPLES * 2 + FFT_LGTH_TRUNCATE * 4):
			self.ser.read(NUM_SAMPLES * 2 + FFT_LGTH_TRUNCATE * 4)
			print(str(datetime.datetime.now()) + ": skipping one frame")

		# Read raw ADC data (NUM_SAMPLES uint16_t)
		raw_bytes = self.ser.read(NUM_SAMPLES * 2)
		raw_adc_data = np.frombuffer(raw_bytes, dtype=np.dtype("<u2"))
		self.line_time.set_ydata(raw_adc_data)

		# Read FFT data (FFT_LGTH_TRUNCATE float32)
		fft_bytes = self.ser.read(FFT_LGTH_TRUNCATE * 4)
		serial_fft_data = np.frombuffer(fft_bytes, dtype=np.dtype("<f4"))
		self.line_spectrum.set_ydata(serial_fft_data)

		# Update average
		adc_average_array[adc_average_fill_index] = np.mean(raw_adc_data)
		adc_average_fill_index += 1
		if adc_average_fill_index == len(adc_average_array):
			adc_average_fill_index = 0

		# Compute FFT for spectrogram
		normalized_data = np.array(raw_adc_data, dtype=np.float64)
		normalized_data = (normalized_data - np.mean(adc_average_array)) / 2048
		spectrum = np.abs(fft.fft(normalized_data))[:NUM_SAMPLES // 2]
		spectrum = spectrum[:FFT_LGTH_TRUNCATE]

		# Update spectrogram
		self.spectrogram_data = np.hstack(
			(self.spectrogram_data[:, 1:], spectrum.reshape(-1, 1))
		)
		self.img.set_data(self.spectrogram_data)

		return self.line_time, self.line_spectrum, self.img

	def start(self):
		self.anim = animation.FuncAnimation(
			self.fig, self.update, interval=10, blit=False, cache_frame_data=False
		)
		plt.tight_layout()
		plt.show()
		self.ser.close()


def stream_vis_start(com_port):
	vis = CDM324Visualizer(com_port)
	vis.start()


if __name__ == "__main__":
	available_ports = list_serial_ports()

	if len(available_ports) == 0:
		print("No serial ports found")
		sys.exit(0)

	print("Opening", available_ports[0])
	print("Press 'h' in the plot window to toggle low-frequency removal")
	print("Press 'r' in the plot window to resynchronize data")

	stream_vis_start(available_ports[0])
