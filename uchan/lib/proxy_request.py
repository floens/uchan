from flask import request
from uchan import g
from uchan.lib import ArgumentError


def get_request_ip4_str():
    # You must set the correct config.USE_PROXY_FIXER and config.PROXY_FIXER_NUM_PROXIES settings for this to return the correct value
    return request.remote_addr


def get_request_ip4():
    try:
        ip4 = parse_ip4(get_request_ip4_str())
    except ValueError:
        g.logger.exception('Failed to parse request ip4')
        raise ArgumentError('Invalid request')
    return ip4


def parse_ip4(ip4_str):
    ip_parts = ip4_str.split('.')
    if len(ip_parts) != 4:
        raise ValueError()

    ip_nums = []
    for ip_part in ip_parts:
        if ip_part == '*':
            ip_nums.append(0)
        else:
            n = int(ip_part)
            if n < 0 or n > 255:
                raise ValueError()
            ip_nums.append(n)

    return (ip_nums[0] << 24) + (ip_nums[1] << 16) + (ip_nums[2] << 8) + ip_nums[3]
