import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Creating Blockchain

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
    
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain)+1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions
                 }
        self.transactions = []
        self.chain.append(block)
        return block
    
    def get_prev_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof == False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:6] == '000000':
                check_proof = True
            else:
                new_proof = new_proof+1
        return new_proof
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:6] != '000000':
                return False
            previous_block = block
            block_index = block_index + 1
        return True
    
    def add_transaction(self, sender, reciever, amount):
        self.transactions.append({'sender': sender,
                                  'reciever': reciever,
                                  'amount': amount})
        previous_block = self.get_prev_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json(['chain'])
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

# Creating Flask Web App

app = Flask(__name__)

# Address for node on Port 5000

node_address = str(uuid4()).replace('-', '')

# Creating item Blockchain

heisenberg = Blockchain()

# Mining block

@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = heisenberg.get_prev_block()
    previous_proof = previous_block['proof']
    proof = heisenberg.proof_of_work(previous_proof)
    previous_hash = heisenberg.hash(previous_block)
    heisenberg.add_transaction(sender = node_address, reciever = 'User', amount = 1)
    block = heisenberg.create_block(proof, previous_hash)
    response = {'message': 'Congratulations! You just mined a block. This block will now be added to the blockchain',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

# Getting the full chain

@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': heisenberg.chain,
                'length': len(heisenberg.chain)}
    return jsonify(response), 200

# Validity

@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = heisenberg.is_chain_valid(heisenberg.chain)
    if is_valid:
        response = {'message': 'The Blockchain is valid.'}
    else:
        response = {'message': 'The Blockchain is vulnerable.'}
    return jsonify(response), 200

# Adding transactions

@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'reciever', 'amount']
    if not all (key in json for key in transaction_keys):
        return 'Transaction is invalid', 400
    index = heisenberg.add_transaction(json['sender'], json['reciever'], json['amount'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201

# Decentralization

# Connecting nodes

@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'no node', 400
    for node in nodes:
        heisenberg.add_node(node)
    response = {'message': 'All the nodes are connected. The Heisenberg Blockchain now contains the following nodes: ',
                'total nodes': list(heisenberg.nodes)}
    return jsonify(response), 201

# Replacing chains by longest one (if needed)

@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = heisenberg.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest chain',
                    'new_chain': heisenberg.chain}
    else:
        response = {'message': 'All good, the chain is the largest one.',
                    'actual_chain': heisenberg.chain}
    return jsonify(response), 200

# Running the app

app.run(host = '0.0.0.0', port = 5000)

