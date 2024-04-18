# Python Scripts
Unfortunately these scripts are only compatible with Windows at the moment. 
Pull requests are however welcome!

## Import notice
If you follow the steps below, you'll likelly get an error during the chaco installation in step 2.  
This is due to a new issue tracked here: https://github.com/enthought/chaco/issues/910
Before performing the steps below, follow these steps: https://github.com/enthought/chaco/issues/910#issuecomment-2065335367

## Requirements - Windows
1) install c++ build tools from https://visualstudio.microsoft.com/visual-cpp-build-tools/, select :
- C++ CMake tools for Windows (it will select MSVC 2022)
- Testing tools core features
- Windows 10 SDK

2) Install python and the required modules
```
pip install pyqt5 chaco stm32loader pyserial scipy keyboard
```
