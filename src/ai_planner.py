from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from .cargo_model import Allocation, AllocationPlan, Scenario
from .heuristic import DEFAULT_PRIORITY_WEIGHTS, rank_cargo_items


@dataclass
class BeamState:
    remaining_quantity: dict[str, int]
    remaining_weight: dict[str, float]
    remaining_volume: dict[str, float]
    allocations: list[Allocation]
    objective: float


@dataclass
class AIResult:
    plan: AllocationPlan
    execution_time_seconds: float
    states_explored: int


def allocation_objective(
    scenario: Scenario,
    remaining_quantity: dict[str, int],
    priority_weights: dict[str, int],
    critical_penalty: float,
) -> float:
    value = 0.0
    cargo_by_id = {item.cargo_id: item for item in scenario.cargo_items}

    for cargo_id, remaining in remaining_quantity.items():
        item = cargo_by_id[cargo_id]
        delivered = item.quantity - remaining
        value += priority_weights.get(item.priority, 0) * delivered
        if item.critical_flag:
            value -= critical_penalty * remaining

    return value


def allocate_ai(
    scenario: Scenario,
    priority_weights: dict[str, int] | None = None,
    beam_width: int = 24,
    critical_penalty: float = 1.5,
) -> AIResult:
    scenario.validate()
    if beam_width < 1:
        raise ValueError("beam_width must be positive")

    weights = priority_weights or DEFAULT_PRIORITY_WEIGHTS
    start = perf_counter()

    remaining_quantity = {item.cargo_id: item.quantity for item in scenario.cargo_items}
    initial_state = BeamState(
        remaining_quantity=remaining_quantity.copy(),
        remaining_weight={trip.trip_id: trip.maximum_weight for trip in scenario.trips},
        remaining_volume={trip.trip_id: trip.maximum_volume for trip in scenario.trips},
        allocations=[],
        objective=0.0,
    )

    beam = [initial_state]
    states_explored = 1
    ranked_items = rank_cargo_items(scenario.cargo_items, weights)

    cargo_by_id = {item.cargo_id: item for item in scenario.cargo_items}

    for item in ranked_items:
        next_states: list[BeamState] = []

        for state in beam:
            remaining = state.remaining_quantity[item.cargo_id]

            # A reject-or-defer branch preserves feasible states for later items.
            if remaining > 0:
                next_states.append(BeamState(
                    remaining_quantity=state.remaining_quantity.copy(),
                    remaining_weight=state.remaining_weight.copy(),
                    remaining_volume=state.remaining_volume.copy(),
                    allocations=list(state.allocations),
                    objective=allocation_objective(
                        scenario, state.remaining_quantity, weights, critical_penalty
                    ),
                ))

            for trip in scenario.trips:
                if remaining == 0:
                    break

                weight_limited = int(
                    (state.remaining_weight[trip.trip_id] + 1e-9) // item.unit_weight
                )
                volume_limited = int(
                    (state.remaining_volume[trip.trip_id] + 1e-9) // item.unit_volume
                )
                quantity = min(remaining, weight_limited, volume_limited)

                if quantity <= 0:
                    continue

                new_remaining = state.remaining_quantity.copy()
                new_remaining[item.cargo_id] -= quantity
                new_weight = state.remaining_weight.copy()
                new_volume = state.remaining_volume.copy()
                new_weight[trip.trip_id] -= quantity * item.unit_weight
                new_volume[trip.trip_id] -= quantity * item.unit_volume

                new_allocations = list(state.allocations)
                new_allocations.append(Allocation(item.cargo_id, trip.trip_id, quantity))

                objective = allocation_objective(
                    scenario, new_remaining, weights, critical_penalty
                )

                next_states.append(BeamState(
                    remaining_quantity=new_remaining,
                    remaining_weight=new_weight,
                    remaining_volume=new_volume,
                    allocations=new_allocations,
                    objective=objective,
                ))

            # Distribute this cargo across trips in a single candidate state.
            distributed_remaining = state.remaining_quantity.copy()
            distributed_weight = state.remaining_weight.copy()
            distributed_volume = state.remaining_volume.copy()
            distributed_allocations = list(state.allocations)

            for trip in scenario.trips:
                quantity_left = distributed_remaining[item.cargo_id]
                if quantity_left <= 0:
                    break

                weight_limited = int(
                    (distributed_weight[trip.trip_id] + 1e-9) // item.unit_weight
                )
                volume_limited = int(
                    (distributed_volume[trip.trip_id] + 1e-9) // item.unit_volume
                )
                quantity = min(quantity_left, weight_limited, volume_limited)

                if quantity <= 0:
                    continue

                distributed_remaining[item.cargo_id] -= quantity
                distributed_weight[trip.trip_id] -= quantity * item.unit_weight
                distributed_volume[trip.trip_id] -= quantity * item.unit_volume
                distributed_allocations.append(
                    Allocation(item.cargo_id, trip.trip_id, quantity)
                )

            if len(distributed_allocations) > len(state.allocations):
                next_states.append(BeamState(
                    remaining_quantity=distributed_remaining,
                    remaining_weight=distributed_weight,
                    remaining_volume=distributed_volume,
                    allocations=distributed_allocations,
                    objective=allocation_objective(
                        scenario,
                        distributed_remaining,
                        weights,
                        critical_penalty,
                    ),
                ))

        states_explored += len(next_states)

        # Deduplicate states with identical remaining demand and residual capacity.
        unique: dict[tuple, BeamState] = {}
        for candidate in next_states:
            key = (
                tuple(candidate.remaining_quantity[c.cargo_id] for c in ranked_items),
                tuple(round(candidate.remaining_weight[t.trip_id], 6) for t in scenario.trips),
                tuple(round(candidate.remaining_volume[t.trip_id], 6) for t in scenario.trips),
            )
            existing = unique.get(key)
            if existing is None or candidate.objective > existing.objective:
                unique[key] = candidate

        beam = sorted(
            unique.values(),
            key=lambda state: (-state.objective, len(state.allocations)),
        )[:beam_width]

    best = max(beam, key=lambda state: state.objective)
    plan = AllocationPlan(best.allocations)
    plan.validate(scenario)

    return AIResult(
        plan=plan,
        execution_time_seconds=perf_counter() - start,
        states_explored=states_explored,
    )
