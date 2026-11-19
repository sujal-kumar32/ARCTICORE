from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable, Sequence


VALID_PRIORITIES = {"Critical", "High", "Medium", "Low"}


@dataclass(frozen=True)
class CargoItem:
    cargo_id: str
    cargo_name: str
    category: str
    quantity: int
    unit_weight: float
    unit_volume: float
    priority: str
    critical_flag: bool

    def validate(self) -> None:
        if not self.cargo_id.strip():
            raise ValueError("cargo_id cannot be empty")
        if not self.cargo_name.strip():
            raise ValueError("cargo_name cannot be empty")
        if not self.category.strip():
            raise ValueError("category cannot be empty")
        if not isinstance(self.quantity, int) or isinstance(self.quantity, bool) or self.quantity < 0:
            raise ValueError("quantity must be a non-negative integer")
        if self.unit_weight <= 0:
            raise ValueError("unit_weight must be positive")
        if self.unit_volume <= 0:
            raise ValueError("unit_volume must be positive")
        if not self.priority:
            raise ValueError("priority must be provided")
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"invalid priority: {self.priority}")
        if not isinstance(self.critical_flag, bool):
            raise ValueError("critical_flag must be boolean")


@dataclass(frozen=True)
class Trip:
    trip_id: str
    maximum_weight: float
    maximum_volume: float

    def validate(self) -> None:
        if not self.trip_id.strip():
            raise ValueError("trip_id cannot be empty")
        if self.maximum_weight <= 0:
            raise ValueError("maximum_weight must be positive")
        if self.maximum_volume <= 0:
            raise ValueError("maximum_volume must be positive")


@dataclass
class Scenario:
    scenario_id: str
    seed: int
    cargo_items: list[CargoItem]
    trips: list[Trip]

    def validate(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id cannot be empty")
        if not self.cargo_items:
            raise ValueError("scenario must contain at least one cargo item")
        if not self.trips:
            raise ValueError("scenario must contain at least one trip")

        cargo_ids = [item.cargo_id for item in self.cargo_items]
        trip_ids = [trip.trip_id for trip in self.trips]
        if len(cargo_ids) != len(set(cargo_ids)):
            raise ValueError("cargo_id values must be unique")
        if len(trip_ids) != len(set(trip_ids)):
            raise ValueError("trip_id values must be unique")

        for item in self.cargo_items:
            item.validate()
        for trip in self.trips:
            trip.validate()

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "cargo_items": [asdict(item) for item in self.cargo_items],
            "trips": [asdict(trip) for trip in self.trips],
        }


@dataclass
class Allocation:
    cargo_id: str
    trip_id: str
    quantity: int


@dataclass
class AllocationPlan:
    allocations: list[Allocation] = field(default_factory=list)

    def validate(self, scenario: Scenario) -> None:
        cargo_by_id = {item.cargo_id: item for item in scenario.cargo_items}
        trip_by_id = {trip.trip_id: trip for trip in scenario.trips}

        demanded: dict[str, int] = {}
        trip_weight: dict[str, float] = {trip_id: 0.0 for trip_id in trip_by_id}
        trip_volume: dict[str, float] = {trip_id: 0.0 for trip_id in trip_by_id}
        seen_pairs: set[tuple[str, str]] = set()

        for allocation in self.allocations:
            pair = (allocation.cargo_id, allocation.trip_id)
            if pair in seen_pairs:
                raise ValueError(f"duplicate allocation: cargo {allocation.cargo_id} to trip {allocation.trip_id}")
            seen_pairs.add(pair)

            if allocation.cargo_id not in cargo_by_id:
                raise ValueError(f"unknown cargo_id: {allocation.cargo_id}")
            if allocation.trip_id not in trip_by_id:
                raise ValueError(f"unknown trip_id: {allocation.trip_id}")
            if not isinstance(allocation.quantity, int) or isinstance(allocation.quantity, bool):
                raise ValueError("allocation quantity must be an integer")
            if allocation.quantity < 0:
                raise ValueError("allocation quantity cannot be negative")

            item = cargo_by_id[allocation.cargo_id]
            trip = trip_by_id[allocation.trip_id]
            demanded[allocation.cargo_id] = demanded.get(allocation.cargo_id, 0) + allocation.quantity
            if demanded[allocation.cargo_id] > item.quantity:
                raise ValueError(f"demand over-allocation for cargo {allocation.cargo_id}")

            trip_weight[allocation.trip_id] += allocation.quantity * item.unit_weight
            trip_volume[allocation.trip_id] += allocation.quantity * item.unit_volume

            if trip_weight[allocation.trip_id] > trip.maximum_weight + 1e-9:
                raise ValueError(f"weight capacity exceeded for trip {allocation.trip_id}")
            if trip_volume[allocation.trip_id] > trip.maximum_volume + 1e-9:
                raise ValueError(f"volume capacity exceeded for trip {allocation.trip_id}")


def scenario_from_dict(data: dict) -> Scenario:
    cargo_items = [CargoItem(**item) for item in data["cargo_items"]]
    trips = [Trip(**trip) for trip in data["trips"]]
    scenario = Scenario(
        scenario_id=data["scenario_id"],
        seed=int(data["seed"]),
        cargo_items=cargo_items,
        trips=trips,
    )
    scenario.validate()
    return scenario
