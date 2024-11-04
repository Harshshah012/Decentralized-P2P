import asyncio
import time
import random
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import logging
import json

class ForwardingAnalyzer:
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
        self.results = {
            'access_success': defaultdict(list),
            'response_times': defaultdict(list),
            'throughput': defaultdict(list)
        }
        
    async def test_topic_access(self, source_id, target_id, num_tests=10):
        """Test topic access between peers."""
        print(f"\nTesting access from {source_id} to {target_id}")
        successes = 0
        total_time = 0
        
        for i in range(num_tests):
            topic_name = f"TestTopic_{random.randint(1000, 9999)}"
            start_time = time.time()
            
            try:
                # Simulate request forwarding through hypercube
                path = self.calculate_routing_path(source_id, target_id)
                await asyncio.sleep(0.1 * len(path))  # Simulate network delay
                
                end_time = time.time()
                response_time = end_time - start_time
                
                self.results['response_times'][f"{source_id}->{target_id}"].append(response_time)
                successes += 1
                total_time += response_time
                
            except Exception as e:
                print(f"Error in access test: {e}")
        
        success_rate = (successes / num_tests) * 100
        avg_response_time = total_time / num_tests if successes > 0 else 0
        self.results['access_success'][f"{source_id}->{target_id}"] = success_rate
        
        return success_rate, avg_response_time

    async def measure_throughput(self, source_id, target_id, duration=5):
        """Measure throughput between peers."""
        print(f"Measuring throughput from {source_id} to {target_id}")
        messages_sent = 0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                # Simulate message sending
                path = self.calculate_routing_path(source_id, target_id)
                await asyncio.sleep(0.01)  # Simulate processing time
                messages_sent += 1
            except Exception as e:
                print(f"Error in throughput test: {e}")
        
        total_time = time.time() - start_time
        throughput = messages_sent / total_time
        self.results['throughput'][f"{source_id}->{target_id}"] = throughput
        
        return throughput

    def calculate_routing_path(self, source, target):
        """Calculate the routing path between two peers."""
        path = [source]
        current = source
        
        while current != target:
            next_hop = self.get_next_hop(current, target)
            if next_hop is None:
                raise Exception("No valid routing path")
            path.append(next_hop)
            current = next_hop
            
        return path

    def get_next_hop(self, current, target):
        """Get next hop in routing path."""
        for i in range(3):
            if current[i] != target[i]:
                next_hop = list(current)
                next_hop[i] = target[i]
                return ''.join(next_hop)
        return None

    def calculate_hamming_distance(self, id1, id2):
        """Calculate Hamming distance between two peer IDs."""
        return sum(c1 != c2 for c1, c2 in zip(id1, id2))

    async def run_comprehensive_tests(self):
        """Run all forwarding mechanism tests."""
        print("Starting Forwarding Mechanism Analysis...")
        
        # Test access between all peer combinations
        for source in self.peer_configs:
            for target in self.peer_configs:
                if source['id'] != target['id']:
                    success_rate, avg_response = await self.test_topic_access(
                        source['id'], target['id']
                    )
                    throughput = await self.measure_throughput(
                        source['id'], target['id']
                    )
                    
                    print(f"\nResults for {source['id']} -> {target['id']}:")
                    print(f"Success Rate: {success_rate:.2f}%")
                    print(f"Average Response Time: {avg_response*1000:.2f}ms")
                    print(f"Throughput: {throughput:.2f} messages/second")
        
        self.generate_analysis_plots()
        self.print_statistics()

    def generate_analysis_plots(self):
        """Generate visualization plots for the analysis."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Access Success Rates
        success_rates = list(self.results['access_success'].values())
        paths = list(self.results['access_success'].keys())
        ax1.bar(range(len(paths)), success_rates)
        ax1.set_title('Access Success Rates')
        ax1.set_xlabel('Peer Paths')
        ax1.set_ylabel('Success Rate (%)')
        ax1.set_xticks(range(len(paths)))
        ax1.set_xticklabels(paths, rotation=45)
        
        # 2. Response Time Distribution
        all_times = []
        for times in self.results['response_times'].values():
            all_times.extend(times)
        ax2.hist(all_times, bins=20)
        ax2.set_title('Response Time Distribution')
        ax2.set_xlabel('Response Time (seconds)')
        ax2.set_ylabel('Frequency')
        
        # 3. Throughput Comparison
        throughputs = list(self.results['throughput'].values())
        paths = list(self.results['throughput'].keys())
        ax3.bar(range(len(paths)), throughputs)
        ax3.set_title('Throughput Comparison')
        ax3.set_xlabel('Peer Paths')
        ax3.set_ylabel('Messages/Second')
        ax3.set_xticks(range(len(paths)))
        ax3.set_xticklabels(paths, rotation=45)
        
        # 4. Response Time vs Path Length
        path_lengths = [len(self.calculate_routing_path(*path.split('->'))) 
                       for path in self.results['response_times'].keys()]
        avg_times = [np.mean(times) for times in self.results['response_times'].values()]
        ax4.scatter(path_lengths, avg_times)
        ax4.set_title('Response Time vs Path Length')
        ax4.set_xlabel('Path Length (hops)')
        ax4.set_ylabel('Average Response Time (seconds)')
        
        plt.tight_layout()
        plt.savefig('forwarding_analysis.png')
        print("\nAnalysis plots saved as 'forwarding_analysis.png'")

    def print_statistics(self):
        """Print statistical summary of the results."""
        print("\nForwarding Mechanism Analysis Summary:")
        print("=" * 50)
        
        # Access Success Statistics
        print("\nAccess Success Rates:")
        success_rates = list(self.results['access_success'].values())
        print(f"Average Success Rate: {np.mean(success_rates):.2f}%")
        print(f"Minimum Success Rate: {np.min(success_rates):.2f}%")
        print(f"Maximum Success Rate: {np.max(success_rates):.2f}%")
        
        # Response Time Statistics
        print("\nResponse Time Statistics:")
        all_times = []
        for times in self.results['response_times'].values():
            all_times.extend(times)
        print(f"Average Response Time: {np.mean(all_times)*1000:.2f}ms")
        print(f"Median Response Time: {np.median(all_times)*1000:.2f}ms")
        print(f"95th Percentile: {np.percentile(all_times, 95)*1000:.2f}ms")
        
        # Throughput Statistics
        print("\nThroughput Statistics:")
        throughputs = list(self.results['throughput'].values())
        print(f"Average Throughput: {np.mean(throughputs):.2f} messages/second")
        print(f"Maximum Throughput: {np.max(throughputs):.2f} messages/second")
        print(f"Minimum Throughput: {np.min(throughputs):.2f} messages/second")

async def main():
    analyzer = ForwardingAnalyzer()
    await analyzer.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())