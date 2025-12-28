"""
py2app setup script for Rotator Protocol Translator

This script creates a standalone macOS .app bundle that users can double-click.
The app will open a Terminal window showing all the translator logs.

Build the app:
    python3 setup.py py2app

The app will be created in: dist/Rotator Translator.app
"""

from setuptools import setup

APP = ['rotator_translator.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,  # Add an .icns file path here if you create an icon
    'plist': {
        'CFBundleName': 'Rotator Translator',
        'CFBundleDisplayName': 'Rotator Translator',
        'CFBundleGetInfoString': 'RT21 Rotator Protocol Translator',
        'CFBundleIdentifier': 'com.k4control.rotatortranslator',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Rotator Protocol Translator',
        'LSMinimumSystemVersion': '10.13.0',
        # Keep the app running in Terminal mode so users can see logs
        'LSBackgroundOnly': False,
        'LSUIElement': False,
    },
    # Use includes instead of packages for built-in modules
    'includes': ['socket', 'threading', 're', 'datetime'],
    # Exclude unnecessary packages to reduce size and avoid dependency issues
    'excludes': ['tkinter', 'unittest', 'test', 'setuptools', 'pkg_resources'],
    'semi_standalone': False,
    'site_packages': False,
}

setup(
    name='Rotator Translator',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
