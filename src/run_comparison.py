from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ai_planner import allocate_ai
from src.evaluation import calculate_metrics
from src.greedy_baseline import allocate_greedy
from src.scenario_generator import load_scenarios_json


def run_experiment(scenario_limit: int | None = None) -> list[dict]:
    scenario_path = PROJECT_ROOT / "data" / "scenarios" / "scenarios.json"
    scenarios = load_scenarios_json(scenario_path)
    if scenario_limit is not None:
        scenarios = scenarios[:scenario_limit]

    rows = []
    for scenario in scenarios:
        greedy_result = allocate_greedy(scenario)
        ai_result = allocate_ai(scenario, beam_width=24)

        greedy_metrics = calculate_metrics(scenario, greedy_result.plan)
        ai_metrics = calculate_metrics(scenario, ai_result.plan)

        rows.append({
            "scenario_id": scenario.scenario_id,
            "seed": scenario.seed,
            "greedy_priority_weighted_fulfilment": greedy_metrics["priority_weighted_fulfilment"],
            "ai_priority_weighted_fulfilment": ai_metrics["priority_weighted_fulfilment"],
            "greedy_weight_utilization": greedy_metrics["weight_utilization"],
            "ai_weight_utilization": ai_metrics["weight_utilization"],
            "greedy_volume_utilization": greedy_metrics["volume_utilization"],
            "ai_volume_utilization": ai_metrics["volume_utilization"],
            "greedy_unmet_critical_demand": greedy_metrics["unmet_critical_demand"],
            "ai_unmet_critical_demand": ai_metrics["unmet_critical_demand"],
            "greedy_execution_time_seconds": round(greedy_result.execution_time_seconds, 6),
            "ai_execution_time_seconds": round(ai_result.execution_time_seconds, 6),
            "greedy_states_explored": greedy_result.states_explored,
            "ai_states_explored": ai_result.states_explored,
        })

    return rows


def save_results(rows: list[dict]) -> tuple[Path, Path]:
    output_dir = PROJECT_ROOT / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "comparison_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path = output_dir / "comparison_results.json"
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return csv_path, json_path


if __name__ == "__main__":
    results = run_experiment()
    csv_path, json_path = save_results(results)
    print(f"Compared {len(results)} scenarios")
    print(csv_path)
    print(json_path)
