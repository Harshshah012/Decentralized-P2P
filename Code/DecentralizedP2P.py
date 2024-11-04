import asyncio
import json
import hashlib
import logging

# ANSI escape codes for colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class DHT:
    def __init__(self):
        self.table = {}  # DHT table to store topics
        self.topic_mapping = {}  # Maps hash to original topic name

    def _hash_topic(self, topic_name):
        """Generate a hash for the topic name."""
        return hashlib.sha256(topic_name.encode()).hexdigest()

    def put(self, topic_name, messages):
        """Store the topic and its messages in the DHT."""
        topic_hash = self._hash_topic(topic_name)
        self.table[topic_hash] = messages
        self.topic_mapping[topic_hash] = topic_name

    def get(self, topic_name):
        """Retrieve messages for a given topic from the DHT."""
        topic_hash = self._hash_topic(topic_name)
        return self.table.get(topic_hash, None)

    def remove(self, topic_name):
        """Remove a topic from the DHT."""
        topic_hash = self._hash_topic(topic_name)
        if topic_hash in self.table:
            del self.table[topic_hash]
            del self.topic_mapping[topic_hash]

    def contains(self, topic_name):
        """Check if the DHT contains a topic."""
        topic_hash = self._hash_topic(topic_name)
        return topic_hash in self.table

    def get_original_name(self, topic_hash):
        """Get original topic name from hash."""
        return self.topic_mapping.get(topic_hash)

class PeerNode:
    def __init__(self, peer_id, port):
        self.peer_id = peer_id
        self.port = port
        self.connected_peers = {}  # Stores peer_id -> (reader, writer)
        self.dht = DHT()  # Initialize DHT for storing topics and messages
        self.unread_messages = {}  # Tracks unread messages per topic
        self.subscribed_topics = set()  # Tracks which topics this peer is subscribed to

        # Setup logging
        logging.basicConfig(filename=f'{self.peer_id}_log.txt', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    async def start(self):
        server = await asyncio.start_server(self.handle_peer, 'localhost', self.port)
        print(f"{Colors.OKGREEN}Peer Node {self.peer_id} running on port {self.port}{Colors.ENDC}")
        logging.info(f'Peer Node {self.peer_id} started on port {self.port}')
        
        # Start the run loop in the background
        asyncio.create_task(self.run())
        
        async with server:
            await server.serve_forever()

    async def handle_peer(self, reader, writer):
        while True:
            try:
                data = await reader.read(1024)
                if not data:
                    break

                message_data = json.loads(data.decode('utf-8'))
                
                if message_data['type'] == 'route':
                    # Handle routed messages
                    if message_data['target'] == self.peer_id:
                        await self.handle_message(message_data['data'])
                    else:
                        await self.route_request(message_data['target'], message_data['data'])
                else:
                    # Handle regular messages
                    await self.handle_message(message_data)

            except ConnectionResetError:
                break
            except json.JSONDecodeError:
                logging.error("Received malformed JSON data.")
            except Exception as e:
                logging.error(f"Error handling peer message: {str(e)}")

    async def connect_peer(self):
        """Connect to peer with proper error handling and validation."""
        peer_id = await asyncio.to_thread(input, "Enter peer ID to connect (3-bit binary): ")
        if not peer_id or len(peer_id) != 3 or not all(c in '01' for c in peer_id):  # Validate 3-bit binary ID
            print(f"{Colors.FAIL}Invalid peer ID format. Must be 3-bit binary.{Colors.ENDC}")
            return
            
        try:
            port = int(await asyncio.to_thread(input, "Enter peer port (1-65535): "))
            if not (1 <= port <= 65535):
                print(f"{Colors.FAIL}Port number must be between 1 and 65535.{Colors.ENDC}")
                return

            if peer_id not in self.connected_peers:
                reader, writer = await asyncio.open_connection('localhost', port)
                self.connected_peers[peer_id] = (reader, writer)
                print(f"{Colors.OKGREEN}Connected to Peer: {peer_id}{Colors.ENDC}")
                await self.sync_topics(writer)
        except ValueError:
            print(f"{Colors.FAIL}Invalid port number.{Colors.ENDC}")
        except ConnectionRefusedError:
            print(f"{Colors.FAIL}Connection refused by peer {peer_id}.{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Error connecting to peer: {str(e)}{Colors.ENDC}")

    async def sync_topics(self, writer):
        """Send current topics to the connected peer."""
        message_data = {
            'type': 'topic_sync',
            'topics': [self.dht.get_original_name(h) for h in self.dht.table.keys()]
        }
        writer.write(json.dumps(message_data).encode('utf-8'))
        await writer.drain()
        logging.info(f'Sent topic sync to connected peer.')

    async def create_topic(self):
        topic_name = await asyncio.to_thread(input, "Enter topic name to create: ")
        if self.dht.contains(topic_name):
            print(f"{Colors.WARNING}Topic '{topic_name}' already exists.{Colors.ENDC}")
            logging.warning(f'Topic "{topic_name}" already exists.')
            return
        
        self.dht.put(topic_name, [])
        self.unread_messages[topic_name] = []
        self.subscribed_topics.add(topic_name)
        print(f"{Colors.OKGREEN}Topic '{topic_name}' created and subscribed.{Colors.ENDC}")
        logging.info(f'Topic "{topic_name}" created and subscribed.')
        
        for peer_id, (reader, writer) in self.connected_peers.items():
            try:
                message_data = {
                    'type': 'topic_sync',
                    'topics': [topic_name]
                }
                writer.write(json.dumps(message_data).encode('utf-8'))
                await writer.drain()
            except Exception as e:
                print(f"{Colors.FAIL}Failed to notify Peer {peer_id} about new topic: {str(e)}{Colors.ENDC}")
                logging.error(f'Failed to notify Peer {peer_id} about new topic: {str(e)}')

    async def delete_topic(self):
        topic_name = await asyncio.to_thread(input, "Enter topic name to delete: ")
        if not self.dht.contains(topic_name):
            print(f"{Colors.WARNING}Topic '{topic_name}' does not exist.{Colors.ENDC}")
            logging.warning(f'Topic "{topic_name}" does not exist.')
            return
        
        self.dht.remove(topic_name)
        self.unread_messages.pop(topic_name, None)
        self.subscribed_topics.discard(topic_name)
        print(f"{Colors.OKGREEN}Topic '{topic_name}' deleted successfully.{Colors.ENDC}")
        logging.info(f'Topic "{topic_name}" deleted successfully.')
        
        for peer_id, (reader, writer) in self.connected_peers.items():
            try:
                message_data = {
                    'type': 'delete_topic',
                    'topics': [topic_name]
                }
                writer.write(json.dumps(message_data).encode('utf-8'))
                await writer.drain()
            except Exception as e:
                print(f"{Colors.FAIL}Failed to notify Peer {peer_id} about deleted topic: {str(e)}{Colors.ENDC}")
                logging.error(f'Failed to notify Peer {peer_id} about deleted topic: {str(e)}')

    async def list_available_topics(self):
        if not self.dht.table:
            print(f"{Colors.WARNING}No topics available.{Colors.ENDC}")
            logging.warning(f'No topics available to list.')
        else:
            print("\nAvailable Topics:")
            for idx, topic_hash in enumerate(self.dht.table.keys(), start=1):
                original_name = self.dht.get_original_name(topic_hash)
                status = "Subscribed" if original_name in self.subscribed_topics else "Not Subscribed"
                print(f"{idx}. {original_name} [{status}]")
            logging.info(f'Listed available topics.')

    async def subscribe_to_topic(self):
        available_topics = []
        
        # List available topics from local DHT
        for topic_hash in self.dht.table.keys():
            original_name = self.dht.get_original_name(topic_hash)
            if original_name not in self.subscribed_topics:
                available_topics.append((topic_hash, original_name))

        if not available_topics:
            print(f"{Colors.WARNING}No topics available locally. Checking remote peers...{Colors.ENDC}")
            
            # Ask remote peers for topics (route request)
            message_data = {
                'type': 'list_topics',
                'requesting_peer': self.peer_id
            }
            
            # Route message through hypercube
            await self.route_request(target_peer_id='000', message_data=message_data)  # Example: route towards Peer 000
        
        else:
            print("\nAvailable Topics to Subscribe:")
            for idx, (_, original_name) in enumerate(available_topics, start=1):
                print(f"{idx}. {original_name}")
            
            try:
                choice = int(await asyncio.to_thread(input, "Select a topic number to subscribe: "))
                
                if 1 <= choice <= len(available_topics):
                    _, topic_name = available_topics[choice - 1]
                    self.subscribed_topics.add(topic_name)
                    if topic_name not in self.unread_messages:
                        self.unread_messages[topic_name] = []
                    print(f"{Colors.OKGREEN}Subscribed to topic '{topic_name}'.{Colors.ENDC}")
                    logging.info(f'Subscribed to topic "{topic_name}".')
                else:
                    print(f"{Colors.FAIL}Invalid choice.{Colors.ENDC}")
                    logging.error('Invalid choice for subscribing to topic.')
            
            except ValueError:
                print(f"{Colors.FAIL}Invalid input. Please enter a number.{Colors.ENDC}")
                logging.error('Invalid input for subscribing to topic.')

    def calculate_hamming_distance(self, id1, id2):
        """Calculate Hamming distance between two peer IDs."""
        return sum(c1 != c2 for c1, c2 in zip(id1, id2))

    async def route_request(self, target_peer_id, message_data):
        """Route request through hypercube topology using greedy forwarding."""
        if target_peer_id == self.peer_id:
            await self.handle_message(message_data)
            return
        
        current_distance = self.calculate_hamming_distance(self.peer_id, target_peer_id)
        neighbors = self.get_neighbors()
        best_next_hop = None
        min_distance = current_distance

        for neighbor in neighbors:
            distance = self.calculate_hamming_distance(neighbor, target_peer_id)
            if distance < min_distance:
                min_distance = distance
                best_next_hop = neighbor

        if best_next_hop and best_next_hop in self.connected_peers:
            try:
                reader, writer = self.connected_peers[best_next_hop]
                routing_data = {
                    'type': 'route',
                    'target': target_peer_id,
                    'data': message_data,
                    'path': message_data.get('path', []) + [self.peer_id]
                }
                writer.write(json.dumps(routing_data).encode('utf-8'))
                await writer.drain()
                logging.info(f'Using alternative route via {best_next_hop}')
                return
            except Exception:
                logging.error(f'Failed to send message to {best_next_hop}')
                return

        logging.error(f'All routing attempts failed for target {target_peer_id}')

    async def handle_message(self, message_data):
        """Handle incoming messages with proper error handling."""
        try:
            if message_data['type'] == 'topic_sync':
                for topic in message_data.get('topics', []):
                    if not self.dht.contains(topic):
                        self.dht.put(topic, [])
                        self.unread_messages[topic] = []
            elif message_data['type'] == 'message':
                topic_name = message_data.get('topic')
                message = message_data.get('message')
                if topic_name and message:
                    if not self.dht.contains(topic_name):
                        self.dht.put(topic_name, [])
                    messages = self.dht.get(topic_name)
                    messages.append(message)
                    self.dht.put(topic_name, messages)
                    if topic_name in self.subscribed_topics:
                        if topic_name not in self.unread_messages:
                            self.unread_messages[topic_name] = []
                        self.unread_messages[topic_name].append(message)
        except Exception as e:
            logging.error(f"Error handling message: {str(e)}")

    def get_neighbors(self):
        """Calculate neighbors in hypercube topology based on binary ID."""
        neighbors = []
        for i in range(3):  # For 8 nodes (3-bit IDs)
            if len(self.peer_id) > i:  # Add length check
                neighbor_id = list(self.peer_id)
                neighbor_id[i] = '1' if self.peer_id[i] == '0' else '0'
                neighbors.append(''.join(neighbor_id))
        return neighbors
    
    def get_next_hop(self, target_peer_id):
        """Get the next hop closer to the target_peer_id."""
        # Find which bit differs between self.peer_id and target_peer_id and flip that bit
        for i in range(len(self.peer_id)):
            if self.peer_id[i] != target_peer_id[i]:
                next_hop = list(self.peer_id)
                next_hop[i] = target_peer_id[i]  # Flip the differing bit
                return ''.join(next_hop)
        return None


    async def try_alternative_route(self, target_peer_id, message_data):
            """Try alternative path if primary route fails."""
            neighbors = self.get_neighbors()
            for neighbor in neighbors:
                if neighbor in self.connected_peers:
                    try:
                        reader, writer = self.connected_peers[neighbor]
                        routing_data = {
                            'type': 'route',
                            'target': target_peer_id,
                            'data': message_data,
                            'path': message_data.get('path', []) + [self.peer_id]
                        }
                        writer.write(json.dumps(routing_data).encode('utf-8'))
                        await writer.drain()
                        logging.info(f'Using alternative route via {neighbor}')
                        return
                    except Exception:
                        continue
            logging.error(f'All routing attempts failed for target {target_peer_id}')


    async def publish_message(self):
        topic_name = await asyncio.to_thread(input, "Enter topic to publish message: ")
        
        # Check if topic exists in DHT
        if not self.dht.contains(topic_name):
            print(f"{Colors.FAIL}Topic '{topic_name}' does not exist.{Colors.ENDC}")
            return
            
        if topic_name not in self.subscribed_topics:
            print(f"{Colors.FAIL}You are not subscribed to '{topic_name}'. Subscribe first before publishing.{Colors.ENDC}")
            return
            
        message = await asyncio.to_thread(input, "Enter message: ")
        messages = self.dht.get(topic_name)
        messages.append(message)
        self.dht.put(topic_name, messages)
        
        # Add to unread messages for subscribers
        if topic_name not in self.unread_messages:
            self.unread_messages[topic_name] = []
        self.unread_messages[topic_name].append(message)
        
        # Broadcast to connected peers
        for peer_id, (reader, writer) in self.connected_peers.items():
            try:
                message_data = {
                    'type': 'message',
                    'topic': topic_name,
                    'message': message
                }
                writer.write(json.dumps(message_data).encode('utf-8'))
                await writer.drain()
            except Exception as e:
                print(f"{Colors.FAIL}Failed to send message to Peer {peer_id}: {str(e)}{Colors.ENDC}")

    async def pull_messages(self):
        if not self.unread_messages:
            print(f"{Colors.WARNING}No unread messages.{Colors.ENDC}")
            logging.warning('No unread messages to pull.')
            return

        print("\nUnread Messages:")
        for topic_name, messages in self.unread_messages.items():
            if messages:
                print(f"Topic: {topic_name}")
                for message in messages:
                    print(f" - {message}")
                self.unread_messages[topic_name] = []  # Clear messages after displaying
            else:
                print(f"Topic: {topic_name} has no unread messages.")
        logging.info('Pulled unread messages.')

    async def run(self):
        while True:
            print("\nMenu:")
            print("1. Create Topic")
            print("2. Delete Topic")
            print("3. List Available Topics")
            print("4. Subscribe to Topic")
            print("5. Pull Messages")
            print("6. Connect to Peer")
            print("7. Publish Message")  # Add option to publish message
            print("8. Exit")
            
            try:
                choice = int(await asyncio.to_thread(input, "Select an option: "))
                if choice == 1:
                    await self.create_topic()
                elif choice == 2:
                    await self.delete_topic()
                elif choice == 3:
                    await self.list_available_topics()
                elif choice == 4:
                    await self.subscribe_to_topic()
                elif choice == 5:
                    await self.pull_messages()
                elif choice == 6:
                    await self.connect_peer()
                elif choice == 7:
                    await self.publish_message()  # Call the publish message method
                elif choice == 8:
                    print(f"{Colors.OKGREEN}Exiting Peer Node...{Colors.ENDC}")
                    logging.info('Peer Node exited.')
                    break
                else:
                    print(f"{Colors.FAIL}Invalid choice. Please try again.{Colors.ENDC}")
            except ValueError:
                print(f"{Colors.FAIL}Invalid input. Please enter a number.{Colors.ENDC}")
                logging.error('Invalid input in menu selection.')

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 3:
        peer_id = sys.argv[1]
        port = int(sys.argv[2])
    else:
        peer_id = input("Enter your Peer ID (3-bit binary): ")
        port = int(input("Enter your port number (1-65535): "))
    
    peer_node = PeerNode(peer_id, port)
    asyncio.run(peer_node.start())