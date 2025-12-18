def reverse_map(source):
    r_map = {}
    for key, values in source.items():
        for v in values:
            r_map[v] = key
    return r_map
