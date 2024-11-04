import os
import signal
import subprocess
import psutil

def cleanup_peers():
    # Kill processes on ports 8000-8007
    for port in range(8000, 8008):
        try:
            # Find process using the port
            cmd = f"lsof -i :{port} -t"
            pid = subprocess.check_output(cmd, shell=True).decode().strip()
            if pid:
                os.kill(int(pid), signal.SIGTERM)
                print(f"Killed process on port {port}")
        except:
            continue

    # Clean up log files
    try:
        os.system("rm -f *.log")
        os.system("rm -f *_log.txt")
        os.system("rm -rf __pycache__")
        os.system("rm -f *.pyc")
        print("Cleaned up log files and cache")
    except Exception as e:
        print(f"Error cleaning up files: {e}")

if __name__ == "__main__":
    cleanup_peers()