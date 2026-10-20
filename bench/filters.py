"""Filters for games and reference games: 'max_depth>9,end_reason~ant'.

Clauses are joined by ','; each is field=value, field>value, field<value or field~substring
(case-insensitive). > and < compare numbers only. A record missing the field never matches."""
import re

_CLAUSE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*([=<>~])\s*([^=<>~]*?)\s*$")


def _number(text):
    try:
        return float(text)
    except ValueError:
        return None


def parse_where(where):
    if not where:
        return lambda record: True
    tests = []
    for clause in where.split(","):
        m = _CLAUSE.match(clause)
        if m is None:
            raise ValueError(f"bad filter clause {clause!r}; use field=value, field>n, field<n or field~text")
        tests.append(m.groups())

    def match(record):
        for field, op, raw in tests:
            if field not in record:
                return False
            value = record[field]
            if op == "~":
                if raw.lower() not in str(value).lower():
                    return False
            elif op == "=":
                want = _number(raw)
                if isinstance(value, (int, float)) and want is not None:
                    if float(value) != want:
                        return False
                elif str(value) != raw:
                    return False
            else:
                want = _number(raw)
                if want is None or not isinstance(value, (int, float)):
                    return False
                if (op == ">" and not value > want) or (op == "<" and not value < want):
                    return False
        return True

    return match
