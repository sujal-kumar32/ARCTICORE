from src.ai_planner import allocate_ai
from src.cargo_model import CargoItem, Scenario, Trip
from src.greedy_baseline import allocate_greedy


def make_scenario():
    return Scenario(
        scenario_id="AI-TEST",
        seed=1,
        cargo_items=[
            CargoItem("C1", "Critical Rations", "Food", 10, 2.0, 0.5, "Critical", True),
            CargoItem("C2", "Radio", "Communication", 4, 5.0, 1.0, "High", False),
            CargoItem("C3", "Samples", "Science", 20, 1.0, 0.2, "Medium", False),
        ],
        trips=[Trip("T1", 20.0, 4.0), Trip("T2", 20.0, 4.0)],
    )


def test_ai_plan_is_valid():
    scenario = make_scenario()
    result = allocate_ai(scenario, beam_width=12)
    result.plan.validate(scenario)


def test_ai_supports_partial_allocation():
    scenario = Scenario(
        scenario_id="AI-PARTIAL",
        seed=2,
        cargo_items=[CargoItem("C1", "Heavy Item", "Equipment", 20, 6.0, 2.0, "Critical", True)],
        trips=[Trip("T1", 12.0, 4.0), Trip("T2", 12.0, 4.0)],
    )

    result = allocate_ai(scenario, beam_width=8)
    assert sum(allocation.quantity for allocation in result.plan.allocations) == 4


def test_ai_planner_has_bounded_search_tracking():
    scenario = make_scenario()
    result = allocate_ai(scenario, beam_width=6)
    assert result.states_explored >= 1


def test_ai_and_greedy_evaluate_same_scenario():
    scenario = make_scenario()
    ai_result = allocate_ai(scenario, beam_width=12)
    greedy_result = allocate_greedy(scenario)

    ai_result.plan.validate(scenario)
    greedy_result.plan.validate(scenario)
