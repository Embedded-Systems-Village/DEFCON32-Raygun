@echo off

REM Wait for RPI bootloader device
echo Waiting for RPI bootloader device...
:wait_for_device
timeout /t 1 >nul
set "drive="
for %%d in (A B C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    vol %%d: 2>nul | find "RPI-RP2" >nul && set drive=%%d:
)

if not defined drive goto wait_for_device

REM Copy RPI_PICO-20240602-v1.23.0.uf2 to the device
echo Copying RPI_PICO-20240602-v1.23.0.uf2 to the device...
copy "..\micropython\RPI_PICO-20240602-v1.23.0.uf2" "%drive%"

REM Wait for the device to reboot and connect
echo Waiting for the device to reboot and connect...
:wait_for_reboot
timeout /t 1 >nul
set "device_found="
for /f "tokens=1,2,3" %%i in ('mpremote.exe connect list 2^>nul') do (
    if "%%k"=="2e8a:0005" set "device_found=1"
)
if not defined device_found goto wait_for_reboot

REM Copy all wav files from ../sounds to the device using mpremote
echo Copying all wav files to the device...
for %%f in (..\sounds\*.wav) do (
    echo Copying %%f...
    mpremote.exe fs cp "%%f" ":%%~nxf"
)

REM Copy all py files from the parent directory to the device using mpremote
echo Copying all py files to the device...
for %%f in (..\*.py) do (
    echo Copying %%f...
    mpremote.exe fs cp "%%f" ":%%~nxf"
)

mpremote.exe reset
echo Done.