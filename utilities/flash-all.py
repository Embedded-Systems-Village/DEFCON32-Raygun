import os
import shutil
import subprocess
import time
import threading

UF2_FILE = "../micropython/RPI_PICO-20240602-v1.23.0.uf2"
VID_PID = "2e8a:0005"

def wait_for_device():
    print("Waiting for RPI bootloader device...")
    while True:
        drives = [f"{d}:" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:")]
        for drive in drives:
            try:
                result = subprocess.run(["wmic", "logicaldisk", "where", f"DeviceID='{drive}'", "get", "VolumeName"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                if "RPI-RP2" in result.stdout:
                    print(f"Found RPI bootloader device on {drive}")
                    copy_uf2(drive)
            except subprocess.CalledProcessError:
                continue
        time.sleep(1)

def copy_uf2(drive):
    print(f"Copying {UF2_FILE} to the device...")
    destination = os.path.join(drive, os.path.basename(UF2_FILE))
    shutil.copy(UF2_FILE, destination)

def monitor_com_ports():
    known_ports = set()
    while True:
        result = subprocess.run(["mpremote.exe", "connect", "list"], stdout=subprocess.PIPE, text=True)
        current_ports = {line.split()[0] for line in result.stdout.splitlines() if VID_PID in line}
        # print(f"Current ports: {current_ports}")
        # print(f"Known ports: {known_ports}")
        new_ports = current_ports - known_ports
        for port in new_ports:
            print(f"Found new device on port {port}")
            threading.Thread(target=handle_device, args=(port,), daemon=True).start()
        known_ports = current_ports
        time.sleep(1)

def handle_device(port):
    copy_files(port)
    reboot_device(port)

def copy_files(port):
    code_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    sounds_dir = os.path.join(code_dir, "sounds")
    
    # Copy .wav files from /sounds directory
    if os.path.exists(sounds_dir):
        for file in os.listdir(sounds_dir):
            if file.endswith(".wav"):
                file_path = os.path.join(sounds_dir, file)
                print(f"Copying {file_path} to port {port}...")
                subprocess.run(["mpremote.exe", "connect", port, "fs", "cp", file_path, f":{file}"])
    
    # Copy .py files from parent directory
    for file in os.listdir(code_dir):
        if file.endswith(".py"):
            file_path = os.path.join(code_dir, file)
            print(f"Copying {file_path} to port {port}...")
            subprocess.run(["mpremote.exe", "connect", port, "fs", "cp", file_path, f":{file}"])


def reboot_device(port):
    print(f"Rebooting the device on port {port}...")
    subprocess.run(["mpremote.exe", "connect", port, "reset"])

def main():
    threading.Thread(target=wait_for_device, daemon=True).start()
    threading.Thread(target=monitor_com_ports, daemon=True).start()

    # Keep the main thread alive
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()