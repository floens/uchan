import logging

from flask import request as request_ctx

from uchan.lib.exceptions import ArgumentError

logger = logging.getLogger(__name__)


def get_request_ip4_str(request=None):
    # You must set the correct config.USE_PROXY_FIXER and config.PROXY_FIXER_NUM_PROXIES
    # settings for this to return the correct value
    return request.remote_addr if request else request_ctx.remote_addr


def get_request_ip4(request=None):
    try:
        ip4 = parse_ip4(get_request_ip4_str(request))
    except ValueError as e:
        logger.exception("Failed to parse request ip4")
        raise ArgumentError("Invalid request") from e
    return ip4


def parse_ip4(ip4_str):
    ip_parts = ip4_str.split(".")
    if len(ip_parts) != 4:
        raise ValueError()

    ip_nums = []
    for ip_part in ip_parts:
        if ip_part == "*":
            ip_nums.append(0)
        else:
            n = int(ip_part)
            if n < 0 or n > 255:
                raise ValueError()
            ip_nums.append(n)

    return (ip_nums[0] << 24) + (ip_nums[1] << 16) + (ip_nums[2] << 8) + ip_nums[3]
