#!/bin/bash

echo -e "\n==========================================="
echo -e "AWS IPAM Configurator - START"
echo -e "===========================================\n"

# Ask user if they would like to begin
read -p "Begin local deployment of AWS IPAM Configurator? (y/n): " IPAM_APP
if [[ $IPAM_APP != "y" && $IPAM_APP != "Y" ]]; then
    echo -e "\nExiting.\n"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo -e "\nPython 3 is required but not found. Please install Python 3.\n"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null
then
    echo -e "\npip3 is required but not found. Please install pip3.\n"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "\nCreating virtual environment...\n"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "\nActivating virtual environment...\n"
source venv/bin/activate

# Install requirements
echo -e "\nInstalling dependencies...\n"
pip install --upgrade pip
pip install -r requirements.txt

# Run the Streamlit app
echo -e "\nStarting AWS IPAM Configurator...\n"
streamlit run app.py
