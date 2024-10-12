def group_by(collection: List | Set | Generator, key: callable) -> Dict[str, List]:
    """
    group elements from collection
    :param collection:
    :param key: key generator
    :return: group
    """
    groups = {}
    for item in collection:
        item_key = key(item)
        if item_key not in groups:
            groups[item_key] = []
        groups[item_key].append(item)
    return groups
