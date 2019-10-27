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
    if int(first_user, 16) == int(second_user, 16):
        return first_user
    else:
        return f'{min(first_user, second_user)}_{max(first_user, second_user)}'
