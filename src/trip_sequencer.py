from __future__ import annotations

from .cargo_model import AllocationPlan, Scenario


PRIORITY_SEQUENCE = {
    "Critical": 0,
    "High": 1,
    "Medium": 2,
    "Low": 3,
}


def sequence_trip_manifest(
    scenario: Scenario,
    plan: AllocationPlan,
    trip_id: str,
) -> list[dict]:
    scenario.validate()
    plan.validate(scenario)

    trip_ids = {trip.trip_id for trip in scenario.trips}
    if trip_id not in trip_ids:
        raise ValueError(f"unknown trip_id: {trip_id}")

    cargo_by_id = {item.cargo_id: item for item in scenario.cargo_items}

    allocations = [
        allocation
        for allocation in plan.allocations
        if allocation.trip_id == trip_id and allocation.quantity > 0
    ]

    allocations.sort(key=lambda allocation: (
        PRIORITY_SEQUENCE.get(cargo_by_id[allocation.cargo_id].priority, 99),
        not cargo_by_id[allocation.cargo_id].critical_flag,
        cargo_by_id[allocation.cargo_id].cargo_id,
    ))

    sequence = []
    for loading_position, allocation in enumerate(allocations, start=1):
        item = cargo_by_id[allocation.cargo_id]
        sequence.append({
            "loading_position": loading_position,
            "cargo_id": item.cargo_id,
            "cargo_name": item.cargo_name,
            "category": item.category,
            "quantity": allocation.quantity,
            "priority": item.priority,
            "critical_flag": item.critical_flag,
            "weight": round(allocation.quantity * item.unit_weight, 4),
            "volume": round(allocation.quantity * item.unit_volume, 4),
        })

    return sequence


def remaining_trip_capacity(
    scenario: Scenario,
    plan: AllocationPlan,
) -> list[dict]:
    plan.validate(scenario)
    cargo_by_id = {item.cargo_id: item for item in scenario.cargo_items}

    consumed_weight = {trip.trip_id: 0.0 for trip in scenario.trips}
    consumed_volume = {trip.trip_id: 0.0 for trip in scenario.trips}

    for allocation in plan.allocations:
        item = cargo_by_id[allocation.cargo_id]
        consumed_weight[allocation.trip_id] += allocation.quantity * item.unit_weight
        consumed_volume[allocation.trip_id] += allocation.quantity * item.unit_volume

    return [
        {
            "trip_id": trip.trip_id,
            "maximum_weight": trip.maximum_weight,
            "maximum_volume": trip.maximum_volume,
            "remaining_weight": round(trip.maximum_weight - consumed_weight[trip.trip_id], 4),
            "remaining_volume": round(trip.maximum_volume - consumed_volume[trip.trip_id], 4),
            "weight_utilization": round(100 * consumed_weight[trip.trip_id] / trip.maximum_weight, 4),
            "volume_utilization": round(100 * consumed_volume[trip.trip_id] / trip.maximum_volume, 4),
        }
        for trip in scenario.trips
    ]
