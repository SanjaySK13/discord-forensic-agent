@echo off
title Discord Stylometric Confession Predictor
cd /d "%~dp0"
echo ================================================================
echo Starting Discord Confession Attribution Web App...
echo URL: http://localhost:5000
echo ================================================================
python server.py
pause

