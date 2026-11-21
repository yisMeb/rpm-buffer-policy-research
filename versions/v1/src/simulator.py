from dataclasses import dataclass
from .buffer_policies import admit
from .network_model import available


@dataclass
class Result:
    readings: list
    delivered: list
    dropped: set
    pending: list
    occupancy: list
    events: list
    end: float
    recovery_time: float | None


def simulate(readings, trace, policy, capacity, rate, end, reconnect_delay=5, log=False):
    """At equal times: connectivity, transmission, then acquisition. P1 can send
    newly acquired readings immediately if connected; buffered policies queue them.
    Service slots are spaced 1/rate seconds, with first slot at t=0.
    """
    queue, delivered, dropped, occupancy, events = [], [], set(), [], []
    slot_index = 0
    recovery_time = None
    last_outage_end = max((b + reconnect_delay for _, b in trace), default=0)
    def send(item, t):
        delivered.append((item, t))
        if log: events.append((t, 'delivered', item.id, len(queue)))
    def flush(until):
        nonlocal slot_index, recovery_time
        limit = int(round(until * rate))
        while queue and slot_index <= limit:
            t = slot_index / rate
            blocked = next(((a, b) for a, b in trace if a <= t < b + reconnect_delay), None)
            if blocked:
                slot_index = max(slot_index + 1, int(round((blocked[1] + reconnect_delay) * rate)))
                continue
            send(queue.pop(0), t)
            slot_index += 1
            if t >= last_outage_end and not queue and recovery_time is None:
                recovery_time = t - last_outage_end
        if not queue:
            slot_index = max(slot_index, limit + 1)
    for item in readings:
        flush(item.time)
        if policy == 'P1':
            if available(item.time, trace, reconnect_delay): send(item, item.time)
            else:
                dropped.add(item.id)
                if log: events.append((item.time, 'dropped', item.id, 0))
        else:
            admitted, evicted = admit(queue, item, capacity, policy)
            if evicted is not None:
                dropped.add(evicted.id)
                if log: events.append((item.time, 'evicted', evicted.id, len(queue)))
            if not admitted:
                dropped.add(item.id)
                if log: events.append((item.time, 'dropped', item.id, len(queue)))
        if log: occupancy.append((item.time, len(queue)))
    flush(end)
    if recovery_time is None and not queue:
        recovery_time = 0.0
    assert len(readings) == len(delivered) + len(dropped) + len(queue)
    assert len({r.id for r, _ in delivered}) == len(delivered)
    return Result(readings, delivered, dropped, list(queue), occupancy, events, end, recovery_time)
