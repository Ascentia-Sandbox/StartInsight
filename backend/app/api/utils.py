"""Shared API utilities."""


def escape_like(value: str) -> str:
    """Escape SQL LIKE/ILIKE wildcard characters (% and _).

    Prevents user input containing % or _ from being interpreted
    as SQL wildcards in LIKE/ILIKE queries.
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
