POLICIES = ('P1', 'P2', 'P3', 'P4')


def admit(queue, item, capacity, policy):
    """Return (admitted, evicted). Queue is chronological; P4 evicts oldest routine,
    and rejects routine if all stored readings are abnormal. Abnormal then evicts oldest abnormal.
    """
    if policy == 'P1':
        return False, None
    if len(queue) < capacity:
        queue.append(item)
        return True, None
    if policy == 'P2':
        return False, None
    if policy == 'P3':
        old = queue.pop(0)
    elif policy == 'P4':
        idx = next((i for i, r in enumerate(queue) if not r.abnormal), None)
        if idx is None:
            if not item.abnormal:
                return False, None
            idx = 0
        old = queue.pop(idx)
    else:
        raise ValueError(policy)
    queue.append(item)
    return True, old
