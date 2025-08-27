# Steam Robot Updater

A simple tool to update your Steam Robot firmware directly from GitHub without requiring PlatformIO installation.

## Quick Start

### Windows Users
1. **Double-click** `update_robot.bat`
2. The script will automatically:
   - Check if Python is installed
   - Install required dependencies (pyserial)
   - Find your connected robot
   - Download and flash the latest firmware

### Linux/Mac Users
1. **Run** `./update_robot.sh` in a terminal
2. The script will automatically:
   - Check if Python is installed
   - Install required dependencies (pyserial)
   - Find your connected robot
   - Download and flash the latest firmware

### Manual Usage
If you prefer to run the Python script directly:

```bash
# Basic usage (auto-detect robot)
python robot_updater.py

# Specify a specific port
python robot_updater.py --port COM3

# Enable debug output
python robot_updater.py --debug

# List available ports
python robot_updater.py --list-ports
```

## Requirements

- **Python 3.6+** installed on your system
- **pyserial** library (automatically installed by the scripts)
- **USB cable** connecting your robot to the computer

## What It Does

1. **Downloads latest firmware** from GitHub repository
2. **Verifies firmware integrity** using SHA256 checksums
3. **Automatically finds** connected ESP32 devices
4. **Downloads esptool.py** if not already available
5. **Flashes firmware** to the robot's OTA partition
6. **Resets the robot** to boot with new firmware

## Supported Platforms

- ✅ **Windows** (7, 8, 10, 11)
- ✅ **macOS** (10.12+)
- ✅ **Linux** (Ubuntu, Debian, Fedora, etc.)

## Troubleshooting

### "No ESP32 devices found"
- Make sure your robot is connected via USB
- Check that the robot is powered on
- Try a different USB cable or port
- On Linux, you may need to add your user to the `dialout` group:
  ```bash
  sudo usermod -a -G dialout $USER
  # Then log out and log back in
  ```

### "Python is not installed"
- Download and install Python from [python.org](https://python.org)
- Make sure to check "Add Python to PATH" during installation

### "Permission denied" (Linux/Mac)
- Make sure the script is executable: `chmod +x update_robot.sh`
- You may need to run with sudo for serial port access

### Multiple ESP32 devices detected
- Disconnect other ESP32 devices
- Or specify the exact port: `python robot_updater.py --port COM3`

### Flash fails
- Try a different USB cable
- Make sure the robot isn't running other programs
- Try holding the boot button during flash

## Advanced Options

### Using a specific firmware version
The updater always downloads the latest version from the `main` branch. To use a different version:

1. Fork the repository
2. Upload your desired firmware to the `releases/` folder
3. Update the `latest.json` file
4. Modify the `github_repo` variable in `robot_updater.py`

### Building from source
If you want to build and flash your own firmware:

1. Use the full development environment with PlatformIO
2. Use `simple_deploy.py` for development builds
3. Use this updater for release versions only

## Security Notes

- Firmware integrity is verified using SHA256 checksums
- All downloads use HTTPS from the official GitHub repository
- esptool.py is downloaded from the official Espressif repository

## Support

If you encounter issues:

1. Run with `--debug` flag for detailed output
2. Check the troubleshooting section above
3. Make sure you have the latest version of the updater
4. Report issues to the project repository

## Version Information

This updater works with:
- **Hardware**: ESP32-C3 Steam Robot
- **Firmware**: v20250826+ (OTA-enabled versions)
- **Repository**: TheDaveCollective/BYKTW-Robot
