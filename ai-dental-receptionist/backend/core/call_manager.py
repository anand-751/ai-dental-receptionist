from collections import deque

MAX_CONCURRENT_CALLS = 2   # Basic tier limit

active_calls = set()
waiting_queue = deque()


def can_accept_call():
    return len(active_calls) < MAX_CONCURRENT_CALLS


def add_active_call(client_id):
    active_calls.add(client_id)


def remove_active_call(client_id):
    active_calls.discard(client_id)


def add_to_queue(client_id):
    waiting_queue.append(client_id)


def pop_next_from_queue():
    if waiting_queue:
        return waiting_queue.popleft()
    return None
