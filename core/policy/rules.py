"""Package classification: junk/ad detection and protection whitelists."""

from .signatures import (
    AD_DOMAINS,
    AD_NETWORKS,
    BEHAVIOR_KEYWORDS,
    JUNK_KEYWORDS,
    JUNK_KEYWORDS_STRONG,
)
from .store import BLACKLIST
from .whitelists import (
    BANK_APPS_WHITELIST,
    CHAT_WHITELIST,
    POPULAR_APP_PREFIXES,
    POPULAR_APPS_WHITELIST,
    SYSTEM_PACKAGES,
)


def is_bank_app(package: str) -> bool:
    return package in BANK_APPS_WHITELIST


def is_popular_app(package: str) -> bool:
    if package in POPULAR_APPS_WHITELIST:
        return True
    return any(package.startswith(p) for p in POPULAR_APP_PREFIXES)


def is_protected_package(package: str) -> bool:
    return (
        any(package.startswith(p) for p in SYSTEM_PACKAGES)
        or package in CHAT_WHITELIST
        or package in POPULAR_APPS_WHITELIST
        or is_popular_app(package)
        or is_bank_app(package)
    )


def is_ad_related_package(package: str) -> bool:
    """Junk if in blacklist or matches ad SDK / junk keywords."""
    if package in BLACKLIST:
        return True
    if any(ad in package.lower() for ad in AD_NETWORKS):
        return True
    pkg_lower = package.lower()
    return any(kw in pkg_lower for kw in JUNK_KEYWORDS_STRONG)


def check_ad_network_activity(line: str) -> bool:
    lower = line.lower()
    if any(domain.lower() in lower for domain in AD_DOMAINS):
        return True
    return any(keyword in lower for keyword in BEHAVIOR_KEYWORDS)
