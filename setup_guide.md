# Rotator Protocol Translator Setup Guide

## Overview
This translator bridges between your antenna rotator program and the RT21 device by converting various rotator protocols to the RT21 format you defined.

## RT21 Protocol 
```javascript
// Azimuth command: AP0{3-digit-azimuth}\r;
// Examples:
//   0°   -> "AP0000\r;"
//   35°  -> "AP0035\r;"
//   180° -> "AP0180\r;"

// Stop command: ";"
```

## Quick Start


### 1. Start the Translator
```bash
python3 rotator_translator.py
```
- Listens on port 6555 (same as RT21)
- Converts incoming commands to RT21 format
- Forwards to RT21 at 192.168.1.8:6555

### 3. Configure Your Rotator Program
Change your program's target from:
- **From**: `192.168.1.8:6555` 
- **To**: `127.0.0.1:6555` (translator)

### 4. Test the Translation
```bash
python3 test_translator.py
```
Sends various command formats to verify translation works.

## Supported Input Formats

The translator recognizes these command patterns:

### Direct Numbers
```
35        -> AP0035\r;
180       -> AP0180\r;
0         -> AP0000\r;
```

### Yaesu GS-232 Style
```
AZ90      -> AP0090\r;
AZ270     -> AP0270\r;
M180      -> AP0180\r;
```

### Hamlib Style
```
P 45      -> AP0045\r;
\set_pos 90 -> AP0090\r;
```

### Stop Commands
```
S         -> ;
STOP      -> ;
stop      -> ;
;         -> ;
```

## Network Setup Options

### Option 1: Redirect Program (Recommended)
- Configure program to connect to `127.0.0.1:6555`
- Translator forwards to RT21 at `192.168.1.8:6555`
- No network changes needed

## Troubleshooting

### Connection Issues
```bash
# Test RT21 directly
telnet 192.168.1.8 6555

# Send test command
AP0000\r;
```

### Firewall
Ensure ports are open:
- Incoming: 6555 (or chosen port)
- Outgoing: 6555 to 192.168.1.8

### Different RT21 Device
Change IP/port in the constructor:
```python
translator = RotatorProtocolTranslator(
    rt21_ip="192.168.1.10",    # Your RT21 IP
    rt21_port=6555,            # Your RT21 port
    listen_port=6555           # Port to listen on
)
```

## Files Created

1. **rotator_translator.py** - Main translator service

