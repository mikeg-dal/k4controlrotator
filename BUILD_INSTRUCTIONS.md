# Building the Rotator Translator macOS App

This guide explains how to build a double-clickable macOS application from the Rotator Translator Python script.

## Prerequisites

- macOS 10.13 or later
- Python 3.6 or later installed
- pip3 (comes with Python 3)

## Quick Build (Recommended)

Simply run the build script:

```bash
./build_app.sh
```

This script will:
1. Check if Python 3 is installed
2. Install py2app if needed
3. Build the .app bundle
4. Place it in the `dist/` folder

## Manual Build

If you prefer to build manually:

1. **Install py2app:**
   ```bash
   pip3 install py2app
   ```

2. **Build the app:**
   ```bash
   python3 setup.py py2app
   ```

3. **Find your app:**
   The app will be created at: `dist/Rotator Translator.app`

## Installing the App

1. Open Finder and navigate to the `dist/` folder
2. Drag `Rotator Translator.app` to your Applications folder
3. Double-click the app to run it

**First run on macOS Catalina or later:**
- You may see a security warning
- Go to System Preferences → Security & Privacy
- Click "Open Anyway" to allow the app to run
- This only needs to be done once

## Using the App

When you double-click the app:
1. A Terminal window will open
2. The translator will start and display connection logs
3. You'll see the message "Translator running. Press Ctrl+C to stop."
4. K4-Control can now connect to `127.0.0.1:6555`

**To stop the app:**
- Press `Ctrl+C` in the Terminal window, or
- Close the Terminal window

## Configuration

Before building, you can edit the configuration in [rotator_translator.py](rotator_translator.py):

```python
# RT21 Rotator Device Settings
RT21_IP = "192.168.1.8"      # Change to your RT21 IP
RT21_PORT = 6555              # Change if needed

# Translator Listen Port
LISTEN_PORT = 6555            # Port for K4-Control to connect to
```

After changing configuration, rebuild the app using `./build_app.sh`

## Troubleshooting

### "py2app: command not found"
Run: `pip3 install py2app`

### "Permission denied" when running build_app.sh
Run: `chmod +x build_app.sh`

### App won't open - "damaged or can't be verified"
This is a macOS security feature for unsigned apps:
1. Go to System Preferences → Security & Privacy
2. Click "Open Anyway"

Alternatively, run this command:
```bash
xattr -cr "dist/Rotator Translator.app"
```

### Clean build (start fresh)
```bash
rm -rf build dist
./build_app.sh
```

## App Details

- **App Name:** Rotator Translator
- **Bundle ID:** com.k4control.rotatortranslator
- **Version:** 1.0.0
- **Size:** ~25-30 MB (includes Python runtime)
- **Location after build:** `dist/Rotator Translator.app`

## Distribution

To share the app with others:
1. Build the app using the instructions above
2. Compress the app: Right-click `Rotator Translator.app` → Compress
3. Share the resulting `Rotator Translator.app.zip` file
4. Recipients can unzip and drag to their Applications folder

**Note:** Recipients will need to allow the app in Security & Privacy settings on first run (macOS Catalina+), since the app is not code-signed.

## Advanced: Code Signing (Optional)

To avoid security warnings, you can code-sign the app with an Apple Developer account:

```bash
codesign --deep --force --sign "Developer ID Application: Your Name" "dist/Rotator Translator.app"
```

This requires:
- Apple Developer Program membership ($99/year)
- Developer ID certificate installed in Keychain

## File Structure

```
k4controlrotator/
├── rotator_translator.py    # Main Python script
├── setup.py                  # py2app configuration
├── build_app.sh             # Build script (recommended)
├── requirements.txt          # Python dependencies
├── BUILD_INSTRUCTIONS.md    # This file
├── build/                   # Temporary build files (created during build)
└── dist/                    # Output folder (created during build)
    └── Rotator Translator.app  # Your finished app!
```

## Support

For issues with:
- **The translator functionality:** See [CLAUDE.md](CLAUDE.md)
- **Building the app:** Check Troubleshooting section above
- **py2app issues:** Visit https://py2app.readthedocs.io/
