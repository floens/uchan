import time


def now():
    return int(time.time() * 1000)


def ip4_to_str(ip4):
    outputs = []
    for i in range(4):
        n = (ip4 >> (3 - i) * 8) & 255
        outputs.append(str(n))

    return '.'.join(outputs)
