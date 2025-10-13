import subprocess
import threading
import time

# Start a persistent CMD (on Windows)
proc = subprocess.Popen(
    ["cmd.exe"],                 # change to ["bash"] if on Linux
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

def reader():
    """Continuously read output from the terminal."""
    for line in proc.stdout:
        print("[TERMINAL]", line.strip())

# Run output reader in a separate thread
thread = threading.Thread(target=reader, daemon=True)
thread.start()

# --- Send commands dynamically ---
while True:
    cmd = input(">>> ")  # type any command
    if cmd.lower() in ("exit", "quit"):
        print("Session will NOT exit. (Use Ctrl+C to stop manually)")
        continue

    # Send the command to the running terminal
    proc.stdin.write(cmd + "\n")
    proc.stdin.flush()
