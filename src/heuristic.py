from __future__ import annotations

from .cargo_model import CargoItem


DEFAULT_PRIORITY_WEIGHTS = {
    "Critical": 5,
    "High": 4,
    "Medium": 2,
    "Low": 1,
}


def cargo_value_score(
    item: CargoItem,
    priority_weights: dict[str, int] | None = None,
    critical_bonus: float = 2.0,
) -> float:
    weights = priority_weights or DEFAULT_PRIORITY_WEIGHTS
    priority_value = weights.get(item.priority, 0)

    weight_density = priority_value / max(item.unit_weight, 1e-9)
    volume_density = priority_value / max(item.unit_volume, 1e-9)
    critical_value = critical_bonus if item.critical_flag else 0.0

    return (
        4.0 * priority_value
        + critical_value
        + 0.12 * weight_density
        + 0.08 * volume_density
    )


def rank_cargo_items(
    cargo_items: list[CargoItem],
    priority_weights: dict[str, int] | None = None,
) -> list[CargoItem]:
    return sorted(
        cargo_items,
        key=lambda item: (
            -cargo_value_score(item, priority_weights),
            item.cargo_id,
        ),
    )
