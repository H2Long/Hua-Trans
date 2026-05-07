"""Build script for TranslateTor using PyInstaller."""

import PyInstaller.__main__
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    os.path.join(base_dir, 'main.py'),
    '--name=黄花梨之译',
    '--onefile',
    '--windowed',
    '--add-data=core:core',
    '--add-data=gui:gui',
    '--hidden-import=PyQt5',
    '--hidden-import=PyQt5.QtWidgets',
    '--hidden-import=PyQt5.QtCore',
    '--hidden-import=PyQt5.QtGui',
    '--hidden-import=PyQt5.QtSvg',
    '--hidden-import=fitz',
    '--hidden-import=pytesseract',
    '--hidden-import=pynput',
    '--hidden-import=pyperclip',
    '--hidden-import=PIL',
    '--hidden-import=requests',
    '--noconfirm',
    '--clean',
])
