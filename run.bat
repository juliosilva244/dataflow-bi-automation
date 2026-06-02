@echo off
title DataFlow BI Automation

cd /d "%~dp0"

python -m streamlit run app.py

pause