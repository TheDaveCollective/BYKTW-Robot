#!/bin/bash

echo "================================================"
echo "          Steam Robot Firmware Updater"
echo "================================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed"
        echo "Please install Python 3.x"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "Using Python: $PYTHON_CMD"

# Check if pyserial is installed
$PYTHON_CMD -c "import serial" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing pyserial dependency..."
    $PYTHON_CMD -m pip install pyserial
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install pyserial"
        echo "Please run: pip install pyserial"
        exit 1
    fi
fi

# Run the updater
echo "Starting robot updater..."
echo
$PYTHON_CMD robot_updater.py "$@"
