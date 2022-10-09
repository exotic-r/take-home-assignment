class TransactionNotFoundException(Exception):
    def __init__(self, tx_hash):
        self.tx_hash = tx_hash

    def __str__(self):
        return f'No transaction found tx_hash: {self.tx_hash}'

class TransactionNotFoundExceptionByTimeRange(Exception):
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        return f'No transaction found between {self.start_time} and {self.end_time}'
