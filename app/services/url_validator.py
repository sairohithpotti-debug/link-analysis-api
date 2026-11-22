import ipaddress
import socket
from urllib.parse import urlparse

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "169.254.169.254",
}

class SSRFValidationError(ValueError):
    """Raised when a URL targets a disallowed scheme, host, or private IP."""

def _is_forbidden_ip(ip_str: str) -> bool:
    addr = ipaddress.ip_address(ip_str)
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
        or getattr(addr, "is_site_local", False)
    )

def validate_public_url(raw_url: str) -> str:
    parsed = urlparse(raw_url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise SSRFValidationError("Only http and https URLs are allowed.")
    hostname = (parsed.hostname or "").strip().lower().rstrip(".")
    if not hostname:
        raise SSRFValidationError("URL must contain a valid hostname.")
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".local") or hostname.endswith(".internal"):
        raise SSRFValidationError(f"Access to internal or local host '{hostname}' is blocked.")
    try:
        if _is_forbidden_ip(hostname):
            raise SSRFValidationError("Access to private, loopback, or reserved IP addresses is blocked.")
        return parsed.geturl()
    except ValueError:
        pass
    try:
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise SSRFValidationError(f"Unable to resolve hostname '{hostname}'.") from exc
    if not addr_info:
        raise SSRFValidationError(f"No IP addresses resolved for '{hostname}'.")
    for entry in addr_info:
        ip_str = entry[4][0]
        if _is_forbidden_ip(ip_str):
            raise SSRFValidationError(
                f"Hostname '{hostname}' resolved to a restricted IP address ({ip_str})."
            )
    return parsed.geturl()
