from flask import request


def get_request_ip4_str():
    # You must set the correct config.USE_PROXY_FIXER and config.PROXY_FIXER_NUM_PROXIES settings for this to return the correct value
    return request.remote_addr
