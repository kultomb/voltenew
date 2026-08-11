from dataclasses import dataclass
from typing import AbstractSet, Optional

from core.policy.signatures import (
    BEHAVIOR_KEYWORDS_BROAD,
    JUNK_KEYWORDS_STRONG,
    JUNK_KEYWORDS_WEAK,
)


@dataclass
class AnalysisResult:
    score: int
    level: str
    tags: list
    reasons: list
    matched_rules: list


class AppAnalyzer:
    """Rule-based analyzer for junk/ad/tracker Android apps."""

    def __init__(
        self,
        blacklist,
        ad_networks,
        ad_domains,
        behavior_keywords,
        junk_keywords,
        *,
        trusted_packages: Optional[AbstractSet[str]] = None,
    ):
        self.blacklist = {x.lower() for x in blacklist}
        self.trusted_packages = {x.lower() for x in (trusted_packages or ())}
        self.ad_networks = [x.lower() for x in ad_networks]
        self.ad_domains = [x.lower() for x in ad_domains]
        self.behavior_keywords = [x.lower() for x in behavior_keywords]
        self.junk_keywords = [k.lower() for k in junk_keywords]
        self.junk_keywords_strong = list(JUNK_KEYWORDS_STRONG)
        self.permission_risk = {
            "SYSTEM_ALERT_WINDOW": 6,
            "QUERY_ALL_PACKAGES": 6,
            "PACKAGE_USAGE_STATS": 5,
            "REQUEST_INSTALL_PACKAGES": 6,
            "RECEIVE_BOOT_COMPLETED": 5,
        }
        self._perm_cap_no_identity = 15
        self._sideload_score_cap = 55

    def _level_from_score(self, score):
        if score <= 19:
            return "safe"
        if score <= 39:
            return "low_risk"
        if score <= 59:
            return "warning"
        if score <= 79:
            return "high_risk"
        return "dangerous"

    def _trusted_result(self, package: str, note: str = "") -> dict:
        return {
            "score": 8,
            "level": "safe",
            "tags": ["trusted"],
            "reasons": [
                note
                or "Ứng dụng phổ biến / chính thống — không phải app rác hay quảng cáo giả mạo.",
            ],
            "matched_rules": ["TRUSTED_APP"],
        }

    @staticmethod
    def _junk_hits(pkg: str, name: str, keywords: list[str]) -> list[str]:
        return [k for k in keywords if k and (k in pkg or k in name)]

    def _behavior_hits(self, text: str, *, inspect: bool) -> list[str]:
        keys = [
            k for k in self.behavior_keywords
            if k and k not in BEHAVIOR_KEYWORDS_BROAD
        ]
        if inspect:
            keys = [k for k in keys if len(k) >= 6 or "ad" in k or "qc" in k or "quảng" in k]
        return [k for k in keys if k in text]

    def _has_strong_junk_identity(self, pkg: str, name: str, junk_hits: list[str]) -> bool:
        if pkg in self.blacklist:
            return True
        if self._junk_hits(pkg, name, self.junk_keywords_strong):
            return True
        return bool(self._junk_hits(pkg, name, list(JUNK_KEYWORDS_WEAK))) and bool(junk_hits)

    def analyze(self, package, app_name="", permissions=None, services=None, receivers=None, apk_strings=None):
        permissions = permissions or []
        services = services or []
        receivers = receivers or []
        apk_strings = apk_strings or []

        pkg = (package or "").lower()
        name = (app_name or "").lower()
        identity_text = f"{pkg} {name}"
        inspect_text = " ".join(apk_strings).lower()

        if pkg in self.trusted_packages:
            return self._trusted_result(
                package,
                f"{app_name or package}: app uy tín — bỏ qua chấm điểm app rác/blacklist.",
            )

        score = 0
        tags = []
        reasons = []
        matched = []

        if pkg in self.blacklist:
            score += 90
            tags.extend(["blacklist", "remove_recommended"])
            reasons.append("Package nằm trong BLACKLIST (app rác đã biết).")
            matched.append("BLACKLIST")

        junk_hits = self._junk_hits(pkg, name, self.junk_keywords_strong)
        weak_junk = self._junk_hits(pkg, name, list(JUNK_KEYWORDS_WEAK))
        if junk_hits:
            add = min(40, 20 + len(set(junk_hits)) * 4)
            score += add
            tags.append("cleaner")
            reasons.append(f"Tên/gói chứa từ khóa app rác: {', '.join(sorted(set(junk_hits))[:6])}")
            matched.append("JUNK_KEYWORDS")
        elif weak_junk:
            score += 8
            tags.append("suspicious_name")
            reasons.append(f"Tên/gói có từ gợi ý rác (yếu): {', '.join(sorted(set(weak_junk))[:4])}")
            matched.append("JUNK_KEYWORDS_WEAK")

        ad_identity = [a for a in self.ad_networks if a in identity_text]
        ad_inspect = [a for a in self.ad_networks if a in inspect_text and a not in ad_identity]
        ad_hits = sorted(set(ad_identity + ad_inspect))
        if ad_identity:
            add = min(35, 15 + len(ad_identity) * 5)
            score += add
            tags.append("ads")
            reasons.append(f"Ad SDK (tên/gói): {', '.join(ad_identity[:4])}")
            matched.append("AD_NETWORKS_IDENTITY")
        elif ad_inspect:
            add = min(20, 10 + len(ad_inspect) * 3)
            score += add
            tags.append("ads")
            reasons.append(f"Ad SDK (metadata): {', '.join(ad_inspect[:4])}")
            matched.append("AD_NETWORKS_INSPECT")

        domain_hits = [d for d in self.ad_domains if d in inspect_text]
        if domain_hits:
            score += min(15, 8 + len(set(domain_hits)) * 2)
            tags.append("tracker")
            reasons.append(f"Domain QC/tracker: {', '.join(sorted(set(domain_hits))[:4])}")
            matched.append("AD_DOMAINS")

        perm_set = {p.upper() for p in permissions}
        risky_perm_hits = [p for p in self.permission_risk if p in perm_set]
        if risky_perm_hits:
            perm_score = sum(self.permission_risk[p] for p in risky_perm_hits)
            strong_identity = self._has_strong_junk_identity(pkg, name, junk_hits)
            if not strong_identity and pkg not in self.blacklist:
                perm_score = min(perm_score, self._perm_cap_no_identity)
            score += perm_score
            tags.append("permissions")
            reasons.append(f"Quyền nhạy cảm: {', '.join(risky_perm_hits)}")
            matched.append("PERMISSION_RISK")

        has_overlay = "SYSTEM_ALERT_WINDOW" in perm_set
        has_boot = "RECEIVE_BOOT_COMPLETED" in perm_set or any(
            "BOOT_COMPLETED" in (x or "") for x in receivers
        )
        has_ads = bool(ad_identity or (ad_inspect and domain_hits))
        if has_overlay and has_boot and has_ads and (junk_hits or ad_identity):
            score += 35
            tags.extend(["popup", "boot"])
            reasons.append("Overlay + khởi động cùng lúc + QC — nguy cơ popup.")
            matched.append("OVERLAY_BOOT_ADS")

        behavior_identity = self._behavior_hits(identity_text, inspect=False)
        if behavior_identity:
            score += min(12, len(set(behavior_identity)) * 3)
            tags.append("behavior")
            reasons.append("Tên/gói gợi ý hành vi QC/rác.")
            matched.append("BEHAVIOR_IDENTITY")

        behavior_inspect = self._behavior_hits(inspect_text, inspect=True)
        if behavior_inspect and (junk_hits or ad_identity or domain_hits):
            score += min(8, len(set(behavior_inspect)) * 2)
            if "behavior" not in tags:
                tags.append("behavior")
            reasons.append("Metadata có dấu hiệu QC (kèm tín hiệu khác).")
            matched.append("BEHAVIOR_INSPECT")

        strong_signal = self._has_strong_junk_identity(pkg, name, junk_hits) or bool(ad_identity)
        if not strong_signal and pkg not in self.blacklist:
            score = min(score, self._sideload_score_cap)

        score = max(0, min(100, score))
        level = self._level_from_score(score)
        tags = sorted(set(tags))

        return {
            "score": score,
            "level": level,
            "tags": tags,
            "reasons": reasons,
            "matched_rules": matched,
        }
