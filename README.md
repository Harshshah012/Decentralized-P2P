# P2P Publisher-Subscriber System

This project implements a Peer-to-Peer (P2P) Publisher-Subscriber system using a Distributed Hash Table (DHT) and a hypercube topology for efficient message routing between peers.

## Features

- **Distributed Hash Table (DHT):** Decentralized storage of topics and messages.
- **Hypercube Topology:** Efficient message routing between peer nodes.
- **Topic Management:** Create, delete, and list available topics.
- **Subscription Mechanism:** Subscribe to topics and pull messages from subscribed topics.
- **Message Publishing:** Publish messages to topics in the network.
- **Peer-to-Peer Connections:** Direct connections between peers without a central server.
- **Asynchronous Communication:** Non-blocking message passing using Python's `asyncio` library.

## Requirements

- Python 3.7+
- `asyncio` library (included with Python 3.7+)

## Usage

To start a peer node, run:

```bash
python3 Test1.py <peer_id> <port>
```

Where:
- `<peer_id>` is a unique 3-bit binary identifier for the peer node (e.g., `000`, `001`, `010`, etc.).
- `<port>` is a port number between 1 and 65535.

If no arguments are provided, the program will prompt you to enter these values.

## Makefile Targets

This project includes a `Makefile` with the following targets:

- **`make run`**: Runs the main `DecentralizedP2P.py` script.
- **`make Test1`**: Deploys peer nodes using `deploy_peers.py`.
- **`make Test2`**: Runs the `PeerBenchmark.py` script for performance testing.
- **`make Test3`**: Executes the `Hashtest.py` script for hash function testing.
- **`make Test4`**: Runs the `forwardinganalysis.py` script for network analysis.
- **`make Extracredit`**: Executes the `Extracredit.py` script for additional features.
- **`make clean`**: Stops all running peer processes and performs cleanup.
- **`make stop`**: Stops all running peer processes.

To use these targets, simply run:

```bash
make <target>
```

## Menu Options

Once the peer node is running, you will see a command-line menu with the following options:

1. **Create Topic**: Initiate a new topic in the DHT.
2. **Delete Topic**: Remove an existing topic from the DHT.
3. **List Available Topics**: View all topics in the network.
4. **Subscribe to Topic**: Subscribe to a specific topic to receive updates.
5. **Pull Messages**: Retrieve new messages from subscribed topics.
6. **Connect to Peer**: Connect to another peer node within the network.
7. **Publish Message**: Publish a message to a topic for subscribers.
8. **Exit**: Disconnect the peer node and exit the program.
