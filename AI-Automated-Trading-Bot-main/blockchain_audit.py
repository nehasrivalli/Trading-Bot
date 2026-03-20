import hashlib
import json
import time
from typing import List, Dict, Any
import sqlite3

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block"""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()
    
    def mine_block(self, difficulty: int) -> None:
        """Mine a block (Proof of Work)"""
        target = "0" * difficulty
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        
        print(f"Block mined: {self.hash}")

class Blockchain:
    def __init__(self, difficulty: int = 2):
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.pending_transactions: List[Dict[str, Any]] = []
        
        # Initialize SQLite database for persistent storage first
        self.init_db()
        
        # Create genesis block after database is initialized
        self.create_genesis_block()
    
    def init_db(self) -> None:
        """Initialize SQLite database for blockchain storage"""
        self.conn = sqlite3.connect("blockchain.db")
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        # Note: 'index' is a reserved keyword in SQLite, so we use "block_index" instead
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY,
            block_index INTEGER,
            timestamp REAL,
            transactions TEXT,
            previous_hash TEXT,
            nonce INTEGER,
            hash TEXT
        )
        ''')
        self.conn.commit()
        
        # Load existing blockchain from database
        self.load_blockchain()
    
    def load_blockchain(self) -> None:
        """Load blockchain from database"""
        self.cursor.execute("SELECT * FROM blocks ORDER BY block_index")
        rows = self.cursor.fetchall()
        
        if not rows:
            return
        
        # Clear existing chain
        self.chain = []
        
        # Load blocks from database
        for row in rows:
            _, block_index, timestamp, transactions_json, previous_hash, nonce, hash_value = row
            transactions = json.loads(transactions_json)
            
            block = Block(block_index, timestamp, transactions, previous_hash)
            block.nonce = nonce
            block.hash = hash_value
            
            self.chain.append(block)
    
    def save_block(self, block: Block) -> None:
        """Save block to database"""
        self.cursor.execute('''
        INSERT INTO blocks (block_index, timestamp, transactions, previous_hash, nonce, hash)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (block.index, block.timestamp, json.dumps(block.transactions), block.previous_hash, block.nonce, block.hash))
        self.conn.commit()
    
    def create_genesis_block(self) -> None:
        """Create the first block in the chain (genesis block)"""
        genesis_block = Block(0, time.time(), [], "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        
        # Save genesis block to database
        self.save_block(genesis_block)
    
    def get_latest_block(self) -> Block:
        """Get the latest block in the blockchain"""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Dict[str, Any]) -> int:
        """Add a new transaction to the list of pending transactions"""
        # Add timestamp to transaction
        transaction['timestamp'] = time.time()
        
        # Add transaction to pending transactions
        self.pending_transactions.append(transaction)
        
        # Return the index of the block that will hold this transaction
        return self.get_latest_block().index + 1
    
    def mine_pending_transactions(self, mining_reward_address: str) -> None:
        """Mine pending transactions and add a new block to the chain"""
        # Create reward transaction
        reward_transaction = {
            "from": "SYSTEM",
            "to": mining_reward_address,
            "amount": 1,  # Mining reward
            "timestamp": time.time(),
            "type": "REWARD"
        }
        
        # Add reward transaction to pending transactions
        self.pending_transactions.append(reward_transaction)
        
        # Create new block
        block = Block(
            len(self.chain),
            time.time(),
            self.pending_transactions,
            self.get_latest_block().hash
        )
        
        # Mine block
        block.mine_block(self.difficulty)
        
        # Add block to chain
        self.chain.append(block)
        
        # Save block to database
        self.save_block(block)
        
        # Reset pending transactions
        self.pending_transactions = []
    
    def is_chain_valid(self) -> bool:
        """Validate the blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if hash is correct
            if current_block.hash != current_block.calculate_hash():
                print("Invalid hash")
                return False
            
            # Check if previous hash reference is correct
            if current_block.previous_hash != previous_block.hash:
                print("Invalid previous hash reference")
                return False
        
        return True
    
    def get_balance(self, address: str) -> float:
        """Get the balance of an address"""
        balance = 0
        
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.get("to") == address:
                    balance += transaction.get("amount", 0)
                
                if transaction.get("from") == address:
                    balance -= transaction.get("amount", 0)
        
        return balance
    
    def get_transactions_for_address(self, address: str) -> List[Dict[str, Any]]:
        """Get all transactions for a specific address"""
        transactions = []
        
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.get("to") == address or transaction.get("from") == address:
                    transactions.append(transaction)
        
        return transactions
    
    def close(self) -> None:
        """Close database connection"""
        self.conn.close()


# Audit Log Functions
def log_trade_to_blockchain(blockchain: Blockchain, trade_data: Dict[str, Any]) -> None:
    """Log a trade to the blockchain"""
    transaction = {
        "type": "TRADE",
        "from": trade_data.get("trader", "SYSTEM"),
        "to": "MARKET",
        "symbol": trade_data.get("symbol"),
        "trade_type": trade_data.get("trade_type"),
        "price": trade_data.get("price"),
        "quantity": trade_data.get("quantity"),
        "timestamp": time.time()
    }
    
    blockchain.add_transaction(transaction)
    
    # Mine block if there are enough pending transactions
    if len(blockchain.pending_transactions) >= 5:
        blockchain.mine_pending_transactions("SYSTEM")

def log_fraud_alert_to_blockchain(blockchain: Blockchain, alert_data: Dict[str, Any]) -> None:
    """Log a fraud alert to the blockchain"""
    transaction = {
        "type": "FRAUD_ALERT",
        "from": "FRAUD_DETECTION_SYSTEM",
        "to": "SECURITY_TEAM",
        "alert_type": alert_data.get("alert_type"),
        "trader": alert_data.get("trader"),
        "symbol": alert_data.get("symbol"),
        "details": alert_data.get("details"),
        "timestamp": time.time()
    }
    
    blockchain.add_transaction(transaction)
    blockchain.mine_pending_transactions("SYSTEM")

def verify_trade_integrity(blockchain: Blockchain, trade_id: str) -> bool:
    """Verify the integrity of a trade in the blockchain"""
    for block in blockchain.chain:
        for transaction in block.transactions:
            if transaction.get("type") == "TRADE" and transaction.get("id") == trade_id:
                # The trade exists in the blockchain, which means it's verified
                return True
    
    return False


if __name__ == "__main__":
    # Create blockchain
    blockchain = Blockchain(difficulty=2)
    
    # Test logging a trade
    trade_data = {
        "trader": "Trader_A",
        "symbol": "BTCUSDT",
        "trade_type": "BUY",
        "price": 65000,
        "quantity": 0.5
    }
    
    log_trade_to_blockchain(blockchain, trade_data)
    
    # Test logging a fraud alert
    alert_data = {
        "alert_type": "SUSPICIOUS_VOLUME",
        "trader": "Trader_B",
        "symbol": "BTCUSDT",
        "details": "Unusually large trade volume detected"
    }
    
    log_fraud_alert_to_blockchain(blockchain, alert_data)
    
    # Verify chain integrity
    print(f"Blockchain valid: {blockchain.is_chain_valid()}")
    
    # Close blockchain
    blockchain.close()