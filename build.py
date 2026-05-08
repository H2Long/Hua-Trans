"""Build script for TranslateTor using PyInstaller — cross-platform."""

import sys
import os
import PyInstaller.__main__

base_dir = os.path.dirname(os.path.abspath(__file__))

hidden_imports = [
    '--hidden-import=PyQt5',
    '--hidden-import=PyQt5.QtWidgets',
    '--hidden-import=PyQt5.QtCore',
    '--hidden-import=PyQt5.QtGui',
    '--hidden-import=PyQt5.QtSvg',
    '--hidden-import=fitz',
    '--hidden-import=pytesseract',
    '--hidden-import=pyperclip',
    '--hidden-import=PIL',
    '--hidden-import=requests',
]

# Platform-specific hidden imports
if sys.platform == "linux":
    hidden_imports.append('--hidden-import=Xlib')
elif sys.platform == "win32":
    hidden_imports.append('--hidden-import=pynput')

args = [
    os.path.join(base_dir, 'main.py'),
    '--name=黄花梨之译',
    '--onefile',
    '--windowed',
    '--add-data=core:core',
    '--add-data=gui:gui',
    *hidden_imports,
    '--noconfirm',
    '--clean',
]

PyInstaller.__main__.run(args)
