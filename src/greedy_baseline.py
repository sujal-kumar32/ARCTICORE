from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from .cargo_model import Allocation, AllocationPlan, Scenario


DEFAULT_PRIORITY_WEIGHTS = {
    "Critical": 5,
    "High": 4,
    "Medium": 2,
    "Low": 1,
}


@dataclass
class GreedyResult:
    plan: AllocationPlan
    execution_time_seconds: float
    states_explored: int = 1


def allocate_greedy(
    scenario: Scenario,
    priority_weights: dict[str, int] | None = None,
) -> GreedyResult:
    scenario.validate()
    weights = priority_weights or DEFAULT_PRIORITY_WEIGHTS

    start = perf_counter()
    remaining_quantity = {
        item.cargo_id: item.quantity
        for item in scenario.cargo_items
    }
    remaining_weight = {
        trip.trip_id: trip.maximum_weight
        for trip in scenario.trips
    }
    remaining_volume = {
        trip.trip_id: trip.maximum_volume
        for trip in scenario.trips
    }

    ordered_items = sorted(
        scenario.cargo_items,
        key=lambda item: (-weights.get(item.priority, 0), item.cargo_id),
    )

    allocations: list[Allocation] = []

    for item in ordered_items:
        remaining = remaining_quantity[item.cargo_id]
        if remaining == 0:
            continue

        for trip in scenario.trips:
            if remaining == 0:
                break

            weight_limited = int((remaining_weight[trip.trip_id] + 1e-9) // item.unit_weight)
            volume_limited = int((remaining_volume[trip.trip_id] + 1e-9) // item.unit_volume)
            allocated = min(remaining, weight_limited, volume_limited)

            if allocated > 0:
                allocations.append(Allocation(item.cargo_id, trip.trip_id, allocated))
                remaining -= allocated
                remaining_weight[trip.trip_id] -= allocated * item.unit_weight
                remaining_volume[trip.trip_id] -= allocated * item.unit_volume

        remaining_quantity[item.cargo_id] = remaining

    plan = AllocationPlan(allocations)
    plan.validate(scenario)

    return GreedyResult(
        plan=plan,
        execution_time_seconds=perf_counter() - start,
        states_explored=len(ordered_items),
    )
