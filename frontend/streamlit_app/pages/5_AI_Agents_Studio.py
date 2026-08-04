from __future__ import annotations

import streamlit as st

from utils.api_client import ApiError, api_get, api_post

st.set_page_config(page_title="AI Agents Studio - RetailIQ", page_icon="🤖", layout="wide")

st.title("🤖 AI Agents Studio (CrewAI Multi-Agent SDLC)")
st.caption(
    "Runs Business Analyst, Architect, Developer, Tester, and Documentation agents against a "
    "project brief. Real LLM-backed generation requires OPENAI_API_KEY; otherwise clearly-labeled "
    "template output is returned so the studio is always usable."
)

try:
    roster = api_get("/api/v1/agents/roster")
except ApiError as exc:
    st.error(f"Could not load agent roster: {exc.detail}")
    roster = []

if roster:
    with st.expander("👥 Agent roster", expanded=False):
        for agent in roster:
            st.markdown(f"**{agent['name']}** — {agent['role']}\n\n_{agent['goal']}_")

project_brief = st.text_area(
    "Project brief",
    height=150,
    placeholder="e.g. Add a 'buy online, pick up in store' (BOPIS) feature for the retail platform...",
)
target_agent = st.selectbox(
    "Run", ["all", "business_analyst", "architect", "developer", "tester", "documentation"]
)

if st.button("Run agents", disabled=len(project_brief.strip()) < 10):
    with st.spinner("Running agent pipeline..."):
        try:
            response = api_post(
                "/api/v1/agents/run", {"project_brief": project_brief, "target_agent": target_agent}
            )
            st.success(f"Completed in {response['total_execution_time_seconds']}s")

            for result in response["results"]:
                with st.expander(f"📄 {result['agent_name']} — {result['execution_time_seconds']}s", expanded=True):
                    st.markdown(result["output"])
                    metrics = result["quality_metrics"]
                    cols = st.columns(5)
                    cols[0].metric("Confidence", metrics["confidence_score"])
                    cols[1].metric("Hallucination Risk", metrics["hallucination_risk"])
                    cols[2].metric("Req. Coverage", metrics["requirement_coverage"])
                    cols[3].metric("Context Relevance", metrics["context_relevance"])
                    cols[4].metric("Completeness", metrics["completeness"])
                    st.caption(metrics["explanation"])
        except ApiError as exc:
            st.error(f"Agent run failed: {exc.detail}")

st.divider()
st.subheader("📝 Feedback")
st.caption("Rate the generated artifacts to help improve future generations.")

with st.form("feedback_form"):
    artifact_type = st.selectbox(
        "Artifact type", ["business_analyst", "architect", "developer", "tester", "documentation"]
    )
    rating = st.slider("Rating", 1, 5, 4)
    comments = st.text_area("Comments", height=80)
    improvements = st.text_area("Suggested improvements", height=80)
    submitted = st.form_submit_button("Submit feedback")

if submitted:
    try:
        from utils.api_client import api_post as _post

        _post(
            "/api/v1/feedback",
            {
                "artifact_type": artifact_type, "rating": rating,
                "comments": comments or None, "improvements": improvements or None,
            },
        )
        st.success("Thanks! Feedback recorded.")
    except ApiError as exc:
        st.error(f"Failed to submit feedback: {exc.detail}")
