import re
from datetime import date, timedelta


WEEKDAY_NAMES = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}
NEXT_WEEKDAY_PATTERN = re.compile(r"^next\s+(\w+)$")
TEST_EXPRESSIONS = ("tomorrow", "next Monday", "next Friday", "next week")
TEST_RANGE_CASES = (
    ("next Monday", 3),
    ("tomorrow", None),
    ("next week", 3),
)


def resolve_date_expression(expression: str, today: date) -> tuple[date, date] | None:
    """Resolve a supported relative date expression into an inclusive date range."""
    normalized_expression = expression.strip().casefold()
    if normalized_expression == "today":
        return today, today
    if normalized_expression == "tomorrow":
        tomorrow = today + timedelta(days=1)
        return tomorrow, tomorrow

    weekday_match = NEXT_WEEKDAY_PATTERN.fullmatch(normalized_expression)
    if weekday_match is None:
        return None

    target_weekday = WEEKDAY_NAMES.get(weekday_match.group(1))
    if target_weekday is None:
        return None

    days_until_next_monday = 7 - today.weekday()
    resolved_date = today + timedelta(
        days=days_until_next_monday + target_weekday
    )
    return resolved_date, resolved_date


def resolve_date_range(
    expression: str, duration_days: int | None, today: date
) -> tuple[date, date] | None:
    """Resolve a supported expression and expand it to the requested duration."""
    resolved_dates = resolve_date_expression(expression, today)
    if resolved_dates is None:
        return None

    start_date, _ = resolved_dates
    if duration_days is None:
        return start_date, start_date
    if duration_days <= 0:
        raise ValueError("Duration must be a positive number of days.")
    return start_date, start_date + timedelta(days=duration_days - 1)


def main() -> None:
    today = date(2026, 9, 16)
    for expression in TEST_EXPRESSIONS:
        resolved_dates = resolve_date_expression(expression, today)
        if resolved_dates is None:
            print(f"{expression}: ambiguous")
            continue

        start_date, end_date = resolved_dates
        print(f"{expression}: {start_date} to {end_date}")

    print()
    for expression, duration_days in TEST_RANGE_CASES:
        resolved_dates = resolve_date_range(expression, duration_days, today)
        if resolved_dates is None:
            print(f"{expression}, {duration_days}: ambiguous")
            continue

        start_date, end_date = resolved_dates
        print(f"{expression}, {duration_days}: {start_date} to {end_date}")


if __name__ == "__main__":
    main()
