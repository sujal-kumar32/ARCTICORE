from src.ai_planner import allocate_ai
from src.cargo_model import CargoItem, Scenario, Trip
from src.trip_sequencer import remaining_trip_capacity, sequence_trip_manifest


def test_loading_sequence_prioritizes_critical_items():
    scenario = Scenario(
        scenario_id="SEQUENCE",
        seed=1,
        cargo_items=[
            CargoItem("C1", "Low Cargo", "Food", 3, 1.0, 0.2, "Low", False),
            CargoItem("C2", "Critical Cargo", "Medical", 3, 1.0, 0.2, "Critical", True),
        ],
        trips=[Trip("T1", 10.0, 2.0)],
    )

    plan = allocate_ai(scenario, beam_width=4).plan
    sequence = sequence_trip_manifest(scenario, plan, "T1")

    assert sequence[0]["priority"] == "Critical"


def test_trip_remaining_capacity_is_calculated():
    scenario = Scenario(
        scenario_id="CAPACITY",
        seed=2,
        cargo_items=[CargoItem("C1", "Cargo", "Food", 4, 2.0, 0.5, "High", False)],
        trips=[Trip("T1", 10.0, 3.0)],
    )

    plan = allocate_ai(scenario, beam_width=4).plan
    remaining = remaining_trip_capacity(scenario, plan)

    assert len(remaining) == 1
    assert remaining[0]["remaining_weight"] >= 0
    assert remaining[0]["remaining_volume"] >= 0
