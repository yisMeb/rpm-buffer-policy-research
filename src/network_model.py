def outages(start, duration, repeats=1):
    if duration <= 0:
        return []
    return [(start + i * (duration + 600), start + i * (duration + 600) + duration) for i in range(repeats)]


def available(t, trace, reconnect_delay=0):
    return all(not (a <= t < b + reconnect_delay) for a, b in trace)
