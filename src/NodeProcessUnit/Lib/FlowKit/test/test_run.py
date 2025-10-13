import subprocess

commands = [
    r'cd /d D:\Project\V1\FlowKit\src\NodeProcessUnit',
    r'venv\Scripts\activate.bat',
    r'python test_run.py',
]

for cmd in commands:
    print(f"→ Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # print output
    print(result.stdout)
    print(result.stderr)
    
    # check for errors
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        break
