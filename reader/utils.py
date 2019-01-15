def shrink_str(text: str, max_length=100) -> str:
    if len(text) < max_length:
        return text

    return '{}…'.format(text[:max_length - 1])
