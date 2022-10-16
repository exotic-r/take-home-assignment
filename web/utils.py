from config import *


def get_ether_scan_params(start_block, end_block, page, offset=10) -> dict:
    return {
        'module': 'account',
        'action': 'tokentx',
        'address': UNISWAP_ADDRESS,
        'page': page,
        'offset': offset,
        'startblock': start_block,
        'endblock': end_block,
        'sort': 'asc',
        'apikey': ETHER_SCAN_API_KEY,
    }
