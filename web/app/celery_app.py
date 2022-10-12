from redis.client import Redis
from celery import Celery

from cryptoService import CryptoService

celery = Celery(
    'worker',
    broker='redis://redis:6379',
    backend='redis://redis:6379'
)
redis = Redis(host='redis', port=6379)
service = CryptoService(redis)


@celery.task(name='tasks.get_historic_transaction')
def get_historic_transaction():
    service.request_fees(start_block, end_block)