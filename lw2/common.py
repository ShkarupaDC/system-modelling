from typing import Union, TypeVar, Type, Any

INF_TIME = float('inf')
TIME_EPS = 1e-6

TIME_PR = 5
TIME_FORMATTER = f'{{value:.{TIME_PR}f}}'

T = TypeVar('T')
PathFormat = Union[str, tuple[str, str]]


def _get_param_by_path(parent: Any, path: str) -> tuple[str, Any]:
    name, value = None, parent
    for name in path.split('.'):
        value = getattr(value, name)
    return name, value


def _format_param(parent: Any, path: str, formatter: str = '{name}={value}') -> str:
    name, value = _get_param_by_path(parent, path)
    return formatter.format(name=name, value=value)


def format_params(parent: Any, param_args: list[PathFormat]) -> str:
    params_reprs: list[str] = []
    for args in param_args:
        if isinstance(args, tuple):
            path, formatter = args
            param_repr = _format_param(parent, path, f'{{name}}={formatter}')
        else:
            param_repr = _format_param(parent, args)
        params_reprs.append(param_repr)
    return ', '.join(params_reprs)


def instance_counter(target: Type[T]) -> Type[T]:
    target.count = 0

    def next_id(cls: Type[T]) -> int:
        cls.count += 1
        return cls.count

    target._next_id = classmethod(next_id)
    return target
