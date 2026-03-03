# Import submodules to register commands
from . import (
    auth as auth,
)
from . import (
    dashboard as dashboard,
)
from . import (
    sync as sync,
)
from . import (
    transfer as transfer,
)
from .common import app

__all__ = ["app"]
