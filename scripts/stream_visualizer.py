#!/usr/bin/env python
# Needed to configure graphics library
# Requires Enthought Tool Suite 4
from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

# Data processing functions
from numpy import zeros, linspace, short, fromstring, hstack, transpose
from scipy import fft

# Enthought library imports
from chaco.default_colormaps import hot
from enable.api import Component, ComponentEditor
from traits.api import HasTraits, Instance
from traitsui.api import Item, Group, View, Handler
from pyface.timer.api import Timer
from time import sleep

# Chaco imports
from chaco.api import Plot, ArrayPlotData, HPlotContainer, VPlotContainer

# Imports for core program
import numpy as np
import keyboard
import serial
import array
import sys

# Number of ADC samples sent by the device
NUM_SAMPLES = 1024
# ADC sampling rate
SAMPLING_RATE = 35714
# Spectogram length in # of FFTs
SPECTROGRAM_LENGTH = 500
# How many fft bins are sent by the platform
FFT_LGTH_TRUNCATE = 150

# Array for computing signal average
adc_average_array = [0]*20
adc_average_fill_index = 0


def _create_plot_component(obj):
	# Time Series plot
	times = linspace(0.0, float(NUM_SAMPLES) / SAMPLING_RATE, num=NUM_SAMPLES)
	obj.time_data = ArrayPlotData(time=times)
	empty_amplitude = zeros(NUM_SAMPLES)
	obj.time_data.set_data("amplitude", empty_amplitude)
	obj.time_plot = Plot(obj.time_data)
	obj.time_plot.plot(("time", "amplitude"), name="Time", color="blue")
	obj.time_plot.padding = 50
	obj.time_plot.title = "Device Raw ADC Values"
	obj.time_plot.index_axis.title = "Time (seconds)"
	obj.time_plot.value_axis.title = "ADC word"
	time_range = list(obj.time_plot.plots.values())[0][0].value_mapper.range
	time_range.low = 0
	time_range.high = 5000
	
	# Setup the device spectrum plot
	frequencies = linspace(0.0, SAMPLING_RATE*0.02262295*FFT_LGTH_TRUNCATE/NUM_SAMPLES, num=FFT_LGTH_TRUNCATE)
	obj.device_spectrum_data = ArrayPlotData(frequency=frequencies)
	empty_amplitude = zeros(FFT_LGTH_TRUNCATE)
	obj.device_spectrum_data.set_data("amplitude", empty_amplitude)
	obj.device_spectrum_plot = Plot(obj.device_spectrum_data)
	obj.device_spectrum_plot.plot(("frequency", "amplitude"), name="Device Spectrum", color="red", renderstyle='hold')
	obj.device_spectrum_plot.padding = 50
	obj.device_spectrum_plot.title = "Device Computed Speed Spectrum"
	plot_rends = list(obj.device_spectrum_plot.plots.values())
	spec_range = plot_rends[0][0].value_mapper.range
	spec_range.low = 0.0
	spec_range.high = 300000.0
	obj.device_spectrum_plot.index_axis.title = "Speed (km/h)"
	obj.device_spectrum_plot.value_axis.title = "Amplitude"
	
	# Setup the spectrum plot
	frequencies = linspace(0.0, FFT_LGTH_TRUNCATE, num=FFT_LGTH_TRUNCATE)
	obj.spectrum_data = ArrayPlotData(frequency=frequencies)
	empty_amplitude = zeros(NUM_SAMPLES // 2)
	obj.spectrum_data.set_data("amplitude", empty_amplitude)
	obj.spectrum_plot = Plot(obj.spectrum_data)
	obj.spectrum_plot.plot(("frequency", "amplitude"), name="Spectrum", color="red", renderstyle='hold')
	obj.spectrum_plot.padding = 50
	obj.spectrum_plot.title = "Spectrum"
	plot_rends = list(obj.spectrum_plot.plots.values())
	spec_range = plot_rends[0][0].value_mapper.range
	spec_range.low = 0.0
	spec_range.high = 200.0
	obj.spectrum_plot.index_axis.title = "Frequency (Hz)"
	obj.spectrum_plot.value_axis.title = "Amplitude"

	# Spectrogram plot
	spectrogram_data = zeros((FFT_LGTH_TRUNCATE, SPECTROGRAM_LENGTH))
	obj.spectrogram_plotdata = ArrayPlotData()
	obj.spectrogram_plotdata.set_data("imagedata", spectrogram_data)
	spectrogram_plot = Plot(obj.spectrogram_plotdata)
	max_time = float(SPECTROGRAM_LENGTH * NUM_SAMPLES) / SAMPLING_RATE
	max_freq = float(SAMPLING_RATE*0.02262295*FFT_LGTH_TRUNCATE/NUM_SAMPLES)
	spectrogram_plot.img_plot(
		"imagedata",
		name="Spectrogram",
		xbounds=(0, max_time),
		ybounds=(0, max_freq),
		colormap=hot,
	)
	range_obj = spectrogram_plot.plots["Spectrogram"][0].value_mapper.range
	range_obj.high = 130
	range_obj.low = 0.0
	spectrogram_plot.title = "Speed Spectrogram"
	obj.spectrogram_plot = spectrogram_plot

	container = VPlotContainer()
	container.add(obj.time_plot)
	container.add(obj.device_spectrum_plot)
	#container.add(obj.spectrum_plot)
	container.add(spectrogram_plot)
	return container

counter = 0
skip_low_freqs = False
# HasTraits class that supplies the callable for the timer event.
class TimerController(HasTraits):
	def onTimer(self, *args):
		global platform_serial_initialized
		global counter
		#print(counter)
		counter += 1
		
		# Debug choices
		sync_prot = True
		raw_data_fetch = True
		fft_data_fetch = True
		
		# keyboard shortcut pressed?
		if keyboard.is_pressed("h") and skip_low_freqs == False:
			platform_serial.write(b'h')
		elif keyboard.is_pressed("r"):
			platform_serial_initialized = False
	
		# Did we initialize our serial port?
		if platform_serial_initialized == False:
			if sync_prot:
				# Stop stream, empty buffer
				platform_serial.write(b's')
				sleep(.1)
				platform_serial.read(platform_serial.in_waiting)
				platform_serial.reset_input_buffer()
				# Start stream
				platform_serial.write(b'a')
				platform_serial_initialized = True
			else:
				platform_serial.read(platform_serial.in_waiting)				
	
		#sys.stdout.write(str(platform_serial.in_waiting) + " ")
		# Get raw adc data (NUM_SAMPLES uint16_t)
		if raw_data_fetch:
			raw_adc_data = platform_serial.read(NUM_SAMPLES*2)
			dt = np.dtype(np.uint16)
			dt = dt.newbyteorder('<')
			raw_adc_data = np.frombuffer(raw_adc_data, dtype=dt)
		
		# Get FFT data
		if fft_data_fetch:
			serial_fft_data = platform_serial.read(FFT_LGTH_TRUNCATE*4)
			dt = np.dtype(np.single)
			dt = dt.newbyteorder('<')
			serial_fft_data = np.frombuffer(serial_fft_data, dtype=dt)
			#print(max(serial_fft_data))
			self.device_spectrum_data.set_data("amplitude", serial_fft_data)
		
		# debug
		if False:
			np.set_printoptions(threshold=np.inf)
			arrayyy = np.frombuffer(raw_adc_data, dtype=dt)
			print("Min: " + str(np.min(arrayyy)) + ", max: " + str(np.max(arrayyy)) + " at index " + " " . join(str(i) for i in np.where(arrayyy == np.max(arrayyy))))
		
		if raw_data_fetch:
			# Update average
			global adc_average_array
			global adc_average_fill_index
			adc_average_array[adc_average_fill_index] = np.mean(raw_adc_data)
			adc_average_fill_index += 1
			if adc_average_fill_index == len(adc_average_array):
				adc_average_fill_index = 0		
		
			# Compute fft
			normalized_data = np.array(raw_adc_data, copy=True)  
			normalized_data = (normalized_data - np.mean(adc_average_array)) / 2048
			spectrum = abs(fft.fft(normalized_data))[: NUM_SAMPLES // 2]
			spectrum = spectrum[:FFT_LGTH_TRUNCATE]
			time = raw_adc_data
		
			self.spectrum_data.set_data("amplitude", spectrum)
			self.time_data.set_data("amplitude", time)
			spectrogram_data = self.spectrogram_plotdata.get_data("imagedata")
			spectrogram_data = hstack(
				(spectrogram_data[:, 1:], transpose([spectrum]))
			)
			self.spectrogram_plotdata.set_data("imagedata", spectrogram_data)
		
		# redraw
		self.spectrum_plot.request_redraw()


# ============================================================================
# Attributes to use for the plot view.
size = (1280, 1024)
title = "CDM324 Speed Sensor"

class CDM324Handler(Handler):
	def closed(self, info, is_ok):
		"""Handles a dialog-based user interface being closed by the user.
		Overridden here to stop the timer once the window is destroyed.
		"""
		info.object.timer.Stop()
		platform_serial.close()


class CDM324(HasTraits):
	timer = Instance(Timer)
	plot = Instance(Component)
	controller = Instance(TimerController, ())
	
	traits_view = View(
		Group(Item("plot", editor=ComponentEditor(size=size), show_label=False),orientation="vertical",),
		resizable=True,
		title=title,
		width=size[0],
		height=size[1],
		handler=CDM324Handler,)

	def _plot_default(self):
		return _create_plot_component(self.controller)

	def edit_traits(self, *args, **kws):
		# Start up the timer! We should do this only when the demo actually
		# starts and not when the demo object is created.
		self.timer = Timer(10, self.controller.onTimer)
		return super(CDM324, self).edit_traits(*args, **kws)

	def configure_traits(self, *args, **kws):
		# Start up the timer! We should do this only when the demo actually
		# starts and not when the demo object is created.
		self.timer = Timer(10, self.controller.onTimer)
		return super(CDM324, self).configure_traits(*args, **kws)

def stream_vis_start(com_port):
	global platform_serial_initialized
	global platform_serial
	
	platform_serial_initialized = False
	platform_serial = serial.Serial(com_port, 1000000)
	platform_serial.set_buffer_size(rx_size = 1000000, tx_size = 1000000)
	platform_serial.rts = False
	
	# Start GUI
	popup = CDM324()
	popup.configure_traits()	

if __name__ == "__main__":
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
			
	# Did we find anything?
	if len(available_ports) == 0:
		print("No COM ports found")
		sys.exit(0)

	# Debug info
	print("Opening" , available_ports[0])
	print("Press 'h' to remove low frequencies")
	print("Press 'r' in case data gets misaligned")

	# Start main program
	stream_vis_start(available_ports[0])