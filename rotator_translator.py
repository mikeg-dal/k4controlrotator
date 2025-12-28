#!/usr/bin/env python3
"""
Rotator Protocol Translator for RT21 Device

This translator bridges between K4-Control rotator software and the RT21
rotator controller. It accepts rotator commands and translates them to
the RT21-specific protocol format.

Key Features:
- Listens on port 6555 for incoming rotator commands
- Maintains persistent TCP connection to RT21 device
- Translates position queries (C command) to RT21 format (AI1\r;)
- Translates move commands to RT21 format (AP0{azimuth}\r;)
- Translates stop commands to RT21 format (;)
- Returns responses in K4-Control format (AZ=nnn\r\n)
"""

import socket
import threading
import re
from datetime import datetime


# ============================================================================
# CONFIGURATION SECTION - Edit these values as needed
# ============================================================================

# RT21 Rotator Device Settings
RT21_IP = "192.168.1.8"
RT21_PORT = 6555

# Translator Listen Port (K4-Control connects here)
LISTEN_PORT = 6555

# ============================================================================


class RotatorProtocolTranslator:
    """Protocol translator for RT21 rotator device"""

    def __init__(self, rt21_ip, rt21_port, listen_port):
        """
        Initialize the translator.

        Args:
            rt21_ip: IP address of RT21 device
            rt21_port: Port of RT21 device
            listen_port: Port to listen for incoming connections
        """
        self.rt21_ip = rt21_ip
        self.rt21_port = rt21_port
        self.listen_port = listen_port
        self.running = False

    def log_message(self, direction, message, protocol=""):
        """
        Log a message with timestamp to console.

        Args:
            direction: Type of message (RECEIVED, SENT, PARSED, etc.)
            message: The message content
            protocol: Protocol identifier (PROGRAM, RT21, TRANSLATOR, etc.)
        """
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        log_entry = f"[{timestamp}] {direction} {protocol}: {repr(message)}"
        print(log_entry)

    def format_rt21_command(self, azimuth):
        """
        Convert azimuth value to RT21 command format.

        Args:
            azimuth: Azimuth value (0-359) or "stop" string

        Returns:
            RT21 formatted command string:
            - Position: AP0{3-digit-azimuth}\r; (e.g., AP0180\r;)
            - Stop: ;
        """
        if isinstance(azimuth, str) and azimuth.lower() == "stop":
            return ";"

        try:
            az_int = int(float(azimuth))
            # Format as 3-digit zero-padded number
            command = f"AP0{az_int:03d}\r;"
            return command
        except (ValueError, TypeError):
            # Default to stop on invalid input
            return ";"

    def parse_incoming_command(self, data):
        """
        Parse incoming command from K4-Control software.

        Supported commands:
        - C: Query current position
        - Mnnn: Move to azimuth nnn (e.g., M030 = move to 30 degrees)
        - S or STOP: Stop rotation
        - ;: Stop rotation

        Args:
            data: Raw bytes received from software

        Returns:
            Parsed command: "query", "stop", or azimuth (int)
            Returns None if command is invalid
        """
        data_str = data.decode('ascii', errors='ignore').strip()
        self.log_message("RECEIVED", data_str, "PROGRAM")

        # Query current position
        if data_str.upper().startswith('C'):
            self.log_message("PARSED", "Command: query", "TRANSLATOR")
            return "query"

        # Move to azimuth command (e.g., M030)
        if data_str.upper().startswith('M'):
            match = re.match(r'^M(\d+)', data_str, re.IGNORECASE)
            if match:
                azimuth = int(match.group(1))
                self.log_message("PARSED", f"Command: move to {azimuth}", "TRANSLATOR")
                return azimuth

        # Stop commands
        if data_str.upper() in ('S', 'STOP') or data_str == ';':
            self.log_message("PARSED", "Command: stop", "TRANSLATOR")
            return "stop"

        self.log_message("PARSED", "No valid command found", "TRANSLATOR")
        return None

    def query_rt21_position(self, rt21_socket):
        """
        Query current azimuth position from RT21 device.

        Sends AI1\r; command to RT21 and parses numeric response.

        Args:
            rt21_socket: Open socket connection to RT21

        Returns:
            Current azimuth (int) or None on error
        """
        try:
            # Send position query command
            command = "AI1\r;"
            rt21_socket.send(command.encode('ascii'))
            self.log_message("SENT", command, "RT21")

            # Receive response (e.g., "030;")
            response = rt21_socket.recv(1024)

            if response:
                response_str = response.decode('ascii', errors='ignore').strip()
                self.log_message("RESPONSE", response_str, "RT21")

                # Extract numeric azimuth from response
                numbers = re.findall(r'\d+', response_str)
                if numbers:
                    azimuth = int(numbers[0])
                    return azimuth

            return None

        except Exception as e:
            self.log_message("ERROR", f"RT21 query failed: {e}", "TRANSLATOR")
            return None

    def send_to_rt21(self, rt21_socket, command):
        """
        Send a command to RT21 device.

        Args:
            rt21_socket: Open socket connection to RT21
            command: RT21 formatted command string

        Returns:
            Response bytes from RT21 or default OK/ERROR response
        """
        try:
            rt21_socket.send(command.encode('ascii'))
            self.log_message("SENT", command, "RT21")

            # Try to receive response with short timeout
            try:
                rt21_socket.settimeout(2)
                response = rt21_socket.recv(1024)
                if response:
                    self.log_message("RESPONSE", response.decode('ascii', errors='ignore'), "RT21")
                    return response
            except socket.timeout:
                pass

            return b"OK\r\n"

        except Exception as e:
            self.log_message("ERROR", f"RT21 communication failed: {e}", "TRANSLATOR")
            return b"ERROR\r\n"

    def handle_client(self, client_socket, client_address):
        """
        Handle incoming connection from rotator software.

        Opens persistent connection to RT21 and processes commands until client disconnects.

        Args:
            client_socket: Socket connection from rotator software
            client_address: Address tuple of client
        """
        self.log_message("CONNECTION", f"Client connected: {client_address}", "PROXY")

        rt21_socket = None
        try:
            # Open persistent connection to RT21 device
            # This connection stays open for the entire session to avoid RT21's
            # one-connection-at-a-time limitation
            rt21_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            rt21_socket.settimeout(5)
            rt21_socket.connect((self.rt21_ip, self.rt21_port))
            self.log_message("CONNECTION", f"Connected to RT21 at {self.rt21_ip}:{self.rt21_port}", "RT21")

            # Process commands until client disconnects
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break

                # Parse incoming command
                command = self.parse_incoming_command(data)

                if command is not None:
                    # Handle position query command
                    if command == "query":
                        current_azimuth = self.query_rt21_position(rt21_socket)
                        if current_azimuth is not None:
                            # K4-Control format: AZ=nnn\r\n
                            program_response = f"AZ={current_azimuth:03d}\r\n"
                            client_socket.send(program_response.encode('ascii'))
                            self.log_message("REPLIED", program_response.strip(), "PROGRAM")
                        else:
                            client_socket.send(b"ERROR\r\n")
                            self.log_message("REPLIED", "ERROR", "PROGRAM")

                    # Handle stop command
                    elif command == "stop":
                        rt21_command = self.format_rt21_command(command)
                        self.send_to_rt21(rt21_socket, rt21_command)
                        client_socket.send(b"OK\r\n")
                        self.log_message("REPLIED", "OK", "PROGRAM")

                    # Handle move to azimuth command
                    else:
                        rt21_command = self.format_rt21_command(command)
                        self.send_to_rt21(rt21_socket, rt21_command)
                        # Send simple OK - let queries report actual position
                        client_socket.send(b"OK\r\n")
                        self.log_message("REPLIED", "OK", "PROGRAM")
                else:
                    # Unknown/invalid command
                    client_socket.send(b"ERROR\r\n")

        except Exception as e:
            self.log_message("ERROR", f"Client handler error: {e}", "PROXY")
        finally:
            # Clean up connections
            if rt21_socket:
                try:
                    rt21_socket.close()
                    self.log_message("CONNECTION", "Disconnected from RT21", "RT21")
                except Exception:
                    pass

            client_socket.close()
            self.log_message("CONNECTION", "Client disconnected", "PROXY")

    def start_server(self):
        """Start TCP server to listen for rotator software connections."""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', self.listen_port))
            server_socket.listen(5)

            print(f"Protocol Translator started on port {self.listen_port}")
            print(f"Forwarding to RT21 at {self.rt21_ip}:{self.rt21_port}")
            print("-" * 60)

            while self.running:
                try:
                    client_socket, client_address = server_socket.accept()
                    # Handle each client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except socket.error as e:
                    if self.running:
                        print(f"Server error: {e}")

        except Exception as e:
            print(f"Failed to start server: {e}")
        finally:
            try:
                server_socket.close()
            except Exception:
                pass

    def start(self):
        """Start the protocol translator service."""
        self.running = True

        print("=== ROTATOR PROTOCOL TRANSLATOR ===")
        print("Converts rotator protocols to RT21 format")
        print()

        # Test RT21 connection at startup
        print("Testing RT21 connection...")
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            test_socket.connect((self.rt21_ip, self.rt21_port))

            # Query position to verify connection
            test_socket.send(b"AI1\r;")
            response = test_socket.recv(1024)
            test_socket.close()

            if response:
                azimuth = response.decode('ascii', errors='ignore').strip()
                print(f"✓ RT21 connected - Current position: {azimuth}")
            else:
                print("⚠️  Warning: RT21 connected but no response")
        except Exception as e:
            print(f"⚠️  Warning: Could not connect to RT21 device - {e}")
        print()

        # Start server in background thread
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()

        # Keep running until user stops with Ctrl+C
        print("Translator running. Press Ctrl+C to stop.")
        print("K4-Control can connect and disconnect as needed.\n")
        try:
            while self.running:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            print("\nTranslator stopped.")


def test_rt21_commands():
    """Test RT21 command formatting (for development/debugging)."""
    translator = RotatorProtocolTranslator(
        rt21_ip=RT21_IP,
        rt21_port=RT21_PORT,
        listen_port=LISTEN_PORT
    )

    test_cases = [
        (0, "AP0000\r;"),
        (35, "AP0035\r;"),
        (180, "AP0180\r;"),
        (359, "AP0359\r;"),
        ("stop", ";"),
        ("STOP", ";"),
    ]

    print("Testing RT21 command formatting:")
    print("-" * 30)

    for input_val, expected in test_cases:
        result = translator.format_rt21_command(input_val)
        status = "✓" if result == expected else "✗"
        print(f"{status} {input_val} -> {repr(result)} (expected: {repr(expected)})")


if __name__ == "__main__":
    import sys

    # Test mode for command formatting
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_rt21_commands()
    else:
        # Normal operation mode - use configuration values from top of file
        translator = RotatorProtocolTranslator(
            rt21_ip=RT21_IP,
            rt21_port=RT21_PORT,
            listen_port=LISTEN_PORT
        )
        translator.start()
