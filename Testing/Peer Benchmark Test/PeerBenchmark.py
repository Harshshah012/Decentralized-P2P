import asyncio
import time
import random
import matplotlib.pyplot as plt
import numpy as np
import statistics
import json
import os

class PeerBenchmark:
    def __init__(self):
        self.peer_configs = [
            {"id": "000", "port": 8000},
            {"id": "001", "port": 8001},
            {"id": "010", "port": 8002},
            {"id": "011", "port": 8003},
            {"id": "100", "port": 8004},
            {"id": "101", "port": 8005},
            {"id": "110", "port": 8006},
            {"id": "111", "port": 8007}
        ]
        self.test_topics = [f"Topic_{i}" for i in range(5)]
        self.test_messages = [f"Test message {i}" for i in range(10)]
        self.results = {
            'create_topic': {'latency': [], 'throughput': []},
            'delete_topic': {'latency': [], 'throughput': []},
            'publish': {'latency': [], 'throughput': []},
            'subscribe': {'latency': [], 'throughput': []},
            'pull': {'latency': [], 'throughput': []}
        }
        
    async def benchmark_api(self, peer_id, port, operation, num_iterations=10):
        """Benchmark a specific API operation."""
        latencies = []
        start_time = time.time()
        operations_completed = 0
        
        for _ in range(num_iterations):
            if operation == 'create_topic':
                topic_name = f"Topic_{random.randint(1000, 9999)}"
                start = time.time()
                # Simulate create topic operation
                await asyncio.sleep(random.uniform(0.1, 0.3))
                end = time.time()
                
            elif operation == 'delete_topic':
                start = time.time()
                # Simulate delete topic operation
                await asyncio.sleep(random.uniform(0.1, 0.2))
                end = time.time()
                
            elif operation == 'publish':
                start = time.time()
                # Simulate publish operation
                await asyncio.sleep(random.uniform(0.2, 0.4))
                end = time.time()
                
            elif operation == 'subscribe':
                start = time.time()
                # Simulate subscribe operation
                await asyncio.sleep(random.uniform(0.1, 0.2))
                end = time.time()
                
            elif operation == 'pull':
                start = time.time()
                # Simulate pull operation
                await asyncio.sleep(random.uniform(0.3, 0.5))
                end = time.time()
            
            latency = end - start
            latencies.append(latency)
            operations_completed += 1
        
        total_time = time.time() - start_time
        throughput = operations_completed / total_time
        
        self.results[operation]['latency'].extend(latencies)
        self.results[operation]['throughput'].append(throughput)
        
        return np.mean(latencies), throughput

    async def run_benchmarks(self):
        """Run benchmarks for all peers and operations."""
        operations = ['create_topic', 'delete_topic', 'publish', 'subscribe', 'pull']
        
        for peer in self.peer_configs:
            print(f"Benchmarking peer {peer['id']} on port {peer['port']}")
            
            for operation in operations:
                latency, throughput = await self.benchmark_api(
                    peer['id'], 
                    peer['port'], 
                    operation
                )
                print(f"  {operation}: Avg Latency = {latency:.3f}s, Throughput = {throughput:.2f} ops/s")

    def generate_graphs(self):
        """Generate performance visualization graphs."""
        operations = list(self.results.keys())
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Latency Box Plot
        latency_data = [self.results[op]['latency'] for op in operations if self.results[op]['latency']]
        ops_with_data = [op for op in operations if self.results[op]['latency']]
        if latency_data:
            ax1.boxplot(latency_data, labels=ops_with_data)
            ax1.set_title('API Latency Distribution')
            ax1.set_ylabel('Latency (seconds)')
            ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True)
        
        # 2. Average Throughput Bar Chart
        throughputs = [np.mean(self.results[op]['throughput']) if self.results[op]['throughput'] else 0 
                      for op in operations]
        ax2.bar(operations, throughputs)
        ax2.set_title('Average API Throughput')
        ax2.set_ylabel('Operations per second')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True)
        
        # 3. Latency Histogram
        for op in operations:
            if self.results[op]['latency']:
                ax3.hist(self.results[op]['latency'], 
                        alpha=0.5, 
                        label=op, 
                        bins=20)
        ax3.set_title('Latency Distribution')
        ax3.set_xlabel('Latency (seconds)')
        ax3.set_ylabel('Frequency')
        ax3.legend()
        ax3.grid(True)
        
        # 4. Throughput per Peer
        x = np.arange(len(self.peer_configs))
        width = 0.15  # Adjusted for 5 operations
        
        for i, op in enumerate(operations):
            if self.results[op]['throughput']:
                ax4.bar(x + i*width, self.results[op]['throughput'], width, label=op)
        
        ax4.set_title('Throughput Across Peers')
        ax4.set_xlabel('Peer Index')
        ax4.set_ylabel('Operations per second')
        ax4.set_xticks(x + width * (len(operations)-1)/2)
        ax4.set_xticklabels([p['id'] for p in self.peer_configs])
        ax4.legend()
        ax4.grid(True)
        
        plt.tight_layout()
        plt.savefig('peer_benchmark_results.png')
        print("\nBenchmark graphs saved as 'peer_benchmark_results.png'")
        
        # Print statistical summary
        self.print_statistics()

    def print_statistics(self):
        """Print statistical summary of benchmark results."""
        print("\nBenchmark Results Summary:")
        print("=" * 50)
        
        for operation in self.results:
            latencies = self.results[operation]['latency']
            throughputs = self.results[operation]['throughput']
            
            print(f"\n{operation.upper()} Statistics:")
            if latencies:
                print(f"Latency (seconds):")
                print(f"  Mean: {np.mean(latencies):.6f}")
                print(f"  Median: {np.median(latencies):.6f}")
                print(f"  Std Dev: {np.std(latencies):.6f}")
            else:
                print("  No latency data available")
            
            if throughputs:
                print(f"Throughput (ops/sec):")
                print(f"  Mean: {np.mean(throughputs):.2f}")
                print(f"  Median: {np.median(throughputs):.2f}")
                print(f"  Std Dev: {np.std(throughputs):.2f}")
            else:
                print("  No throughput data available")

async def main():
    benchmark = PeerBenchmark()
    await benchmark.run_benchmarks()
    benchmark.generate_graphs()

if __name__ == "__main__":
    asyncio.run(main())