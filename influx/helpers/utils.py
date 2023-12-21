import re

INTERVAL_MAPPING = {
    'u': 0.000001,  # 'u': 1 / 1000000,
    'ms': 0.001,  # 'ms': 1 / 1000,
    's': 1,
    'm': 60,
    'h': 3600,
    'd': 86400,
    'w': 604800,
}


def inv(x):
    return 1 / x if x else 0


def generate_interval_string(interval):
    seconds = int(interval.total_seconds())
    if seconds < 60:
        return f'{seconds}s'
    m, s = divmod(seconds, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        if h >= 24:
            d, h = divmod(h, 24)
            return f'{d}d'
        return f'{h}h'
    return f'{m}m'


def generate_seconds(interval):
    # regex to separate the number from the unit
    pattern = re.compile(r'(\d+)([a-z]+)')
    match = pattern.match(interval)
    if match:
        value, unit = match.groups()
        return int(value) * INTERVAL_MAPPING[unit]
    else:
        raise ValueError(f'Invalid interval: {interval}')
