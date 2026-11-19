from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ai_planner import allocate_ai
from src.evaluation import calculate_metrics
from src.greedy_baseline import allocate_greedy
from src.report_generator import generate_pdf_report, save_csv_report, save_json_report
from src.scenario_generator import generate_scenarios, load_scenarios_json, save_scenarios
from src.trip_sequencer import remaining_trip_capacity, sequence_trip_manifest


st.set_page_config(
    page_title="Arcticore Logistics",
    page_icon="❄️",
    layout="wide",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #071827 0%, #0b2438 70%, #102f46 100%) !important;
}
[data-testid="stHeader"] {
    background: rgba(7, 24, 39, 0.92) !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #12355b 0%, #0b263b 100%) !important;
    border-right: 1px solid #315875;
}
[data-testid="stSidebar"] * {
    color: #edf7ff !important;
}
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3,
[data-testid="stMain"] p,
[data-testid="stMain"] label,
[data-testid="stMain"] span,
[data-testid="stMain"] div {
    color: #edf7ff !important;
}
[data-testid="stMetric"] {
    background: #102f46;
    border: 1px solid #315875;
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
}
[data-testid="stMetricLabel"] p,
[data-testid="stMetricValue"] {
    color: #edf7ff !important;
}
[data-testid="stDataFrame"] {
    background: #102f46;
    border: 1px solid #315875;
    border-radius: 10px;
}
.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {
    background-color: #102f46 !important;
    color: #edf7ff !important;
    border-color: #4a7695 !important;
}
[data-testid="stAlert"] {
    background: #102f46;
    color: #edf7ff;
}
button[kind="primary"] {
    background: #35a7cb !important;
    color: #071827 !important;
    border: 0;
}
hr { border-color: #315875; }
</style>
""", unsafe_allow_html=True)

SCENARIO_PATH = PROJECT_ROOT / "data" / "scenarios" / "scenarios.json"
RESULTS_PATH = PROJECT_ROOT / "data" / "results" / "comparison_results.csv"


@st.cache_data
def load_scenarios():
    if SCENARIO_PATH.exists():
        return load_scenarios_json(SCENARIO_PATH)
    return generate_scenarios(count=50)


if "scenarios" not in st.session_state:
    st.session_state.scenarios = load_scenarios()
scenarios = st.session_state.scenarios
comparison = pd.read_csv(RESULTS_PATH) if RESULTS_PATH.exists() else pd.DataFrame()

st.sidebar.title("❄️ Arcticore")
st.sidebar.caption("Polar Expedition Logistics")
page = st.sidebar.radio("Navigation", [
    "Dashboard Overview",
    "Scenario Generator",
    "Cargo Manifest",
    "AI Cargo Planner",
    "Greedy Baseline",
    "Algorithm Comparison",
    "Trip Details",
    "Reports",
])

if page == "Dashboard Overview":
    st.title("Polar Logistics Overview")
    st.caption("Synthetic academic demonstration — not an official MoES manifest")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Scenarios", len(scenarios))
    col2.metric("Cargo items", sum(len(s.cargo_items) for s in scenarios))
    col3.metric("Trips", sum(len(s.trips) for s in scenarios))

    if not comparison.empty:
        col4.metric("AI weighted fulfilment", f"{comparison['ai_priority_weighted_fulfilment'].mean():.2f}%")

    if not comparison.empty:
        chart_df = pd.DataFrame({
            "Algorithm": ["Greedy", "AI Planner"],
            "Fulfilment": [
                comparison["greedy_priority_weighted_fulfilment"].mean(),
                comparison["ai_priority_weighted_fulfilment"].mean(),
            ],
        })
        fig = px.bar(
            chart_df,
            x="Algorithm",
            y="Fulfilment",
            color="Algorithm",
            template="plotly_dark",
            color_discrete_map={"Greedy": "#84a7c3", "AI Planner": "#35a7cb"},
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(16,47,70,0.75)")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Scenario Generator":
    st.title("Scenario Generator")
    cargo_count = st.slider("Cargo items per scenario", 200, 300, 200)
    trip_count = st.slider("Available trips", 1, 8, 4)
    count = st.slider("Number of scenarios", 50, 100, 50)
    base_seed = st.number_input("Base random seed", 1, 999999, 26062)
    scale = st.slider("Capacity scale", 0.5, 2.0, 1.0)

    if st.button("Generate scenarios", type="primary"):
        generated = generate_scenarios(count, int(base_seed), cargo_count, trip_count, scale)
        combined, _ = save_scenarios(generated, PROJECT_ROOT / "data" / "scenarios")
        st.session_state.generated_scenarios = generated
        st.session_state.scenarios = generated
        st.session_state.ai_plan_scenario_id = None
        st.session_state.greedy_plan_scenario_id = None
        st.success(f"Generated {len(generated)} reproducible scenarios")
        st.download_button("Download scenarios JSON", combined.read_bytes(), "scenarios.json")

elif page == "Cargo Manifest":
    st.title("Cargo Manifest")
    scenario_choice = st.selectbox("Scenario", [s.scenario_id for s in scenarios])
    scenario = next(s for s in scenarios if s.scenario_id == scenario_choice)

    search = st.text_input("Search cargo name or ID")
    priority = st.multiselect("Priority", ["Critical", "High", "Medium", "Low"])

    rows = [{
        "cargo_id": item.cargo_id,
        "cargo_name": item.cargo_name,
        "category": item.category,
        "quantity": item.quantity,
        "unit_weight": item.unit_weight,
        "unit_volume": item.unit_volume,
        "priority": item.priority,
        "critical_flag": item.critical_flag,
    } for item in scenario.cargo_items]

    cargo_df = pd.DataFrame(rows)
    if search:
        cargo_df = cargo_df[cargo_df.astype(str).agg(" ".join, axis=1).str.contains(search, case=False)]
    if priority:
        cargo_df = cargo_df[cargo_df.priority.isin(priority)]
    st.dataframe(cargo_df, use_container_width=True, hide_index=True)

elif page in {"AI Cargo Planner", "Greedy Baseline", "Trip Details"}:
    st.title(page)
    scenario_choice = st.selectbox("Scenario", [s.scenario_id for s in scenarios], key="plan_scenario")
    scenario = next(s for s in scenarios if s.scenario_id == scenario_choice)

    if page == "AI Cargo Planner":
        beam_width = st.slider("Beam width", 4, 40, 24)
        if st.button("Run AI planner", type="primary"):
            result = allocate_ai(scenario, beam_width=beam_width)
            st.session_state.ai_plan = result.plan
            st.session_state.ai_result = result
            st.session_state.ai_plan_scenario_id = scenario.scenario_id

        if st.session_state.get("ai_plan_scenario_id") == scenario.scenario_id:
            plan = st.session_state.ai_plan
            result = st.session_state.ai_result
            metrics = calculate_metrics(scenario, plan)
            st.metric("Priority fulfilment", f"{metrics['priority_weighted_fulfilment']:.2f}%")
            st.metric("States explored", result.states_explored)

            allocation_rows = [{
                "cargo_id": a.cargo_id,
                "trip_id": a.trip_id,
                "quantity": a.quantity,
            } for a in plan.allocations]
            st.dataframe(pd.DataFrame(allocation_rows), use_container_width=True, hide_index=True)

    elif page == "Greedy Baseline":
        if st.button("Run greedy baseline", type="primary"):
            result = allocate_greedy(scenario)
            st.session_state.greedy_plan = result.plan
            st.session_state.greedy_result = result
            st.session_state.greedy_plan_scenario_id = scenario.scenario_id

        if st.session_state.get("greedy_plan_scenario_id") == scenario.scenario_id:
            plan = st.session_state.greedy_plan
            result = st.session_state.greedy_result
            metrics = calculate_metrics(scenario, plan)
            st.metric("Priority fulfilment", f"{metrics['priority_weighted_fulfilment']:.2f}%")
            st.metric("Execution time", f"{result.execution_time_seconds:.6f} s")

            allocation_rows = [{"cargo_id": a.cargo_id, "trip_id": a.trip_id, "quantity": a.quantity} for a in plan.allocations]
            st.dataframe(pd.DataFrame(allocation_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No greedy plan has been run for this scenario yet.")

    else:
        trip_choice = st.selectbox("Trip", [trip.trip_id for trip in scenario.trips])
        if st.session_state.get("ai_plan_scenario_id") != scenario.scenario_id:
            st.info("No AI plan has been run for this scenario yet.")
            if st.button("Run AI planner for this scenario", type="primary"):
                result = allocate_ai(scenario)
                st.session_state.ai_plan = result.plan
                st.session_state.ai_result = result
                st.session_state.ai_plan_scenario_id = scenario.scenario_id

        if st.session_state.get("ai_plan_scenario_id") == scenario.scenario_id:
            plan = st.session_state.ai_plan
            st.subheader("Loading sequence")
            sequence = sequence_trip_manifest(scenario, plan, trip_choice)
            if sequence:
                st.dataframe(pd.DataFrame(sequence), use_container_width=True, hide_index=True)
            else:
                st.info("This trip has no cargo allocated in the current AI plan.")

            st.subheader("All trip remaining capacity")
            st.dataframe(pd.DataFrame(remaining_trip_capacity(scenario, plan)), use_container_width=True, hide_index=True)

elif page == "Algorithm Comparison":
    st.title("Algorithm Comparison")
    if comparison.empty:
        st.warning("No comparison results found. Run src/run_comparison.py.")
    else:
        average = pd.DataFrame({
            "Metric": ["Priority fulfilment (%)", "Weight utilization (%)", "Volume utilization (%)", "Unmet critical demand"],
            "Greedy": [
                comparison.greedy_priority_weighted_fulfilment.mean(),
                comparison.greedy_weight_utilization.mean(),
                comparison.greedy_volume_utilization.mean(),
                comparison.greedy_unmet_critical_demand.mean(),
            ],
            "AI": [
                comparison.ai_priority_weighted_fulfilment.mean(),
                comparison.ai_weight_utilization.mean(),
                comparison.ai_volume_utilization.mean(),
                comparison.ai_unmet_critical_demand.mean(),
            ],
        })
        st.dataframe(average, use_container_width=True, hide_index=True)

        fig = px.bar(
            comparison.head(20),
            x="scenario_id",
            y=["greedy_priority_weighted_fulfilment", "ai_priority_weighted_fulfilment"],
            barmode="group",
            template="plotly_dark",
            color_discrete_sequence=["#84a7c3", "#35a7cb"],
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(16,47,70,0.75)")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Reports":
    st.title("Reports")
    if comparison.empty:
        st.warning("No experiment results available.")
    else:
        rows = comparison.to_dict(orient="records")
        csv_path = PROJECT_ROOT / "reports" / "comparison_report.csv"
        json_path = PROJECT_ROOT / "reports" / "comparison_report.json"
        pdf_path = PROJECT_ROOT / "reports" / "experiment_report.pdf"

        save_csv_report(rows, csv_path)
        save_json_report(rows, json_path)

        if st.button("Generate PDF report", type="primary"):
            generate_pdf_report(rows, pdf_path)
            st.success("PDF report generated")

        if pdf_path.exists():
            st.download_button("Download PDF", pdf_path.read_bytes(), "experiment_report.pdf")
        st.download_button("Download CSV", csv_path.read_bytes(), "comparison_report.csv")
        st.download_button("Download JSON", json_path.read_bytes(), "comparison_report.json")
