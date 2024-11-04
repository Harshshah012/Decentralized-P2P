import asyncio
import json
import hashlib
import logging
import random
import sys
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class DHT:
    def __init__(self):
        self.table = {}  # DHT table to store topics
        self.topic_mapping = {}  # Maps hash to original topic name
        self.reverse_mapping = {}  # Maps original name to hash

    def _hash_topic(self, topic_name):
        """Generate a hash for the topic name."""
        if isinstance(topic_name, (list, tuple)):
            topic_name = str(topic_name)
        return hashlib.sha256(str(topic_name).encode()).hexdigest()

    def put(self, topic_name, messages):
        """Store the topic and its messages in the DHT."""
        topic_hash = self._hash_topic(topic_name)
        if not isinstance(messages, list):
            messages = list(messages) if isinstance(messages, (tuple, set)) else [messages]
        self.table[topic_hash] = messages
        self.topic_mapping[topic_hash] = topic_name
        self.reverse_mapping[topic_name] = topic_hash

    def get(self, topic_name):
        """Retrieve messages for a given topic from the DHT."""
        topic_hash = self._hash_topic(topic_name)
        messages = self.table.get(topic_hash, [])
        return messages if isinstance(messages, list) else [messages]

    def remove(self, topic_name):
        """Remove a topic from the DHT."""
        topic_hash = self._hash_topic(topic_name)
        if topic_hash in self.table:
            del self.table[topic_hash]
            original_name = self.topic_mapping.get(topic_hash)
            if original_name:
                del self.reverse_mapping[original_name]
            del self.topic_mapping[topic_hash]

    def contains(self, topic_name):
        """Check if the DHT contains a topic."""
        topic_hash = self._hash_topic(topic_name)
        return topic_hash in self.table

    def get_original_name(self, topic_hash):
        """Get original topic name from hash."""
        return self.topic_mapping.get(topic_hash)

    def get_all_topics(self):
        """Get all topic names."""
        return list(self.reverse_mapping.keys())

    def get_hash(self, topic_name):
        """Get hash for a topic name."""
        return self.reverse_mapping.get(topic_name)

class PeerNode:
    def __init__(self, peer_id, port):
        self.peer_id = peer_id
        self.port = port
        self.connected_peers = {}
        self.dht = DHT()
        self.unread_messages = {}
        self.subscribed_topics = set()
        
        # Setup logging
        logging.basicConfig(
            filename=f'peer_{peer_id}.log',
            level=logging.INFO,
            format='%(asctime)s - %(message)s'
        )

    async def start(self):
        server = await asyncio.start_server(
            self.handle_peer, 'localhost', self.port
        )
        print(f"{Colors.OKGREEN}Peer {self.peer_id} running on port {self.port}{Colors.ENDC}")
        logging.info(f'Peer started on port {self.port}')
        
        # Start automated operations
        asyncio.create_task(self.automated_operations())
        
        async with server:
            await server.serve_forever()

    async def automated_operations(self):
        """Perform automated operations periodically"""
        operations = {
            'create': self.auto_create_topic,
            'publish': self.auto_publish_message,
            'subscribe': self.auto_subscribe_topic
        }
        
        weights = {
            'create': 0.3,    # 30% chance
            'publish': 0.3,   # 30% chance
            'subscribe': 0.4  # 40% chance - higher weight for subscribe
        }
        
        while True:
            await asyncio.sleep(random.uniform(2, 5))
            
            # Weighted random choice of operation
            operation_name = random.choices(
                list(operations.keys()),
                weights=list(weights.values())
            )[0]
            
            try:
                await operations[operation_name]()
            except Exception as e:
                logging.error(f"Error in {operation_name} operation: {str(e)}")

    async def auto_create_topic(self):
        """Automatically create a new topic"""
        topic_name = f"Topic_{self.peer_id}_{random.randint(1, 1000)}"
        if not self.dht.contains(topic_name):
            self.dht.put(topic_name, [])
            self.unread_messages[topic_name] = []
            self.subscribed_topics.add(topic_name)
            logging.info(f'Created topic: {topic_name}')
            await self.broadcast_topic_creation(topic_name)
        else:
            logging.warning(f'Topic {topic_name} already exists')

    async def auto_publish_message(self):
        """Automatically publish a message to a random subscribed topic"""
        if self.subscribed_topics:
            topic_name = random.choice(list(self.subscribed_topics))
            message = f"Message_{random.randint(1, 1000)}"
            
            # Get current messages and ensure it's a list
            messages = self.dht.get(topic_name)
            if not isinstance(messages, list):
                messages = []
            
            messages.append(message)
            self.dht.put(topic_name, messages)
            logging.info(f'Published to topic {topic_name}: {message}')
            
            # Broadcast to connected peers
            message_data = {
                'type': 'message',
                'topic': topic_name,
                'message': message
            }
            await self.broadcast_message(message_data)

    async def auto_subscribe_topic(self):
        """Automatically subscribe to an available topic"""
        # Get all topics from DHT
        all_topics = set()
        for topic_hash in self.dht.table.keys():
            topic_name = self.dht.get_original_name(topic_hash)
            if topic_name:
                all_topics.add(topic_name)
        
        # Get unsubscribed topics
        available_topics = all_topics - self.subscribed_topics
        
        if available_topics:
            # Choose a random topic to subscribe to
            topic_name = random.choice(list(available_topics))
            self.subscribed_topics.add(topic_name)
            if topic_name not in self.unread_messages:
                self.unread_messages[topic_name] = []
            logging.info(f'Subscribed to topic: {topic_name}')
            
            # Broadcast subscription to peers
            message_data = {
                'type': 'subscribe',
                'topic': topic_name,
                'subscriber': self.peer_id
            }
            await self.broadcast_message(message_data)
        else:
            logging.info('No available topics to subscribe to')

    async def handle_peer(self, reader, writer):
        while True:
            try:
                data = await reader.read(1024)
                if not data:
                    break
                
                message = json.loads(data.decode())
                await self.handle_message(message)
                
            except Exception as e:
                logging.error(f"Error handling peer message: {str(e)}")
                break
    
    async def broadcast_topic_creation(self, topic_name):
        """Broadcast topic creation to all connected peers"""
        message_data = {
            'type': 'topic_sync',
            'topics': [topic_name]
        }
        
        for peer_id, (reader, writer) in self.connected_peers.items():
            try:
                writer.write(json.dumps(message_data).encode('utf-8'))
                await writer.drain()
                logging.info(f'Broadcasted topic creation to peer {peer_id}')
            except Exception as e:
                logging.error(f'Failed to broadcast topic to peer {peer_id}: {str(e)}')
    
    async def broadcast_message(self, message_data):
        """Broadcast a message to all connected peers"""
        for peer_id, (reader, writer) in self.connected_peers.items():
            try:
                writer.write(json.dumps(message_data).encode('utf-8'))
                await writer.drain()
            except Exception as e:
                logging.error(f'Failed to broadcast to peer {peer_id}: {str(e)}')

    async def handle_message(self, message_data):
        """Handle incoming messages with proper error handling."""
        try:
            if message_data['type'] == 'topic_sync':
                topics = message_data.get('topics', [])
                if isinstance(topics, (list, tuple)):
                    for topic in topics:
                        if not self.dht.contains(topic):
                            self.dht.put(topic, [])
                            self.unread_messages[topic] = []
            
            elif message_data['type'] == 'subscribe':
                topic_name = message_data.get('topic')
                subscriber = message_data.get('subscriber')
                if topic_name and subscriber:
                    if not self.dht.contains(topic_name):
                        self.dht.put(topic_name, [])
                    logging.info(f'Peer {subscriber} subscribed to topic {topic_name}')
            
            elif message_data['type'] == 'message':
                topic_name = message_data.get('topic')
                message = message_data.get('message')
                if topic_name and message:
                    if not self.dht.contains(topic_name):
                        self.dht.put(topic_name, [])
                    messages = self.dht.get(topic_name) or []
                    messages.append(message)
                    self.dht.put(topic_name, messages)
                    if topic_name in self.subscribed_topics:
                        self.unread_messages.setdefault(topic_name, []).append(message)
                        logging.info(f'Received message in subscribed topic {topic_name}: {message}')
        
        except Exception as e:
            logging.error(f"Error handling message: {str(e)}")

    async def log_subscription_status(self):
        """Periodically log subscription status"""
        while True:
            await asyncio.sleep(10)  # Log every 10 seconds
            if self.subscribed_topics:
                logging.info(f'Currently subscribed to topics: {list(self.subscribed_topics)}')
            else:
                logging.info('Not subscribed to any topics')


    async def start(self):
        server = await asyncio.start_server(self.handle_peer, 'localhost', self.port)
        print(f"{Colors.OKGREEN}Peer {self.peer_id} running on port {self.port}{Colors.ENDC}")
        logging.info(f'Peer started on port {self.port}')
        
        # Start automated operations and logging
        asyncio.create_task(self.automated_operations())
        asyncio.create_task(self.log_subscription_status())
        
        async with server:
            await server.serve_forever()
    
    async def publish_to_topic(self, topic_name, message):
        if topic_name in self.subscribed_topics:
            messages = self.dht.get(topic_name)
            messages.append(message)
            self.dht.put(topic_name, messages)
            logging.info(f'Published to topic {topic_name}: {message}')
            
            # Broadcast to subscribers
            await self.broadcast_message({
                'type': 'publish',
                'topic': topic_name,
                'message': message
            })

    async def broadcast_message(self, message):
        """Broadcast a message to all connected peers"""
        for peer_id, (reader, writer) in self.connected_peers.items():
            try:
                writer.write(json.dumps(message).encode())
                await writer.drain()
            except Exception as e:
                logging.error(f"Failed to broadcast to peer {peer_id}: {str(e)}")

    async def connect_to_neighbors(self):
        """Connect to neighboring nodes in the hypercube"""
        for i in range(3):  # 3-bit IDs
            neighbor_id = list(self.peer_id)
            neighbor_id[i] = '1' if neighbor_id[i] == '0' else '0'
            neighbor_id = ''.join(neighbor_id)
            
            if neighbor_id not in self.connected_peers:
                try:
                    port = 8000 + int(neighbor_id, 2)
                    reader, writer = await asyncio.open_connection(
                        'localhost', port
                    )
                    self.connected_peers[neighbor_id] = (reader, writer)
                    logging.info(f'Connected to neighbor {neighbor_id}')
                except Exception as e:
                    logging.error(f"Failed to connect to neighbor {neighbor_id}: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python peer_node.py <peer_id> <port>")
        sys.exit(1)

    peer_id = sys.argv[1]
    port = int(sys.argv[2])
    
    peer = PeerNode(peer_id, port)
    asyncio.run(peer.start())