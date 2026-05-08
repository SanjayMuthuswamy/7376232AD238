from contextlib import contextmanager


@contextmanager
def get_connection():
    # Not using a real DB yet, but routes can be moved here later.
    yield None
