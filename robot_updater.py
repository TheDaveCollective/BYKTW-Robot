#!/usr/bin/env python3
"""
Steam Robot Local Updater
Downloads and flashes firmware directly from GitHub repository
No PlatformIO installation required - uses esptool directly
"""

import os
import sys
import json
import hashlib
import subprocess
import urllib.request
import urllib.error
import tempfile
import time
import serial.tools.list_ports
from datetime import datetime

class RobotUpdater:
    def __init__(self, debug=False, dry_run=False):
        self.debug = debug
        self.dry_run = dry_run
        self.github_repo = "TheDaveCollective/BYKTW-Robot"
        self.github_branch = "main"
        self.base_url = f"https://raw.githubusercontent.com/{self.github_repo}/refs/heads/{self.github_branch}"
        self.temp_dir = None
        self.esptool_path = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️ ",
            "DEBUG": "🔍"
        }.get(level, "")
        
        if level == "DEBUG" and not self.debug:
            return
            
        print(f"[{timestamp}] {prefix} {message}")
        
    def print_banner(self):
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                Steam Robot Local Updater                    ║")
        print("║             Update robot firmware from GitHub               ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()
        
    def download_file(self, url, description="file"):
        """Download a file from URL and return content"""
        self.log(f"Downloading {description}...")
        self.log(f"URL: {url}", "DEBUG")
        
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                content = response.read()
                self.log(f"Downloaded {len(content)} bytes", "DEBUG")
                return content
        except urllib.error.URLError as e:
            self.log(f"Failed to download {description}: {e}", "ERROR")
            return None
        except Exception as e:
            self.log(f"Unexpected error downloading {description}: {e}", "ERROR")
            return None
            
    def get_latest_firmware_info(self):
        """Get latest firmware information from GitHub"""
        self.log("Checking for latest firmware...")
        
        latest_url = f"{self.base_url}/releases/latest.json"
        content = self.download_file(latest_url, "firmware info")
        
        if not content:
            return None
            
        try:
            latest_info = json.loads(content.decode('utf-8'))
            self.log(f"Latest version: {latest_info['latest_version']}", "SUCCESS")
            
            # Now download the detailed version info
            version_info_url = latest_info['info_url']
            self.log("Getting detailed version information...")
            version_content = self.download_file(version_info_url, "version details")
            
            if not version_content:
                return None
                
            version_info = json.loads(version_content.decode('utf-8'))
            
            # Combine the information
            firmware_info = {
                'latest_version': latest_info['latest_version'],
                'latest_firmware': latest_info['latest_firmware'],
                'download_url': latest_info['download_url'],
                'file_size': version_info['file_size'],
                'sha256': version_info['sha256']
            }
            
            return firmware_info
            
        except (json.JSONDecodeError, KeyError) as e:
            self.log(f"Invalid firmware info format: {e}", "ERROR")
            return None
            
    def download_firmware(self, firmware_info):
        """Download firmware binary"""
        firmware_url = firmware_info['download_url']
        expected_size = firmware_info['file_size']
        expected_sha256 = firmware_info['sha256']
        
        self.log(f"Downloading firmware: {firmware_info['latest_firmware']}")
        self.log(f"Expected size: {expected_size:,} bytes")
        
        firmware_data = self.download_file(firmware_url, "firmware binary")
        if not firmware_data:
            return None
            
        # Verify size
        if len(firmware_data) != expected_size:
            self.log(f"Size mismatch! Expected {expected_size}, got {len(firmware_data)}", "ERROR")
            return None
            
        # Verify SHA256
        actual_sha256 = hashlib.sha256(firmware_data).hexdigest()
        if actual_sha256 != expected_sha256:
            self.log(f"SHA256 mismatch! Expected {expected_sha256}, got {actual_sha256}", "ERROR")
            return None
            
        self.log("Firmware verification successful", "SUCCESS")
        return firmware_data
        
    def setup_temp_directory(self):
        """Create temporary directory for firmware file"""
        self.temp_dir = tempfile.mkdtemp(prefix="robot_updater_")
        self.log(f"Created temp directory: {self.temp_dir}", "DEBUG")
        
    def cleanup_temp_directory(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                self.log("Cleaned up temp directory", "DEBUG")
            except Exception as e:
                self.log(f"Warning: Could not clean up temp directory: {e}", "WARNING")
                
    def find_esptool(self):
        """Find esptool.py installation"""
        self.log("Looking for esptool...")
        
        # Try common locations
        possible_paths = [
            # PlatformIO installation
            os.path.expanduser("~/.platformio/packages/tool-esptoolpy/esptool.py"),
            "C:/Users/" + os.getenv('USERNAME', 'user') + "/.platformio/packages/tool-esptoolpy/esptool.py",
            
            # pip installation
            "esptool.py",
            "esptool",
            
            # Local installation
            "./esptool.py",
            "../esptool.py"
        ]
        
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    self.log(f"Found esptool at: {path}", "DEBUG")
                    self.esptool_path = path
                    return True
                    
                # Try to run it (for PATH-based installations)
                result = subprocess.run([path, "version"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                if result.returncode == 0:
                    self.log(f"Found esptool in PATH: {path}", "DEBUG")
                    self.esptool_path = path
                    return True
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                continue
                
        return False
        
    def download_esptool(self):
        """Download esptool.py if not found locally"""
        self.log("Downloading esptool.py...")
        
        esptool_url = "https://raw.githubusercontent.com/espressif/esptool/master/esptool.py"
        esptool_content = self.download_file(esptool_url, "esptool.py")
        
        if not esptool_content:
            return False
            
        esptool_path = os.path.join(self.temp_dir, "esptool.py")
        with open(esptool_path, 'wb') as f:
            f.write(esptool_content)
            
        self.esptool_path = esptool_path
        self.log("Downloaded esptool.py successfully", "SUCCESS")
        return True
        
    def find_esp32_ports(self):
        """Find available ESP32 devices"""
        self.log("Scanning for ESP32 devices...")
        
        esp32_ports = []
        for port in serial.tools.list_ports.comports():
            # Look for ESP32 indicators
            if any(indicator in (port.description or "").lower() for indicator in 
                   ["esp32", "silicon labs", "cp210", "ch340", "ftdi"]):
                esp32_ports.append(port.device)
                self.log(f"Found potential ESP32 at {port.device}: {port.description}", "DEBUG")
                
        return esp32_ports
        
    def flash_firmware(self, firmware_data, port):
        """Flash firmware to ESP32"""
        self.log(f"Flashing firmware to {port}...")
        
        if self.dry_run:
            self.log("DRY RUN: Would flash firmware but --dry-run is enabled", "WARNING")
            return True
        
        # Save firmware to temp file
        firmware_path = os.path.join(self.temp_dir, "firmware.bin")
        with open(firmware_path, 'wb') as f:
            f.write(firmware_data)
            
        # Build esptool command
        cmd = [
            "python", self.esptool_path,
            "--chip", "esp32c3",
            "--port", port,
            "--baud", "460800",
            "write_flash",
            "0x150000",  # OTA_0 partition
            firmware_path
        ]
        
        self.log(f"Flash command: {' '.join(cmd)}", "DEBUG")
        
        try:
            # Run flash command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.log("Firmware flashed successfully!", "SUCCESS")
                
                # Reset the device
                reset_cmd = [
                    "python", self.esptool_path,
                    "--chip", "esp32c3", 
                    "--port", port,
                    "--baud", "460800",
                    "run"
                ]
                
                subprocess.run(reset_cmd, capture_output=True, timeout=10)
                self.log("Device reset completed", "SUCCESS")
                return True
            else:
                self.log(f"Flash failed: {result.stderr}", "ERROR")
                if self.debug:
                    self.log(f"Flash stdout: {result.stdout}", "DEBUG")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("Flash operation timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"Flash error: {e}", "ERROR")
            return False
            
    def update_robot(self, port=None):
        """Main update process"""
        try:
            # Setup
            self.setup_temp_directory()
            
            # Find esptool
            if not self.find_esptool():
                if not self.download_esptool():
                    self.log("Could not find or download esptool.py", "ERROR")
                    return False
                    
            # Get latest firmware info
            firmware_info = self.get_latest_firmware_info()
            if not firmware_info:
                self.log("Could not get firmware information", "ERROR")
                return False
                
            # Download firmware
            firmware_data = self.download_firmware(firmware_info)
            if not firmware_data:
                self.log("Could not download firmware", "ERROR")
                return False
                
            # Find ESP32 devices if port not specified
            if not port:
                ports = self.find_esp32_ports()
                if not ports:
                    self.log("No ESP32 devices found. Please connect your robot.", "ERROR")
                    return False
                elif len(ports) == 1:
                    port = ports[0]
                    self.log(f"Using port: {port}")
                else:
                    self.log(f"Multiple ESP32 devices found: {', '.join(ports)}")
                    self.log("Please specify port with --port option", "ERROR")
                    return False
                    
            # Flash firmware
            success = self.flash_firmware(firmware_data, port)
            
            if success:
                self.log("Robot update completed successfully! 🎉", "SUCCESS")
                self.log("Your robot will restart with the new firmware.", "INFO")
            
            return success
            
        finally:
            self.cleanup_temp_directory()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Update Steam Robot firmware from GitHub")
    parser.add_argument("--port", help="Serial port (e.g., COM3, /dev/ttyUSB0)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--dry-run", action="store_true", help="Download firmware but don't flash")
    parser.add_argument("--list-ports", action="store_true", help="List available serial ports")
    
    args = parser.parse_args()
    
    if args.list_ports:
        print("Available serial ports:")
        import serial.tools.list_ports
        for port in serial.tools.list_ports.comports():
            print(f"  {port.device}: {port.description}")
        return
        
    updater = RobotUpdater(debug=args.debug, dry_run=args.dry_run)
    updater.print_banner()
    
    # Check dependencies
    try:
        import serial.tools.list_ports
    except ImportError:
        updater.log("pyserial is required. Install with: pip install pyserial", "ERROR")
        sys.exit(1)
        
    success = updater.update_robot(args.port)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
