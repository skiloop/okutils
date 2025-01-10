import random

from okutils.sdm import Writer


def random_string(size: int = 10):
    chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ;:."
    return "".join(random.choices(chars, k=size))


def write_items(filename: str, encoder, items):
    writer = Writer(filename, encoder=encoder)
    pos = []
    for key, value in items:
        pos.append(writer.append(key, value))
    return pos
