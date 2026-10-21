from __future__ import annotations

from dataclasses import dataclass, field

def pd_isna(v) -> bool:
    try:
        return v != v  # NaN
    except Exception:
        return False


@dataclass(frozen=True)
class Country:
    iso2: str
    iso3: str
    m49: int
    name: str
    aliases: tuple[str, ...] = ()
    region: str = ""


@dataclass(frozen=True)
class Product:
    code: str
    name: str
    family: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Port:
    portid: str
    name: str
    country: str
    kind: str  # origin | dest | alt
    lon: float
    lat: float


@dataclass(frozen=True)
class Chokepoint:
    portid: str
    name: str
    aliases: tuple[str, ...]
    lon: float
    lat: float


COUNTRIES: dict[str, Country] = {}


def _c(
    iso2: str,
    iso3: str,
    m49: int,
    name: str,
    aliases: tuple[str, ...] = (),
    region: str = "",
) -> Country:
    rec = Country(iso2, iso3, m49, name, aliases, region)
    COUNTRIES[iso2] = rec
    COUNTRIES[iso3] = rec
    COUNTRIES[str(m49)] = rec
    return rec


_c("IT", "ITA", 380, "Italy", ("italian", "italia", "italian pasta"), "EU")
_c("TR", "TUR", 792, "Türkiye", ("turkey", "turkish", "turkiye"), "ANATOLIA")
_c("EG", "EGY", 818, "Egypt", ("egyptian", "egypt"), "MENA")
_c("IR", "IRN", 364, "Iran", ("iranian", "persia"), "MENA")
_c("SA", "SAU", 682, "Saudi Arabia", ("saudi", "ksa", "kingdom of saudi arabia"), "GCC")
_c("AE", "ARE", 784, "United Arab Emirates", ("uae", "emirates", "dubai", "abu dhabi"), "GCC")
_c("LB", "LBN", 422, "Lebanon", ("lebanese", "beirut"), "LEVANT")
_c("KE", "KEN", 404, "Kenya", ("kenyan", "nairobi", "mombasa"), "EA")
_c("TZ", "TZA", 834, "Tanzania", ("tanzanian", "dar es salaam"), "EA")
_c("UG", "UGA", 800, "Uganda", ("ugandan", "kampala"), "EA")
_c("RW", "RWA", 646, "Rwanda", ("rwandan", "kigali"), "EA")
_c("ET", "ETH", 231, "Ethiopia", ("ethiopian", "addis"), "EA")
_c("SO", "SOM", 706, "Somalia", ("somali", "mogadishu"), "EA")
_c("DJ", "DJI", 262, "Djibouti", ("djiboutian",), "EA")
_c("KW", "KWT", 414, "Kuwait", ("kuwaiti",), "GCC")
_c("QA", "QAT", 634, "Qatar", ("qatari", "doha"), "GCC")
_c("OM", "OMN", 512, "Oman", ("omani", "muscat", "sohar", "salalah"), "GCC")
_c("BH", "BHR", 48, "Bahrain", ("bahraini",), "GCC")
_c("SY", "SYR", 760, "Syria", ("syrian", "damascus"), "LEVANT")
_c("IQ", "IRQ", 368, "Iraq", ("iraqi", "baghdad"), "LEVANT")
_c("JO", "JOR", 400, "Jordan", ("jordanian", "amman", "aqaba"), "LEVANT")
_c("YE", "YEM", 887, "Yemen", ("yemeni",), "MENA")
_c("CN", "CHN", 156, "China", ("chinese",), "ASIA")
_c("IN", "IND", 699, "India", ("indian",), "ASIA")
_c("PK", "PAK", 586, "Pakistan", ("pakistani",), "ASIA")
_c("ES", "ESP", 724, "Spain", ("spanish",), "EU")
_c("FR", "FRA", 251, "France", ("french",), "EU")
_c("US", "USA", 842, "United States", ("usa", "america", "american"), "AMERICAS")
_c("CA", "CAN", 124, "Canada", ("canadian",), "AMERICAS")
_c("TN", "TUN", 788, "Tunisia", ("tunisian",), "MENA")
_c("MA", "MAR", 504, "Morocco", ("moroccan",), "MENA")
_c("GR", "GRC", 300, "Greece", ("greek",), "EU")
_c("DE", "DEU", 276, "Germany", ("german",), "EU")
_c("GB", "GBR", 826, "United Kingdom", ("uk", "britain", "british"), "EU")
_c("JP", "JPN", 392, "Japan", ("japanese",), "ASIA")
_c("KR", "KOR", 410, "South Korea", ("korea", "korean"), "ASIA")
_c("ID", "IDN", 360, "Indonesia", ("indonesian",), "ASIA")
_c("PH", "PHL", 608, "Philippines", ("filipino",), "ASIA")
_c("TH", "THA", 764, "Thailand", ("thai",), "ASIA")
_c("NG", "NGA", 566, "Nigeria", ("nigerian",), "AFRICA")
_c("GH", "GHA", 288, "Ghana", ("ghanaian",), "AFRICA")
_c("ZA", "ZAF", 710, "South Africa", ("south african",), "AFRICA")
_c("SD", "SDN", 729, "Sudan", ("sudanese",), "AFRICA")
_c("LY", "LBY", 434, "Libya", ("libyan",), "MENA")
_c("PS", "PSE", 275, "Palestine", ("palestinian",), "LEVANT")
_c("SS", "SSD", 728, "South Sudan", ("south sudanese",), "EA")
_c("ER", "ERI", 232, "Eritrea", ("eritrean",), "EA")
_c("NE", "NER", 562, "Niger", ("nigerien",), "AFRICA")
_c("TG", "TGO", 768, "Togo", ("togolese",), "AFRICA")
_c("BF", "BFA", 854, "Burkina Faso", (), "AFRICA")
_c("CI", "CIV", 384, "Côte d'Ivoire", ("ivory coast",), "AFRICA")
_c("VE", "VEN", 862, "Venezuela", ("venezuelan",), "AMERICAS")
_c("BR", "BRA", 76, "Brazil", ("brazilian",), "AMERICAS")
_c("MX", "MEX", 484, "Mexico", ("mexican",), "AMERICAS")
_c("RU", "RUS", 643, "Russia", ("russian",), "EURASIA")
_c("UA", "UKR", 804, "Ukraine", ("ukrainian",), "EURASIA")
_c("AU", "AUS", 36, "Australia", ("australian",), "OCEANIA")
_c("NL", "NLD", 528, "Netherlands", ("dutch",), "EU")
_c("BE", "BEL", 56, "Belgium", ("belgian",), "EU")
_c("PT", "PRT", 620, "Portugal", ("portuguese",), "EU")
_c("PL", "POL", 616, "Poland", ("polish",), "EU")
_c("RO", "ROU", 642, "Romania", ("romanian",), "EU")
_c("BG", "BGR", 100, "Bulgaria", ("bulgarian",), "EU")
_c("HR", "HRV", 191, "Croatia", ("croatian",), "EU")
_c("RS", "SRB", 688, "Serbia", ("serbian",), "EU")
_c("AL", "ALB", 8, "Albania", ("albanian",), "EU")
_c("BA", "BIH", 70, "Bosnia and Herzegovina", ("bosnian",), "EU")
_c("XK", "XKX", 0, "Kosovo", ("kosovar",), "EU")
_c("AF", "AFG", 4, "Afghanistan", ("afghan",), "ASIA")
_c("BD", "BGD", 50, "Bangladesh", ("bangladeshi",), "ASIA")
_c("MY", "MYS", 458, "Malaysia", ("malaysian",), "ASIA")
_c("VN", "VNM", 704, "Vietnam", ("vietnamese",), "ASIA")
_c("TW", "TWN", 158, "Taiwan", ("taiwanese",), "ASIA")
_c("HK", "HKG", 344, "Hong Kong", (), "ASIA")
_c("SG", "SGP", 702, "Singapore", (), "ASIA")
_c("NZ", "NZL", 554, "New Zealand", (), "OCEANIA")
_c("AR", "ARG", 32, "Argentina", ("argentine",), "AMERICAS")
_c("CL", "CHL", 152, "Chile", ("chilean",), "AMERICAS")
_c("CO", "COL", 170, "Colombia", ("colombian",), "AMERICAS")
_c("PE", "PER", 604, "Peru", ("peruvian",), "AMERICAS")
_c("EC", "ECU", 218, "Ecuador", (), "AMERICAS")
_c("UY", "URY", 858, "Uruguay", (), "AMERICAS")
_c("MZ", "MOZ", 508, "Mozambique", (), "AFRICA")
_c("AO", "AGO", 24, "Angola", (), "AFRICA")
_c("CM", "CMR", 120, "Cameroon", (), "AFRICA")
_c("SN", "SEN", 686, "Senegal", (), "AFRICA")
_c("ML", "MLI", 466, "Mali", (), "AFRICA")
_c("TD", "TCD", 148, "Chad", (), "AFRICA")
_c("MR", "MRT", 478, "Mauritania", (), "AFRICA")
_c("GM", "GMB", 270, "Gambia", (), "AFRICA")
_c("SL", "SLE", 694, "Sierra Leone", (), "AFRICA")
_c("LR", "LBR", 430, "Liberia", (), "AFRICA")
_c("CG", "COG", 178, "Congo", (), "AFRICA")
_c("CD", "COD", 180, "DR Congo", ("drc",), "AFRICA")
_c("GA", "GAB", 266, "Gabon", (), "AFRICA")
_c("GQ", "GNQ", 226, "Equatorial Guinea", (), "AFRICA")
_c("BI", "BDI", 108, "Burundi", (), "EA")
_c("MW", "MWI", 454, "Malawi", (), "AFRICA")
_c("ZM", "ZMB", 894, "Zambia", (), "AFRICA")
_c("ZW", "ZWE", 716, "Zimbabwe", (), "AFRICA")
_c("BW", "BWA", 72, "Botswana", (), "AFRICA")
_c("NA", "NAM", 516, "Namibia", (), "AFRICA")
_c("MG", "MDG", 450, "Madagascar", (), "AFRICA")
_c("MU", "MUS", 480, "Mauritius", (), "AFRICA")
_c("SC", "SYC", 690, "Seychelles", (), "AFRICA")
_c("KM", "COM", 174, "Comoros", (), "AFRICA")
_c("CV", "CPV", 132, "Cabo Verde", (), "AFRICA")
_c("ST", "STP", 678, "São Tomé and Príncipe", (), "AFRICA")
_c("GN", "GIN", 324, "Guinea", (), "AFRICA")
_c("GW", "GNB", 624, "Guinea-Bissau", (), "AFRICA")
_c("BJ", "BEN", 204, "Benin", (), "AFRICA")
_c("WORLD", "WLD", 0, "World", ("world", "global", "all"), "WORLD")


MARKETS = ("LB", "AE", "SA", "KW", "QA", "OM", "BH", "KE", "TZ", "UG", "RW", "ET", "SO", "DJ", "SY", "IQ", "JO")
GCC = ("AE", "SA", "KW", "QA", "OM", "BH")
EAST_AFRICA = ("KE", "TZ", "UG", "RW", "ET", "SO", "DJ")
LEVANT = ("LB", "SY", "IQ", "JO")
COMPETITOR_ORIGINS = ("IT", "TR", "EG", "IR", "SA", "AE", "CN", "IN", "ES", "FR", "TN")

REGIONS = {
    "gulf": GCC,
    "gcc": GCC,
    "east africa": EAST_AFRICA,
    "east-africa": EAST_AFRICA,
    "levant": LEVANT,
    "mena": GCC + LEVANT + ("EG", "IR", "YE", "LY"),
}

PRODUCTS: dict[str, Product] = {
    "1902": Product("1902", "Pasta (HS 1902)", "pasta", ("pasta", "macaroni", "spaghetti", "noodles")),
    "190219": Product("190219", "Uncooked pasta, not stuffed, without eggs", "pasta", ("dry pasta", "uncooked pasta")),
    "110311": Product("110311", "Durum wheat semolina", "semolina", ("semolina", "semola")),
    "200290": Product("200290", "Tomato paste / puree", "tomato", ("tomato paste", "tomato puree", "concentrate")),
    "210320": Product("210320", "Tomato sauce / ketchup", "tomato", ("tomato sauce", "ketchup")),
    "100119": Product("100119", "Durum wheat", "durum", ("durum", "grano duro", "durum wheat")),
}

PORTS = [
    Port("port795", "Napoli", "IT", "origin", 14.27, 40.84),
    Port("port1135", "Salerno", "IT", "origin", 14.77, 40.67),
    Port("port622", "La Spezia", "IT", "origin", 9.83, 44.11),
    Port("port744", "Jebel Ali", "AE", "dest", 55.03, 24.99),
    Port("port561", "Khor Fakkan", "AE", "alt", 56.36, 25.34),
    Port("port362", "Fujairah", "AE", "alt", 56.37, 25.12),
    Port("port988", "Sohar", "OM", "alt", 56.71, 24.50),
    Port("port746", "Salalah", "OM", "alt", 54.02, 16.94),
    Port("port518", "Jeddah", "SA", "dest", 39.17, 21.48),
    Port("port2031", "King Abdullah Port", "SA", "alt", 39.10, 22.52),
    Port("port275", "Dammam", "SA", "dest", 50.20, 26.50),
    Port("port132", "Beirut", "LB", "dest", 35.51, 33.90),
    Port("port757", "Mombasa", "KE", "dest", 39.67, -4.05),
    Port("port278", "Dar Es Salaam", "TZ", "dest", 39.29, -6.83),
    Port("port25", "Shuwaikh", "KW", "dest", 47.93, 29.35),
    Port("port735", "Mersin", "TR", "origin", 34.64, 36.80),
    Port("port2049", "Ambarli", "TR", "origin", 28.68, 40.97),
]

CHOKEPOINTS = [
    Chokepoint("chokepoint6", "Strait of Hormuz", ("hormuz", "strait of hormuz"), 56.25, 26.57),
    Chokepoint("chokepoint4", "Bab el-Mandeb Strait", ("bab el-mandeb", "bab al-mandab", "mandeb"), 43.33, 12.58),
    Chokepoint("chokepoint1", "Suez Canal", ("suez", "suez canal"), 32.35, 30.46),
    Chokepoint("chokepoint7", "Cape of Good Hope", ("cape", "cape of good hope"), 18.47, -34.35),
    Chokepoint("chokepoint8", "Gibraltar Strait", ("gibraltar",), -5.58, 35.97),
]

LANES = [
    {"id": "it-jebel", "origin": "Napoli", "dest": "Jebel Ali", "via": ["Suez Canal", "Bab el-Mandeb Strait", "Strait of Hormuz"], "market": "AE"},
    {"id": "it-khor", "origin": "Napoli", "dest": "Khor Fakkan", "via": ["Suez Canal", "Bab el-Mandeb Strait"], "market": "AE"},
    {"id": "it-dammam", "origin": "Napoli", "dest": "Dammam", "via": ["Suez Canal", "Bab el-Mandeb Strait", "Strait of Hormuz"], "market": "SA"},
    {"id": "it-jeddah", "origin": "Napoli", "dest": "Jeddah", "via": ["Suez Canal", "Bab el-Mandeb Strait"], "market": "SA"},
    {"id": "it-beirut", "origin": "Napoli", "dest": "Beirut", "via": ["Gibraltar Strait"], "market": "LB"},
    {"id": "it-mombasa", "origin": "Salerno", "dest": "Mombasa", "via": ["Suez Canal", "Bab el-Mandeb Strait"], "market": "KE"},
]

TIM_COUNTRY = {
    "LÜBNAN": "LB",
    "SUUDİ ARABİSTAN": "SA",
    "BAE": "AE",
    "BİRLEŞİK ARAP EMİRLİKLERİ": "AE",
    "KATAR": "QA",
    "KUVEYT": "KW",
    "UMMAN": "OM",
    "BAHREYN": "BH",
    "KENYA": "KE",
    "TANZANYA": "TZ",
    "UGANDA": "UG",
    "RUANDA": "RW",
    "ETİYOPYA": "ET",
    "SOMALİ": "SO",
    "CİBUTİ": "DJ",
    "SURİYE": "SY",
    "IRAK": "IQ",
    "ÜRDÜN": "JO",
    "MISIR": "EG",
    "YEMEN": "YE",
}

WFP_DATASETS = {
    "LB": "wfp-food-prices-for-lebanon",
    "SY": "wfp-food-prices-for-syrian-arab-republic",
    "SO": "wfp-food-prices-for-somalia",
    "KE": "wfp-food-prices-for-kenya",
    "YE": "wfp-food-prices-for-yemen",
}

WFP_COMMODITY_MAP = {
    "Pasta (spaghetti)": ("pasta", 0.5 if False else None),
    "Pasta": ("pasta", 1.0),
    "Tomatoes (paste)": ("tomato_paste", None),
    "Tomatoes": ("tomato", 1.0),
}


def country_by_any(token: str | int | float | None) -> Country | None:
    if token is None:
        return None
    try:
        if pd_isna(token):
            return None
    except Exception:
        pass
    t = str(token).strip()
    if t in {"", "nan", "None", "<NA>"}:
        return None
    if not t:
        return None
    if t in COUNTRIES:
        return COUNTRIES[t]
    low = t.lower()
    for rec in unique_countries():
        if rec.name.lower() == low or rec.iso2.lower() == low or rec.iso3.lower() == low:
            return rec
        if any(a == low for a in rec.aliases):
            return rec
    return None


def unique_countries() -> list[Country]:
    seen: set[str] = set()
    out: list[Country] = []
    for rec in COUNTRIES.values():
        if rec.iso2 in seen:
            continue
        seen.add(rec.iso2)
        out.append(rec)
    return out


def country_name(code: str) -> str:
    rec = country_by_any(code)
    return rec.name if rec else code


def iso2(code: str | int | None) -> str | None:
    if code is None:
        return None
    rec = country_by_any(str(code))
    return rec.iso2 if rec else None


def m49(code: str) -> int | None:
    rec = country_by_any(code)
    return rec.m49 if rec else None


def resolve_region(token: str) -> tuple[str, ...]:
    return REGIONS.get(token.lower().strip(), ())


def product_by_any(token: str) -> Product | None:
    t = (token or "").strip().lower()
    if not t:
        return None
    if t in PRODUCTS:
        return PRODUCTS[t]
    for p in PRODUCTS.values():
        if p.name.lower() == t or t in p.aliases or p.family == t:
            return p
    return None
