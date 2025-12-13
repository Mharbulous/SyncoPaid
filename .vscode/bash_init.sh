#!/bin/bash
# VS Code terminal initialization script
# Auto-activates virtual environment for Git Bash

# Source the default bash profile if it exists
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
elif [ -f ~/.bash_profile ]; then
    source ~/.bash_profile
fi

# Auto-activate virtual environment for current project
# Always activate local venv to ensure correct environment
if [ -d "venv/Scripts" ]; then
    source venv/Scripts/activate
fi
