import asyncio
import subprocess
import sys
import time

BASE_PATH = "/Users/harsh/Documents/IIT Sem 1/Advanced Operating Systems/Assignment 3/Test"

async def deploy_peers(num_peers=8):
    processes = []
    base_port = 8000
    
    # Start peer nodes
    for i in range(num_peers):
        peer_id = f"{i:03b}"  # Convert to 3-bit binary
        port = base_port + i
        cmd = [sys.executable, "peer_node.py", peer_id, str(port)]
        process = subprocess.Popen(cmd)
        processes.append(process)
        print(f"Started peer {peer_id} on port {port}")
        time.sleep(1)  # Give each peer time to start
    
    # Wait for all processes
    for process in processes:
        process.wait()

if __name__ == "__main__":
    asyncio.run(deploy_peers())