# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Rotator Protocol Translator** that bridges between K4-Control rotator software and the RT21 rotator controller device. The translator converts K4-Control's rotator commands into the specific RT21 protocol format required by the hardware.

## Architecture

**rotator_translator.py** - Main translator service that:
- Listens on port 6555 for incoming rotator commands from K4-Control
- Maintains a persistent TCP connection to RT21 device (192.168.1.8:6555)
- Parses K4-Control protocol commands
- Translates position queries (`C`) to RT21 query format (`AI1\r;`)
- Translates move commands (`Mnnn`) to RT21 format (`AP0{3-digit-azimuth}\r;`)
- Translates stop commands (`S`, `STOP`, `;`) to RT21 format (`;`)
- Returns responses in K4-Control format (`AZ=nnn\r\n`)

## Key Technical Details

### Connection Management
The translator uses a **persistent socket connection** to the RT21 device. This is critical because the RT21 only accepts one connection at a time. The connection is opened when control software connects and remains open until the software disconnects.

### Protocol Details

**K4-Control Commands (Incoming)**:
- `C` - Query current position
- `Mnnn` - Move to azimuth nnn (e.g., `M030` = move to 30°)
- `S`, `STOP`, `;` - Stop rotation

**RT21 Commands (Outgoing)**:
- **Query Position**: `AI1\r;` → RT21 responds with azimuth (e.g., `030;`)
- **Set Azimuth**: `AP0{3-digit-azimuth}\r;` (e.g., `AP0180\r;` for 180°)
- **Stop**: `;`

**K4-Control Responses (Reply Format)**:
- Position query response: `AZ=nnn\r\n` (e.g., `AZ=030\r\n`)
- Move/Stop acknowledgment: `OK\r\n`
- Error response: `ERROR\r\n`

## Development Commands

### Run the Translator Service
```bash
python3 rotator_translator.py
```
This will:
- Start listening on port 6555 for K4-Control connections
- Test RT21 connection at startup
- Log all command translations to console
- Keep running even when K4-Control disconnects
- Stop only when you press Ctrl+C

### Test RT21 Command Formatting
```bash
python3 rotator_translator.py test
```
Validates command formatting without connecting to RT21 device. Tests azimuth values (0, 35, 180, 359) and stop commands.

## Configuration

### Quick Configuration
Edit the configuration section at the top of [rotator_translator.py](rotator_translator.py#L24-L35):

```python
# RT21 Rotator Device Settings
RT21_IP = "192.168.1.8"      # RT21 device IP address
RT21_PORT = 6555              # RT21 device port

# Translator Listen Port (K4-Control connects here)
LISTEN_PORT = 6555            # Port for K4-Control to connect to
```

### Default Network Settings
- **Listen Port**: 6555 (K4-Control connects here)
- **RT21 Device**: 192.168.1.8:6555
- **Response Format**: K4-Control format (`AZ=nnn\r\n`)

### K4-Control Setup
Configure K4-Control to connect to the translator instead of directly to RT21:
- **IP Address**: `127.0.0.1` (localhost)
- **Port**: `6555` (or whatever you set LISTEN_PORT to)

The translator will forward all commands to the RT21 device. K4-Control can connect and disconnect as needed - the translator keeps running.

## Code Structure

### Main Class: RotatorProtocolTranslator

**Key Methods**:
- `parse_incoming_command(data)` - Parses K4-Control commands (C, Mnnn, S/STOP)
- `format_rt21_command(azimuth)` - Converts azimuth/stop to RT21 format
- `query_rt21_position(rt21_socket)` - Queries RT21 and parses numeric response
- `send_to_rt21(rt21_socket, command)` - Sends command to RT21 device
- `handle_client(client_socket, address)` - Maintains persistent RT21 connection and processes K4-Control commands
- `start_server()` - Starts TCP server on port 6555
- `start()` - Main entry point, tests RT21 connection and starts server
- `log_message(direction, message, protocol)` - Console logging with timestamps

## Customization

### Adding New K4-Control Command Patterns
Edit `parse_incoming_command()` method in [rotator_translator.py](rotator_translator.py):

```python
def parse_incoming_command(self, data):
    data_str = data.decode('ascii', errors='ignore').strip()

    # Add new command pattern here
    if data_str.upper().startswith('NEWCMD'):
        # Parse and return azimuth or command type
        return azimuth

    # Existing patterns: C (query), Mnnn (move), S/STOP (stop)
    ...
```

### Changing RT21 Device IP/Port
Edit the configuration variables at the top of the file ([rotator_translator.py:29-30](rotator_translator.py#L29-L30)):

```python
RT21_IP = "192.168.1.10"      # Change to your RT21 IP
RT21_PORT = 6555              # Change if your RT21 uses a different port
```

### Changing Listen Port
Edit the configuration variable at the top of the file ([rotator_translator.py:33](rotator_translator.py#L33)):

```python
LISTEN_PORT = 6556            # Use different port if needed
```

Then update K4-Control to connect to the new port.

## Troubleshooting

### RT21 Connection Issues
Check the startup output - the translator tests RT21 connection and displays current position if successful.

**Common issues**:
- RT21 not accessible at 192.168.1.8:6555 - verify IP address and network
- Firewall blocking port 6555 - check both incoming and outgoing rules
- Another program already connected to RT21 - RT21 only accepts one connection at a time
- Check console logs for `CONNECTION` and `ERROR` messages

### K4-Control Not Connecting
**Verify K4-Control settings**:
- IP: `127.0.0.1` (localhost)
- Port: `6555`
- Translator must be running before K4-Control connects

### Commands Not Working
All commands are logged to console. Check the logs:
```
[HH:MM:SS.mmm] RECEIVED PROGRAM: 'M090'
[HH:MM:SS.mmm] PARSED TRANSLATOR: 'Command: move to 90'
[HH:MM:SS.mmm] SENT RT21: 'AP0090\r;'
[HH:MM:SS.mmm] REPLIED PROGRAM: 'OK'
```

If you see `PARSED TRANSLATOR: 'No valid command found'`, the command format is not recognized.

### Testing RT21 Directly
Use telnet to verify RT21 communication:
```bash
telnet 192.168.1.8 6555
AI1\r;          # Query position (should return nnn;)
AP0180\r;       # Move to 180 degrees
;               # Stop
```
