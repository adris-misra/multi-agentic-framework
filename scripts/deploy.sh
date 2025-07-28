#!/bin/bash

# Deployment Script: Setup and Run the Multi-Agentic Coding Framework

echo "📦 Creating virtual environment..."
python3 -m venv env
source env/bin/activate

echo "⬇️ Installing required packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🚀 Running the multi-agent pipeline..."
python main.py
