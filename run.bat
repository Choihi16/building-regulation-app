@echo off
echo Starting AI Architectural Regulation Agent (Streamlit)...
call "%~dp0venv\Scripts\activate.bat"
streamlit run "%~dp0app.py"
pause
