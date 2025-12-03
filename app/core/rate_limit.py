# app/core/rate_limit.py

"""
Rate limiting configuration for the FastAPI application.

This module initializes and exports a SlowAPI `Limiter` instance,
which is responsible for enforcing request rate limits across the API.
The limiter uses the client's IP address as the unique identifier
for counting requests.
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address


# ----------------------------------------------------------------------
# Limiter Instance
# ----------------------------------------------------------------------
# `key_func=get_remote_address` ensures that rate limits are applied
# per client IP address. This function extracts the IP from the request,
# automatically working behind proxies if configured properly
limiter = Limiter(key_func=get_remote_address)
if os.getenv("TESTING") == "1":
    limiter.enabled = False
