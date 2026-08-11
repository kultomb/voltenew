# Ad SDK prefixes, domains, and logcat / package keyword signatures.

AD_NETWORKS = [
    "com.google.ads", "com.facebook.ads", "com.unity3d.ads",
    "com.applovin", "com.ironsource", "com.mopub",
    "com.adcolony", "com.vungle", "com.tapjoy",
    "com.inmobi", "com.startapp", "com.chartboost",
    "com.flurry", "com.admob", "com.heyzap",
    "com.bytedance", "com.pangle", "com.mintegral",
    "com.fyber", "com.ogury", "com.adjust",
    "com.tnkad", "com.adxcorp", "com.iion",
    "com.verve", "com.amazon.device.ads", "com.chartboost.mediation",
    "com.yandex.mobile.ads", "com.pubmatic", "com.smaato",
]

AD_DOMAINS = [
    "ads.google.com", "doubleclick.net", "api.applovin.com", "ads.facebook.com",
    "ads.twitter.com", "ads.yahoo.com", "adserver.unityads.unity3d.com",
    "ads.mopub.com", "adcolony.com", "vungle.com", "tapjoy.com", "inmobi.com",
    "startapp.com", "chartboost.com", "flurry.com", "pangle.io", "mintegral.com",
]

_BEHAVIOR_KEYWORDS_RAW = [
    "admob", "ads", "advert", "popup", "banner", "virus", "infected", "warning", "alert", "scan",
    "clean", "optimize", "cleaner", "dọn rác", "quảng cáo", "hiển thị quảng cáo", "cảnh báo",
    "nguy hiểm", "nhiễm độc", "mã độc", "quét", "dọn dẹp", "tối ưu hóa", "xóa rác", "làm sạch",
    "thông báo", "cảnh báo giả mạo", "tăng tốc", "tăng tốc điện thoại", "adware",
    "install", "download", "tải ngay", "cài đặt", "CH Play", "Google Play", "ứng dụng", "app",
    "market://", "play.google.com", "affiliate", "adclick", "adimpression", "interstitial",
    "bannerad", "nativead", "redirect", "promotion", "offer", "khuyến mãi", "discount",
    "sponsored", "adview", "rewarded", "adload", "adshow", "instream", "outstream",
    "skip", "close ad", "ad closed", "free", "miễn phí", "try now", "thử ngay", "reward", "thưởng",
]

_JUNK_KEYWORDS_RAW = [
    "clean", "boost", "optimizer", "filemanager", "fileexplorer", "keeper", "master", "antivirus",
    "dọn dẹp", "tăng tốc độ", "tối ưu", "quản lý tệp", "diệt virus", "bảo vệ điện thoại",
    "giải phóng bộ nhớ", "tiết kiệm pin", "làm mát máy", "admob", "applovin", "unityads",
    "inmobi", "facebookads", "affiliate", "promotion", "offer",
    "super cleaner", "power clean", "security", "phone booster", "cache cleaner",
]

BEHAVIOR_KEYWORDS = [k.lower() for k in _BEHAVIOR_KEYWORDS_RAW]
JUNK_KEYWORDS = [k.lower() for k in _JUNK_KEYWORDS_RAW]

# Từ khóa rác quá rộng — chỉ dùng kèm tín hiệu mạnh khác, không gợi ý gỡ một mình
JUNK_KEYWORDS_WEAK = frozenset({
    "security", "master", "keeper", "offer", "promotion", "affiliate",
})
JUNK_KEYWORDS_STRONG = [k for k in JUNK_KEYWORDS if k not in JUNK_KEYWORDS_WEAK]

# Không quét trên dumpsys (dễ trúng android.app, install, free…)
BEHAVIOR_KEYWORDS_BROAD = frozenset({
    "app", "install", "download", "free", "miễn phí", "ứng dụng", "quét", "scan",
    "alert", "warning", "clean", "optimize", "thông báo", "cài đặt", "tải ngay",
    "CH Play", "Google Play", "market://", "play.google.com",
})
