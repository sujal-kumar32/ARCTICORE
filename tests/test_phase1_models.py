import pytest

from src.cargo_model import Allocation, AllocationPlan, CargoItem, Scenario, Trip


def make_scenario():
    return Scenario(
        scenario_id="TEST-001",
        seed=1,
        cargo_items=[
            CargoItem("C1", "Rations", "Food", 10, 2.0, 0.5, "Critical", True),
            CargoItem("C2", "Radio", "Communication", 4, 5.0, 1.0, "High", False),
        ],
        trips=[Trip("T1", 20.0, 4.0), Trip("T2", 20.0, 4.0)],
    )


def test_valid_scenario():
    scenario = make_scenario()
    scenario.validate()


def test_weight_capacity_validation():
    scenario = make_scenario()
    plan = AllocationPlan([Allocation("C1", "T1", 11)])
    with pytest.raises(ValueError):
        plan.validate(scenario)


def test_volume_capacity_validation():
    scenario = make_scenario()
    plan = AllocationPlan([Allocation("C1", "T1", 9)])
    with pytest.raises(ValueError):
        plan.validate(scenario)


def test_demand_over_allocation():
    scenario = make_scenario()
    plan = AllocationPlan([Allocation("C2", "T1", 5)])
    with pytest.raises(ValueError):
        plan.validate(scenario)


def test_duplicate_allocation():
    scenario = make_scenario()
    plan = AllocationPlan([
        Allocation("C1", "T1", 2),
        Allocation("C1", "T1", 1),
    ])
    with pytest.raises(ValueError, match="duplicate allocation"):
        plan.validate(scenario)


def test_missing_priority():
    item = CargoItem("C1", "Rations", "Food", 10, 2.0, 0.5, "", True)
    with pytest.raises(ValueError, match="priority"):
        item.validate()


def test_partial_and_multiple_trip_allocation():
    scenario = make_scenario()
    plan = AllocationPlan([
        Allocation("C1", "T1", 6),
        Allocation("C1", "T2", 2),
        Allocation("C2", "T2", 2),
    ])
    plan.validate(scenario)


def test_empty_scenario():
    scenario = Scenario("EMPTY", 1, [], [])
    with pytest.raises(ValueError, match="cargo item"):
        scenario.validate()


def test_invalid_priority():
    item = CargoItem("C1", "Rations", "Food", 10, 2.0, 0.5, "Urgent", True)
    with pytest.raises(ValueError, match="invalid priority"):
        item.validate()
