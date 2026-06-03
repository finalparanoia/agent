from uuid import uuid4


def generate_id() -> str:
    """生成唯一的UUID标识符"""
    return str(uuid4())
