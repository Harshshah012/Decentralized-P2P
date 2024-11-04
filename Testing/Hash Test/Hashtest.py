import hashlib
import time
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import random
import string

class HashFunctionAnalyzer:
    def __init__(self):
        self.num_nodes = 8  # 8 nodes in 3-bit hypercube
        self.node_ids = [format(i, '03b') for i in range(self.num_nodes)]
        
    def _hash_topic(self, topic_name):
        """Hash function from the original implementation."""
        return hashlib.sha256(topic_name.encode()).hexdigest()
    
    def _get_node_for_topic(self, topic_hash):
        """Determine which node should store the topic based on its hash."""
        # Take first 3 bits of hash (converted to binary) to match with 3-bit node IDs
        binary = bin(int(topic_hash[:2], 16))[2:].zfill(8)
        return binary[:3]
    
    def generate_random_topic(self, length=10):
        """Generate a random topic name."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def measure_hash_performance(self, num_operations=10000):
        """Measure time complexity of hash function."""
        topics = [self.generate_random_topic() for _ in range(num_operations)]
        
        # Measure hashing time
        start_time = time.time()
        for topic in topics:
            self._hash_topic(topic)
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / num_operations
        
        return {
            'total_time': total_time,
            'avg_time': avg_time,
            'operations': num_operations
        }
    
    def analyze_distribution(self, num_topics=10000):
        """Analyze how topics are distributed among nodes."""
        distribution = defaultdict(int)
        topics = [self.generate_random_topic() for _ in range(num_topics)]
        
        for topic in topics:
            topic_hash = self._hash_topic(topic)
            node_id = self._get_node_for_topic(topic_hash)
            distribution[node_id] += 1
        
        return dict(distribution)
    
    def run_comprehensive_analysis(self):
        """Run complete analysis and generate visualizations."""
        # 1. Performance Analysis
        sample_sizes = [100, 1000, 5000, 10000, 50000]
        performance_results = []
        
        for size in sample_sizes:
            result = self.measure_hash_performance(size)
            performance_results.append(result)
            print(f"\nPerformance for {size} operations:")
            print(f"Total time: {result['total_time']:.4f} seconds")
            print(f"Average time per operation: {result['avg_time']*1000000:.4f} microseconds")
        
        # 2. Distribution Analysis
        distribution = self.analyze_distribution()
        total_topics = sum(distribution.values())
        expected_per_node = total_topics / self.num_nodes
        
        print("\nDistribution Analysis:")
        for node_id in sorted(distribution.keys()):
            count = distribution[node_id]
            percentage = (count / total_topics) * 100
            deviation = ((count - expected_per_node) / expected_per_node) * 100
            print(f"Node {node_id}: {count} topics ({percentage:.2f}%) [Deviation: {deviation:+.2f}%]")
        
        # Generate visualizations
        self.generate_plots(sample_sizes, performance_results, distribution)
    
    def generate_plots(self, sample_sizes, performance_results, distribution):
        """Generate visualization plots."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Total Time vs Number of Operations
        total_times = [r['total_time'] for r in performance_results]
        ax1.plot(sample_sizes, total_times, marker='o')
        ax1.set_title('Total Time vs Number of Operations')
        ax1.set_xlabel('Number of Operations')
        ax1.set_ylabel('Total Time (seconds)')
        ax1.grid(True)
        
        # 2. Average Time per Operation
        avg_times = [r['avg_time']*1000000 for r in performance_results]  # Convert to microseconds
        ax2.plot(sample_sizes, avg_times, marker='o', color='green')
        ax2.set_title('Average Time per Operation')
        ax2.set_xlabel('Number of Operations')
        ax2.set_ylabel('Average Time (microseconds)')
        ax2.grid(True)
        
        # 3. Topic Distribution Across Nodes
        nodes = sorted(distribution.keys())
        counts = [distribution[node] for node in nodes]
        ax3.bar(nodes, counts)
        ax3.set_title('Topic Distribution Across Nodes')
        ax3.set_xlabel('Node ID')
        ax3.set_ylabel('Number of Topics')
        ax3.grid(True)
        
        # 4. Distribution Uniformity Analysis
        expected = np.mean(counts)
        deviations = [(count - expected)/expected * 100 for count in counts]
        ax4.bar(nodes, deviations, color='red')
        ax4.set_title('Distribution Deviation from Mean')
        ax4.set_xlabel('Node ID')
        ax4.set_ylabel('Deviation from Mean (%)')
        ax4.grid(True)
        
        plt.tight_layout()
        plt.savefig('hash_function_analysis.png')
        print("\nAnalysis plots saved as 'hash_function_analysis.png'")

def main():
    analyzer = HashFunctionAnalyzer()
    print("Starting Hash Function Analysis...")
    analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    main()