import os

_env = os.environ.get("DJANGO_ENV", "").lower()
_debug_env = os.environ.get("DEBUG", "True").lower()

if _env == "production" or _debug_env in ("false", "0", "no"):
    from .prod import *
else:
    from .dev import *
