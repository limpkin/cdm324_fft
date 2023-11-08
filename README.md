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

<b>Unit change to km/h</b>  
To change the speed readout to km/h, connect the "PA1/KMH" pad to the "GND" pad in the above diagram.  

<b>UART connection</b>  

**The UART connection is 3V3 and NOT 5V.**  
To connect the device to an external platform through UART, please use the MCU UART RX/TX pins shown above.   
The baud rate is **1Mbit/s**, speed **can be queried** by **sending the 'k'** character for km/h or the 'm' character for mph.  
**In case of doubt about the UART connection, reboot the device**: it should output "CDM324 fw....".  
**Make sure your host device can handle 1MBit/s**. If that's not the case, head to the [release section](https://github.com/limpkin/cdm324_fft/releases) to download firmware with different UART baud rates.  
Finally, if you still have doubts about the UART connection, you may connect one of your host platform GPIO to the nRESET pin and reset the CDM324 device at your host platform boot.  

## Reflashing the Device

In the unlikely case you want to reflash your device with another firmware, you may either use the [GUI present in this repository](https://github.com/limpkin/cdm324_fft/tree/main/scripts) or the [stm32loader python module](https://pypi.org/project/stm32loader/) directly :  

> pip install stm32loader
> 
... then with the expansion board connected to the device (**as it uses RTS/CTS signals to control the MCU nRESET and BOOT0 pins**):  

> stm32loader -b 115200 -p  com_port -e -w -v -s -f F3 updatefile.bin

If you don't have the companion expansion board, you may use [STM32 Flash loader](https://www.st.com/en/development-tools/flasher-stm32.html) after performing the following toggling sequence:  
- tie nRESET to GND  
- bring BOOT0 to 3V3_OUT  
- release nRESET  
- releae BOOT0  

## Sample Arduino code to fetch speed from device

```c
#define RESET_PIN 2

void issue_cdm324_reset()
{  
  bool string_received = false;
  char receive_buffer[50];
  int index = 0;

  // 20ms reset
  pinMode(RESET_PIN, OUTPUT);
  delay(20);
  pinMode(RESET_PIN, INPUT);

  // get string
  while (string_received == false)
  {
    if (Serial1.available() > 0)
    {
      char bla = Serial1.read();
      receive_buffer[index++] = bla;
      if (bla == '\n')
        string_received = true;
    }
  }
  receive_buffer[index] = 0;

  Serial.println("Received from the CDM324:");
  Serial.println(receive_buffer);
}

void setup() 
{
  // Local console
  Serial.begin(115200);
  Serial.println("Hello there!");

  // To the CDM324
  Serial1.begin(57600);

  // Reset CDM324
  pinMode(RESET_PIN, INPUT);
  digitalWrite(RESET_PIN, LOW);
  issue_cdm324_reset();
}

float get_speed(bool kmh)
{
  if (kmh == true)
  {
    // Query km/h * 10
    Serial1.print('k');
  }
  else
  {
    // Query mph * 10
    Serial1.print('m');
  }  
  while(Serial1.available() == 0);
  float speed = Serial1.parseFloat();
  return (speed / 10);
}

void loop()
{
  Serial.println(get_speed(false));
  delay(500);
}
```
