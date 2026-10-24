from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, MutableMapping


@dataclass(frozen=True)
class UserPreferences:
    visual_density: str = "Confortável"
    motion: str = "Padrão"
    show_help: bool = True
    compact_numbers: bool = True
    ranking_size: int = 10
    default_metric: str = "Receita"
    show_anomaly_details: bool = True


PREFERENCE_PREFIX = "preference_"
ALLOWED_DENSITIES = ("Confortável", "Compacta")
ALLOWED_MOTION = ("Padrão", "Reduzida")
ALLOWED_METRICS = ("Receita", "Quantidade")
ALLOWED_RANKING_SIZES = (5, 10, 15, 20)


def preference_key(name: str) -> str:
    return f"{PREFERENCE_PREFIX}{name}"


def default_preferences() -> UserPreferences:
    return UserPreferences()


def _validated(name: str, value: Any, default: Any) -> Any:
    if name == "visual_density":
        return value if value in ALLOWED_DENSITIES else default
    if name == "motion":
        return value if value in ALLOWED_MOTION else default
    if name == "default_metric":
        return value if value in ALLOWED_METRICS else default
    if name == "ranking_size":
        return value if type(value) is int and value in ALLOWED_RANKING_SIZES else default
    if name in {"show_help", "compact_numbers", "show_anomaly_details"}:
        return value if type(value) is bool else default
    return default


def initialize_preferences(state: MutableMapping[str, Any]) -> UserPreferences:
    defaults = default_preferences()
    values: dict[str, Any] = {}
    for field in fields(defaults):
        key = preference_key(field.name)
        default = getattr(defaults, field.name)
        state[key] = _validated(field.name, state.get(key, default), default)
        values[field.name] = state[key]
    return UserPreferences(**values)


def read_preferences(state: MutableMapping[str, Any]) -> UserPreferences:
    return initialize_preferences(state)


def set_preference(state: MutableMapping[str, Any], name: str, value: Any) -> Any:
    defaults = default_preferences()
    allowed_names = {field.name for field in fields(defaults)}
    if name not in allowed_names:
        raise KeyError(f"Preferência desconhecida: {name}")
    default = getattr(defaults, name)
    validated = _validated(name, value, default)
    if validated != value:
        raise ValueError(f"Valor inválido para a preferência {name}")
    state[preference_key(name)] = validated
    return validated


def restore_preference_defaults(state: MutableMapping[str, Any]) -> UserPreferences:
    defaults = default_preferences()
    for field in fields(defaults):
        state[preference_key(field.name)] = getattr(defaults, field.name)
    return defaults


def revoke_ai_consent(state: MutableMapping[str, Any]) -> None:
    state["ai_consent"] = False


def preference_css(preferences: UserPreferences) -> str:
    compact = preferences.visual_density == "Compacta"
    reduced = preferences.motion == "Reduzida"
    rules = []
    if compact:
        rules.append(
            ".block-container{padding-top:.38rem!important}"
            "[data-testid='stVerticalBlock']{gap:.42rem!important}"
            "[data-testid='stMetric']{padding:.48rem!important}"
        )
    if reduced:
        rules.append("*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}")
    return "<style>" + "".join(rules) + "</style>"
