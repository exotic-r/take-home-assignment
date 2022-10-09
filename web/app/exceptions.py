class TransactionNotFoundException(Exception):
    def __init__(self, tx_hash):
        self.tx_hash = tx_hash

    def __str__(self):
        return f'No transaction found tx_hash: {self.tx_hash}'
