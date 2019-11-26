def create_chat_name(*args) -> str:
    first, second = sorted(args, key=lambda x: int(x, 16))
    if first == second:
        return first
    else:
        return f'{first}_{second}'
