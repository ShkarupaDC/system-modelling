from typing import Any

INF_TIME = float('inf')


def get_param_by_path(parent: Any, path: str) -> tuple[str, Any]:
    name, value = None, parent
    for name in path.split('.'):
        value = getattr(value, name)
    return name, value


def format_param(parent: Any, path: str, formatter: str = '{name}={value}') -> str:
    name, value = get_param_by_path(parent, path)
    return formatter.format(name=name, value=value)
