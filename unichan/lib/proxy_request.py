from flask import request


def get_ip4():
    return request.remote_addr
