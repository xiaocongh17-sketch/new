"""Quick script to check port 8000 and restart backend."""
import subprocess
import sys

# Check if port 8000 is in use
result = subprocess.run(
    ["netstat", "-ano"], capture_output=True, text=True, timeout=10
)
lines = result.stdout.splitlines()
for line in lines:
    if "8000" in line and "LISTENING" in line:
        parts = line.strip().split()
        pid = parts[-1]
        print(f"Port 8000 in use by PID: {pid}")
        # Kill it
        subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, text=True)
        print(f"Killed PID {pid}")
        break
else:
    print("Port 8000 is free")
