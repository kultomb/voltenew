"""App blocking policy: blacklists, ad signatures, whitelists, runtime store."""

from .blacklist_defaults import DEFAULT_BLACKLIST
from .rules import (
    check_ad_network_activity,
    is_ad_related_package,
    is_bank_app,
    is_popular_app,
    is_protected_package,
)
from .signatures import AD_DOMAINS, AD_NETWORKS, BEHAVIOR_KEYWORDS, JUNK_KEYWORDS
from .store import (
    BLACKLIST,
    add_to_blacklist,
    init_policy,
    is_valid_package,
    load_blacklist_file,
    load_config,
    persist_blacklist,
    replace_blacklist,
    save_blacklist,
    save_config,
)
from .whitelists import (
    BANK_APPS_WHITELIST,
    CHAT_WHITELIST,
    POPULAR_APPS_WHITELIST,
    SYSTEM_PACKAGES,
    TRUSTED_ANALYSIS_PACKAGES,
)

__all__ = [
    "DEFAULT_BLACKLIST",
    "BLACKLIST",
    "replace_blacklist",
    "init_policy",
    "load_config",
    "load_blacklist_file",
    "save_blacklist",
    "save_config",
    "persist_blacklist",
    "add_to_blacklist",
    "is_valid_package",
    "AD_NETWORKS",
    "AD_DOMAINS",
    "BEHAVIOR_KEYWORDS",
    "JUNK_KEYWORDS",
    "SYSTEM_PACKAGES",
    "CHAT_WHITELIST",
    "POPULAR_APPS_WHITELIST",
    "BANK_APPS_WHITELIST",
    "TRUSTED_ANALYSIS_PACKAGES",
    "is_ad_related_package",
    "is_protected_package",
    "is_bank_app",
    "is_popular_app",
    "check_ad_network_activity",
]
