from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter compartido por IP. Default global aplicado en main.py;
# los endpoints sensibles/costosos sobreescriben con @limiter.limit(...).
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
