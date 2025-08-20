#!/bin/bash
# Script to clone Pimoroni's ST7735 repo and install requirements

# Exit if any command fails
set -e  

# Create a working folder
mkdir -p ~/projects
cd ~/projects

# Remove old repo if it exists
if [ -d "st7735-python" ]; then
    echo "Removing old st7735-python directory..."
    rm -rf st7735-python
fi

# Clone the Pimoroni repo
echo "Cloning Pimoroni st7735-python repo..."
git clone https://github.com/pimoroni/st7735-python.git

# Move into repo
cd st7735-python

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt
pip install .

echo "Done! Now try running:"
echo "  cd ~/projects/st7735-python/examples"
echo "  python3 shapes.py"
