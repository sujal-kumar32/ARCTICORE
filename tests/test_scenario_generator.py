from src.scenario_generator import generate_scenarios, save_scenarios


def test_generate_at_least_50_scenarios():
    scenarios = generate_scenarios(count=50, cargo_count=200, trip_count=4)
    assert len(scenarios) == 50
    assert all(len(scenario.cargo_items) == 200 for scenario in scenarios)
    assert all(len(scenario.trips) == 4 for scenario in scenarios)


def test_generation_is_reproducible():
    first = generate_scenarios(count=3, base_seed=26062, cargo_count=200, trip_count=4)
    second = generate_scenarios(count=3, base_seed=26062, cargo_count=200, trip_count=4)
    assert [scenario.to_dict() for scenario in first] == [scenario.to_dict() for scenario in second]


def test_save_scenarios(tmp_path):
    scenarios = generate_scenarios(count=2, cargo_count=200, trip_count=3)
    combined_path, csv_paths = save_scenarios(scenarios, tmp_path)
    assert combined_path.exists()
    assert len(csv_paths) == 4
    assert all(path.exists() for path in csv_paths)
