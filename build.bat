@echo off
echo Building Theta Terminal Manager...
python build.py
if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    echo Executable is located in the "dist" folder
) else (
    echo Build failed with error code %ERRORLEVEL%
)
pause 