from typing import List


def check_chat(ids: List[str]) -> bool:
    for i in ids:
        try:
            int(i, 16)
        except ValueError as e:
            return False
        else:
            return True

def create_chat_name(first_user: str, second_user: str) -> str:
    if int(first_user, 16) < int(second_user, 16):
        return f'{first_user}_{second_user}'
    elif int(first_user, 16) > int(second_user, 16):
        return f'{second_user}_{first_user}'
    else:
        return first_user