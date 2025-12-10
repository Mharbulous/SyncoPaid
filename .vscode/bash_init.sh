#!/bin/bash
# VS Code terminal initialization script
# Auto-activates virtual environment for Git Bash

# Source the default bash profile if it exists
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
elif [ -f ~/.bash_profile ]; then
    source ~/.bash_profile
fi

# Auto-activate virtual environment
if [ -d "venv/Scripts" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/Scripts/activate
fi
