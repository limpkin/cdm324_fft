# Python Scripts

GUI tool for flashing, monitoring and configuring the CDM324 sensor board.

## Requirements - macOS

1) Create python virtual environment and activate it
```bash
python3 -m venv venv
source venv/bin/activate
```

2) Install the required python modules
```bash
pip install -r requirements.txt
```

3) Load the GUI
```bash
python3 _start.py
```

Or simply double-click `start.command`.

## Requirements - Windows

1) Install C++ build tools from https://visualstudio.microsoft.com/visual-cpp-build-tools/, select:
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
