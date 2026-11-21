from dataclasses import dataclass, field
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
    network_losses: set = field(default_factory=set)
    overflow_losses: set = field(default_factory=set)
    no_buffer_losses: set = field(default_factory=set)


def simulate(readings, trace, policy, capacity, rate, end, reconnect_delay=5, log=False):
    """At equal times: transmission precedes acquisition for every policy.
    P1 holds at most one connected reading until the next common service slot;
    it cannot retain a reading through a disconnection. Slots are 1/rate apart.
    """
    queue, delivered, dropped, occupancy, events = [], [], set(), [], []
    network_losses, overflow_losses, no_buffer_losses = set(), set(), set()
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
                if policy == 'P1':
                    lost=queue.pop(0)
                    dropped.add(lost.id); network_losses.add(lost.id)
                    if log: events.append((t, 'network_drop', lost.id, 0))
                slot_index = max(slot_index + 1, int(round((blocked[1] + reconnect_delay) * rate)))
                continue
            send(queue.pop(0), t)
            slot_index += 1
            if t >= last_outage_end and not queue and recovery_time is None:
                recovery_time = t - last_outage_end
        if not queue:
            slot_index = max(slot_index, limit + 1)
            if until >= last_outage_end and recovery_time is None:
                recovery_time = 0.0
    for item in readings:
        flush(item.time)
        if policy == 'P1':
            if not available(item.time, trace, reconnect_delay):
                dropped.add(item.id)
                network_losses.add(item.id)
                if log: events.append((item.time, 'network_drop', item.id, len(queue)))
            elif queue:
                dropped.add(item.id); no_buffer_losses.add(item.id)
                if log: events.append((item.time, 'no_buffer_drop', item.id, len(queue)))
            else:
                queue.append(item)
        else:
            admitted, evicted = admit(queue, item, capacity, policy)
            if evicted is not None:
                dropped.add(evicted.id)
                overflow_losses.add(evicted.id)
                if log: events.append((item.time, 'overflow_evicted', evicted.id, len(queue)))
            if not admitted:
                dropped.add(item.id)
                overflow_losses.add(item.id)
                if log: events.append((item.time, 'overflow_drop', item.id, len(queue)))
        occupancy.append((item.time, len(queue)))
    flush(end)
    if not trace:
        recovery_time = 0.0
    assert len(readings) == len(delivered) + len(dropped) + len(queue)
    assert dropped == network_losses | overflow_losses | no_buffer_losses
    assert len({r.id for r, _ in delivered}) == len(delivered)
    return Result(readings, delivered, dropped, list(queue), occupancy, events, end, recovery_time,
                  network_losses, overflow_losses, no_buffer_losses)
