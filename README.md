# CDM324 v2 FFT Project
This repository contains the source files created for the making of the CDM324 project described on <a href="https://www.limpkin.fr/index.php?post/2022/03/31/CDM324-Doppler-Motion-Sensor-Backpack%2C-now-with-FFTs%21">limpkin.fr</a>  
The assembly may be purchased here: <a href="https://www.tindie.com/products/stephanelec/cdm324-doppler-speed-sensor/">US shop</a> / <a href="https://lectronz.com/products/cdm324-doppler-speed-sensor">EU shop</a>   
<p align="center">
  <img src="https://github.com/limpkin/cdm324_fft/blob/main/assets/cdm_and_exp.JPG?raw=true" alt="CDM324"/>
</p>

## Repository Structure
- <b>datasheets</b>: main components datasheets
- <b>fw</b>: firmware source files, used in STM32CubeIDE
- <b>kicad</b>: kicad source files for the "backpack" (cdm324_v2) and the "expansion board" (cdm324_exp)
- <b>scripts</b>: python source files for the tools that are used together with the expansion board

## Quick Interfacing Guide (to be completed)
<p align="center">
  <img src="https://www.limpkin.fr/public/cdm324_v2/exp_pinout.png" width="500" alt="CDM324"/>
</p>

<b>UART connection</b>  

To connect the device to an external platform through UART, please use the MCU UART RX/TX pins shown above.   
The baud rate is 1Mbit/s, speed can be queried by sending the 'k' character for km/h or the 'm' character for mph.  
**In case of doubt about the UART connection**, reboot the device: it should output through UART a "CDM324 fw...." string.  
**Make sure your target device can handle 1MBit/s**. If that's not the case, head to the [release section](https://github.com/limpkin/cdm324_fft/releases)https://github.com/limpkin/cdm324_fft/releases to download firmware with different baud rates.
