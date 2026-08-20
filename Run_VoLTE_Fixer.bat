@echo off
chcp 65001 > NUL
title HBG VoLTE ^& IMS Fixer Tool (1-Click ADB Direct)

cd /d "%~dp0"
call "%~dp0Fix_VoLTE_Direct.bat"

