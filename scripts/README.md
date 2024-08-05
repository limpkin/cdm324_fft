# Python Scripts
Unfortunately these scripts are only compatible with Windows at the moment. 
Pull requests are however welcome!

## Requirements - Windows
1) install c++ build tools from https://visualstudio.microsoft.com/visual-cpp-build-tools/, select :
- C++ CMake tools for Windows (it will select MSVC 2022)
- Testing tools core features
- Windows 10 SDK

2) Create python virtual environment and activate it
```
python -m venv venv
venv\Scripts\activate
```

3) Install the required python modules
```
pip install -r requirements.txt
```

4) Load the GUI
```
python .\_start.py
```
