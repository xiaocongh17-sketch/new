"""Auto-deploy to Alibaba Cloud via SSH."""
import subprocess, sys, os

HOST = "39.106.114.162"
USER = "root"
PASS = "123654Hxc#"
PROJECT_DIR = "/opt/ai-store-copilot"
REPO = "https://github.com/xiaocongh17-sketch/new.git"

COMMANDS = f"""
set -e
echo "=== Step 1: Install Docker ==="
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
fi
echo "Docker OK"

echo "=== Step 2: Clone project ==="
if [ -d {PROJECT_DIR} ]; then
    cd {PROJECT_DIR} && git pull
else
    mkdir -p /opt && cd /opt
    git clone {REPO} ai-store-copilot
fi
cd {PROJECT_DIR}

echo "=== Step 3: Setup env ==="
if [ ! -f .env ]; then
    cp .env.example .env
    sed -i 's/AI_API_KEY=.*/AI_API_KEY=sk-f93ca4cf36f64c909a21770040e95697/' .env
fi

echo "=== Step 4: Start services ==="
docker-compose -f docker/docker-compose.yml up -d --build 2>&1 || docker compose -f docker/docker-compose.yml up -d --build 2>&1

echo "=== Step 5: Status ==="
sleep 8
docker ps
curl -s http://localhost:8000/api/health || echo "Backend starting..."
echo ""
echo "DEPLOY DONE!"
echo "Frontend: http://{HOST}:3003"
echo "Backend: http://{HOST}:8000"
"""

# Use plink if available, else try ssh with expect
def deploy():
    # Try plink (PuTTY) first
    plink_paths = [
        r"C:\Program Files\PuTTY\plink.exe",
        os.path.expandvars(r"%ProgramFiles%\PuTTY\plink.exe"),
    ]
    plink = None
    for p in plink_paths:
        if os.path.exists(p):
            plink = p
            break

    if plink:
        print(f"Using plink: {plink}")
        cmd = [plink, "-ssh", "-pw", PASS, "-batch", f"{USER}@{HOST}", COMMANDS]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr[-500:])
        return result.returncode

    # Try writing an expect-like script with Python
    print("Trying paramiko...")
    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, username=USER, password=PASS, timeout=15)
        stdin, stdout, stderr = client.exec_command(COMMANDS, timeout=300)
        for line in stdout:
            print(line.strip())
        for line in stderr:
            print("ERR:", line.strip())
        client.close()
        return 0
    except ImportError:
        print("paramiko not available")

    # Last resort: try ssh with sshpass
    print("Trying ssh with password pipe...")
    script = f'echo "{PASS}" | ssh -o StrictHostKeyChecking=no {USER}@{HOST} "bash -s" <<\'EOF\'\n{COMMANDS}\nEOF'
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=300)
    print(result.stdout)
    if result.stderr:
        print("ERR:", result.stderr[-500:])
    return result.returncode


if __name__ == "__main__":
    print(f"Deploying to {HOST}...")
    code = deploy()
    sys.exit(code)
