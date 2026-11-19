from __future__ import annotations

from collections import defaultdict

from .cargo_model import AllocationPlan, Scenario


DEFAULT_PRIORITY_WEIGHTS = {
    "Critical": 5,
    "High": 4,
    "Medium": 2,
    "Low": 1,
}


def calculate_delivered_quantities(
    scenario: Scenario,
    plan: AllocationPlan,
) -> dict[str, int]:
    delivered = defaultdict(int)
    for allocation in plan.allocations:
        delivered[allocation.cargo_id] += allocation.quantity
    return dict(delivered)


def calculate_metrics(
    scenario: Scenario,
    plan: AllocationPlan,
    priority_weights: dict[str, int] | None = None,
) -> dict:
    scenario.validate()
    plan.validate(scenario)
    weights = priority_weights or DEFAULT_PRIORITY_WEIGHTS

    cargo_by_id = {item.cargo_id: item for item in scenario.cargo_items}
    delivered_by_id = calculate_delivered_quantities(scenario, plan)

    total_demand = sum(item.quantity for item in scenario.cargo_items)
    total_delivered = sum(delivered_by_id.values())
    total_unfulfilled = total_demand - total_delivered

    weighted_delivered = 0.0
    weighted_demand = 0.0
    unmet_critical = 0

    transported_weight = 0.0
    transported_volume = 0.0

    for item in scenario.cargo_items:
        delivered = delivered_by_id.get(item.cargo_id, 0)
        weight = weights.get(item.priority, 0)
        weighted_delivered += weight * delivered
        weighted_demand += weight * item.quantity
        transported_weight += delivered * item.unit_weight
        transported_volume += delivered * item.unit_volume

        if item.critical_flag:
            unmet_critical += max(0, item.quantity - delivered)

    fulfilment_rate = (
        100.0 * weighted_delivered / weighted_demand
        if weighted_demand > 0
        else 0.0
    )

    total_weight_capacity = sum(trip.maximum_weight for trip in scenario.trips)
    total_volume_capacity = sum(trip.maximum_volume for trip in scenario.trips)

    weight_utilization = (
        100.0 * transported_weight / total_weight_capacity
        if total_weight_capacity > 0
        else 0.0
    )
    volume_utilization = (
        100.0 * transported_volume / total_volume_capacity
        if total_volume_capacity > 0
        else 0.0
    )

    utilized_trips = {
        allocation.trip_id
        for allocation in plan.allocations
        if allocation.quantity > 0
    }

    return {
        "priority_weighted_fulfilment": round(fulfilment_rate, 4),
        "weight_utilization": round(weight_utilization, 4),
        "volume_utilization": round(volume_utilization, 4),
        "unmet_critical_demand": unmet_critical,
        "total_cargo_demand": total_demand,
        "total_cargo_delivered": total_delivered,
        "total_cargo_unfulfilled": total_unfulfilled,
        "trips_utilized": len(utilized_trips),
        "transported_weight": round(transported_weight, 4),
        "transported_volume": round(transported_volume, 4),
        "total_weight_capacity": round(total_weight_capacity, 4),
        "total_volume_capacity": round(total_volume_capacity, 4),
    }
