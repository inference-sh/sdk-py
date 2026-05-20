import asyncio
import inspect

try:
    import pytest_asyncio  # noqa: F401
    # pytest-asyncio is installed; it handles async tests natively
except ImportError:
    def pytest_pyfunc_call(pyfuncitem):
        """Fallback async test runner when pytest-asyncio is not installed."""
        if inspect.iscoroutinefunction(pyfuncitem.function):
            funcargs = pyfuncitem.funcargs
            testargs = {arg: funcargs[arg] for arg in pyfuncitem._fixtureinfo.argnames}
            asyncio.run(pyfuncitem.obj(**testargs))
            return True
