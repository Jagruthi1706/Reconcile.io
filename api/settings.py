from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from api.models import ApplicationSetting

DEFAULTS = {
    "matching_rules": {
        "match_auto_accept_confidence": "0.90",
        "match_amount_tolerance_pct": "1.5",
        "match_date_window_days": 5,
    },
    "tax_rules": [],
}


async def get_setting(session: AsyncSession, key: str) -> dict[str, object]:
    setting = await session.get(ApplicationSetting, key)
    if setting is None:
        return DEFAULTS[key].copy()
    return dict(setting.value)


async def update_setting(session: AsyncSession, key: str, value: dict[str, object]) -> dict[str, object]:
    setting = await session.get(ApplicationSetting, key)
    if setting is None:
        setting = ApplicationSetting(key=key, value=value)
        session.add(setting)
    else:
        setting.value = value
    await session.commit()
    return dict(setting.value)


def matching_rules_response(values: dict[str, object]) -> dict[str, object]:
    return {
        "match_auto_accept_confidence": Decimal(str(values["match_auto_accept_confidence"])),
        "match_amount_tolerance_pct": Decimal(str(values["match_amount_tolerance_pct"])),
        "match_date_window_days": int(values["match_date_window_days"]),
    }
