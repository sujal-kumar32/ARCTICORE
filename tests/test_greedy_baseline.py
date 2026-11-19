from src.cargo_model import Scenario, CargoItem, Trip
from src.greedy_baseline import allocate_greedy
from src.evaluation import calculate_metrics


def test_greedy_respects_all_constraints():
    scenario = Scenario(
        scenario_id="GREEDY-TEST",
        seed=1,
        cargo_items=[
            CargoItem("C1", "Critical Rations", "Food", 10, 2.0, 0.5, "Critical", True),
            CargoItem("C2", "Radio", "Communication", 4, 5.0, 1.0, "High", False),
        ],
        trips=[Trip("T1", 20.0, 4.0), Trip("T2", 20.0, 4.0)],
    )

    result = allocate_greedy(scenario)
    result.plan.validate(scenario)


def test_greedy_supports_partial_and_multiple_trips():
    scenario = Scenario(
        scenario_id="PARTIAL-TEST",
        seed=2,
        cargo_items=[CargoItem("C1", "Large cargo", "Equipment", 20, 6.0, 2.0, "Critical", True)],
        trips=[Trip("T1", 12.0, 4.0), Trip("T2", 12.0, 4.0)],
    )

    result = allocate_greedy(scenario)
    trip_ids = {allocation.trip_id for allocation in result.plan.allocations}
    assert len(trip_ids) == 2


def test_priority_weighted_fulfilment_metric():
    scenario = Scenario(
        scenario_id="METRIC-TEST",
        seed=3,
        cargo_items=[CargoItem("C1", "Critical Rations", "Food", 10, 1.0, 0.2, "Critical", True)],
        trips=[Trip("T1", 5.0, 1.0)],
    )

    result = allocate_greedy(scenario)
    metrics = calculate_metrics(scenario, result.plan)

    assert metrics["total_cargo_demand"] == 10
    assert metrics["total_cargo_delivered"] == 5
    assert metrics["total_cargo_unfulfilled"] == 5
    assert metrics["priority_weighted_fulfilment"] == 50.0
    assert metrics["unmet_critical_demand"] == 5


def test_empty_allocation_metrics_are_valid():
    scenario = Scenario(
        scenario_id="EMPTY-PLAN",
        seed=4,
        cargo_items=[CargoItem("C1", "Cargo", "Food", 10, 100.0, 100.0, "Low", False)],
        trips=[Trip("T1", 10.0, 10.0)],
    )

    result = allocate_greedy(scenario)
    metrics = calculate_metrics(scenario, result.plan)

    assert metrics["total_cargo_delivered"] == 0
    assert metrics["priority_weighted_fulfilment"] == 0.0
    assert metrics["unmet_critical_demand"] == 0
