"""
gui/components/utils/display_format.py

Global numeric display formatting for 3psLCCA.

Change DECIMAL_PLACES once here - it propagates to every table cell,
result label, formula preview, and input field across the app.
"""

import math

DECIMAL_PLACES: int = 2

# ── Shared constants ──────────────────────────────────────────────────────────

_INDIA_THRESHOLDS = [
    (1_00_00_00_00_000, "kharab"),   # 10^11  (100 arab)
    (1_00_00_00_000,    "arab"),     # 10^9   (100 crore)
    (1_00_00_000,       "crore"),    # 10^7
    (1_00_000,          "lakh"),     # 10^5
    (1_000,             "thousand"), # 10^3
]

_UNIT_DIVISORS = {
    "thousand": 1_000,
    "lakh":     1_00_000,
    "million":  1_000_000,
    "crore":    1_00_00_000,
    "billion":  1_000_000_000,
    "arab":     1_00_00_00_000,
    "trillion": 1_000_000_000_000,
    "kharab":   1_00_00_00_00_000,
}

_WESTERN_SUFFIXES = [
    "", "thousand", "million", "billion", "trillion",
    "quadrillion", "quintillion", "sextillion",
    "septillion", "octillion", "nonillion", "decillion",
]

# ── Formatters ────────────────────────────────────────────────────────────────

def fmt(val) -> str:
    """Plain float with global decimal places.  e.g. 1234.5 → '1234.500'"""
    try:
        return f"{float(val):.{DECIMAL_PLACES}f}"
    except (TypeError, ValueError):
        return str(val)


def fmt_comma(val) -> str:
    """Float with thousands separator and global decimal places.  e.g. 12345.6 → '12,345.600'"""
    try:
        return f"{float(val):,.{DECIMAL_PLACES}f}"
    except (TypeError, ValueError):
        return str(val)


def _fmt_currency_inr(v: float, d: int) -> str:
    """Format a non-negative float using the Indian numbering system (12,34,567.89)."""
    s = f"{v:.{d}f}"
    parts = s.split(".")
    integer_part = parts[0]
    decimal_part = "." + parts[1] if len(parts) > 1 else ""

    if len(integer_part) <= 3:
        return integer_part + decimal_part

    last_three = integer_part[-3:]
    rest = integer_part[:-3]

    # Group rest in pairs of 2 from the right; leftmost group may be 1 or 2 digits
    groups = []
    while len(rest) > 2:
        groups.append(rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.append(rest)

    return ",".join(reversed(groups)) + "," + last_three + decimal_part


def fmt_currency(val, currency="INR", decimals=None, fmt="comma") -> str:
    """Format a numeric value as a currency string.

    fmt:
      "comma"  → "12,34,567"           (INR: Indian grouping; others: Western)
      "short"  → "1 crore"             (INR: _format_number_india; others: format_number)
      "both"   → "12,34,567 (1 crore)"
    """
    try:
        v = float(val)
        d = DECIMAL_PLACES if decimals is None else decimals
        sign = "-" if v < 0 else ""
        abs_v = abs(v)

        # if currency == "INR":
        #     comma_str = sign + _fmt_currency_inr(abs_v, d)
        #     short_str = (sign + _format_number_india(abs_v)) if abs_v > 0 else "0"
        # else:
        comma_str = f"{sign}{abs_v:,.{d}f}"
        short_str = format_number(v)

        if fmt == "comma":
            return comma_str
        if fmt == "short":
            return short_str
        return f"{comma_str} ({short_str})"

    except (TypeError, ValueError):
        return str(val)


def fmt_pct(val) -> str:
    """Percentage - always 1 decimal place regardless of DECIMAL_PLACES."""
    try:
        return f"{float(val):.1f}"
    except (TypeError, ValueError):
        return str(val)


def _format_number_india(n: float) -> str:
    """Format a non-negative number using Indian suffixes (lakh, crore)."""
    for threshold, suffix in _INDIA_THRESHOLDS:
        if n >= threshold:
            value = round(n / threshold, 2)
            value = int(value) if float(value).is_integer() else value
            return f"{value} {suffix}"
    return f"{n:g}"


def fmt_unit(n, unit: str) -> str:
    """Express n in the given unit and return a labelled string.

    fmt_unit(15_000_000, "crore")      → "1.5 crore"
    fmt_unit(2_500_000_000, "billion") → "2.5 billion"
    fmt_unit(750_000, "lakh")          → "7.5 lakh"
    """
    try:
        n = float(n)
    except (TypeError, ValueError):
        return str(n)

    divisor = _UNIT_DIVISORS.get(unit.lower(), 1)
    sign = "-" if n < 0 else ""
    val = round(abs(n) / divisor, 2)
    val = int(val) if float(val).is_integer() else val
    return f"{sign}{val} {unit}"


def format_number(n) -> str:
    """Format a number with Western suffixes (thousand, million, billion …)."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return str(n)

    if n == 0:
        return "0"

    sign = "-" if n < 0 else ""
    n = abs(n)

    if n < 1000:
        return f"{sign}{n:g}"

    idx = int(math.log10(n) // 3)

    if idx >= len(_WESTERN_SUFFIXES):
        return f"{sign}{n:.2e}"

    value = round(n / (10 ** (idx * 3)), 2)
    if float(value).is_integer():
        value = int(value)

    return f"{sign}{value} {_WESTERN_SUFFIXES[idx]}"
