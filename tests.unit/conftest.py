"""
Don't accidentally consider anything below feditest to be a pyunit test.
"""

import inspect

import pytest

@pytest.hookimpl(wrapper=True)
def pytest_pycollect_makeitem(
    collector: pytest.Module | pytest.Class,
    name: str,
    obj: object,
) -> pytest.Item | pytest.Collector | list[pytest.Item | pytest.Collector] | None:
    # Ignore all feditest classes and function using
    # pytest naming conventions.
    if isinstance(obj, type) or inspect.isfunction(obj) or inspect.ismethod(obj):
        m = obj.__module__.split(".")
        if len(m) > 0 and m[0] == "feditest":
            yield
            return None
    result = yield
    return result
