import streamlit as st

from nawaloka.agents.orchestrator import run_pipeline
from nawaloka.dashboard.charts import build_figure
from nawaloka.dashboard.panels import PANELS
from nawaloka.dashboard.service import get_date_bounds, load_panel
from nawaloka.log import setup_logging

setup_logging()
st.set_page_config(page_title="Nawaloka Analytics", layout="wide")


@st.cache_data(show_spinner=False)
def cached_bounds():
    return get_date_bounds()


@st.cache_data(show_spinner=False)
def cached_panel(key: str, start, end, with_insight: bool):
    panel = next(p for p in PANELS if p.key == key)
    return load_panel(panel, start, end, with_insight)


def render_dashboard() -> None:
    first, last = cached_bounds()
    start, end = st.sidebar.date_input("Date range", value=(first, last), min_value=first, max_value=last)
    with_insight = st.sidebar.checkbox("Generate insights", value=True)
    columns = st.columns(2)
    for index, panel in enumerate(PANELS):
        with columns[index % 2]:
            with st.spinner(f"Loading {panel.title}"):
                result = cached_panel(panel.key, start, end, with_insight)
            st.subheader(panel.title)
            if result.error:
                st.warning(result.error)
                continue
            if result.rows:
                st.plotly_chart(build_figure(panel.chart, result.rows), use_container_width=True)
            if result.insight:
                st.caption(result.insight)


def render_ask() -> None:
    history = st.session_state.setdefault("history", [])
    with st.form("ask_form", clear_on_submit=True):
        question = st.text_input("Ask a question about hospital data")
        submitted = st.form_submit_button("Ask")
    if submitted and question.strip():
        with st.spinner("Thinking"):
            history.insert(0, run_pipeline(question.strip()))
    for result in history:
        st.markdown(f"**{result.question}**")
        st.write(result.answer)
        chart = result.interpretation.chart if result.interpretation else None
        if chart and result.rows:
            st.plotly_chart(build_figure(chart, result.rows), use_container_width=True)
        if result.rows:
            st.dataframe(result.rows, use_container_width=True)
        if result.sql:
            with st.expander("SQL"):
                st.code(result.sql, language="sql")
        with st.expander(f"Agent steps ({result.duration_ms:.0f} ms)"):
            st.table(
                [
                    {
                        "agent": s.agent,
                        "status": s.status,
                        "ms": s.duration_ms,
                        "tokens in": s.input_tokens,
                        "tokens out": s.output_tokens,
                    }
                    for s in result.steps
                ]
            )
        st.divider()


st.title("Nawaloka Hospital Analytics")
dashboard_tab, ask_tab = st.tabs(["Dashboard", "Ask"])
with dashboard_tab:
    render_dashboard()
with ask_tab:
    render_ask()
