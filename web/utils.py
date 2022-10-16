from config import *


def get_ether_scan_params(start_block, end_block, page, action_type) -> dict:
    return {
        'module': 'account',
        'action': action_type,
        'address': UNISWAP_ADDRESS,
        'page': page,
        'offset': ETHER_SCAN_OFFSET,
        'startblock': start_block,
        'endblock': end_block,
        'sort': 'asc',
        'apikey': ETHER_SCAN_API_KEY,
    }
