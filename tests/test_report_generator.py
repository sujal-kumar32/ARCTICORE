from src.report_generator import generate_pdf_report, save_csv_report, save_json_report


def test_csv_and_json_report_generation(tmp_path):
    rows = [{"scenario_id": "SCENARIO-001", "greedy_priority_weighted_fulfilment": 10.0, "ai_priority_weighted_fulfilment": 12.0}]

    csv_path = save_csv_report(rows, tmp_path / "report.csv")
    json_path = save_json_report(rows, tmp_path / "report.json")

    assert csv_path.exists()
    assert json_path.exists()


def test_pdf_report_generation(tmp_path):
    rows = [{
        "scenario_id": "SCENARIO-001",
        "greedy_priority_weighted_fulfilment": 10.0,
        "ai_priority_weighted_fulfilment": 12.0,
        "greedy_weight_utilization": 70.0,
        "ai_weight_utilization": 80.0,
        "greedy_volume_utilization": 90.0,
        "ai_volume_utilization": 75.0,
        "greedy_unmet_critical_demand": 10,
        "ai_unmet_critical_demand": 8,
    }]

    pdf_path = generate_pdf_report(rows, tmp_path / "report.pdf")
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
