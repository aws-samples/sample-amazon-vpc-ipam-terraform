#!/bin/bash

echo -e "\n==========================================="
echo -e "AWS IPAM Configurator - TEARDOWN"
echo -e "===========================================\n"

# Find and kill the Streamlit process
STREAMLIT_PID=$(ps aux | grep "streamlit run app.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$STREAMLIT_PID" ]; then
    echo -e "\nStopping Streamlit process (PID: $STREAMLIT_PID)...\n"
    kill -9 $STREAMLIT_PID
else
    echo -e "\nNo running Streamlit process found.\n"
fi

# Deactivate virtual environment if active
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "\nDeactivating virtual environment...\n"
    deactivate 2>/dev/null || true
fi

# Clean up __pycache__ directories
echo -e "\nCleaning up __pycache__ directories...\n"
find . -type d -name "__pycache__" -exec rm -rf {} +
# If the above fails (because you can't remove a directory), this will work
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name "*.pyd" -delete

# Ask user if they want to remove the virtual environment
read -p "Do you want to remove the virtual environment? (y/n): " REMOVE_VENV
if [[ $REMOVE_VENV == "y" || $REMOVE_VENV == "Y" ]]; then
    if [ -d "venv" ]; then
        echo -e "\nRemoving virtual environment...\n"
        rm -rf venv
    fi
fi

# Remove .streamlit temporary directory
if [ -d ".streamlit" ]; then
    echo -e "\nRemoving .streamlit temporary directory...\n"
    rm -rf .streamlit
fi

echo -e "\nCleanup complete.\n"
