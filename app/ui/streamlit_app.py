import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="SEC Filing RAG", layout="wide")
st.title("📊 SEC Filing RAG Platform")

tab1, tab2, tab3, tab4 = st.tabs([
    "Ingest Filing",
    "Ask Question",
    "Extract Fields",
    "Compare Filings"
])

# ----------------------------
# TAB 1: INGEST
# ----------------------------
with tab1:
    st.subheader("Ingest SEC Filing")

    filing_url = st.text_input(
        "Filing URL",
        value="https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm"
    )
    output_filename = st.text_input(
        "Output Filename",
        value="aapl_10k_test.html"
    )

    if st.button("Ingest Filing"):
        payload = {
            "filing_url": filing_url,
            "output_filename": output_filename
        }

        try:
            response = requests.post(f"{API_BASE}/filings/ingest", json=payload)
            data = response.json()

            if response.status_code == 200:
                st.success("Filing ingested successfully!")
                st.json(data)
            else:
                st.error(f"Error: {data}")
        except Exception as e:
            st.error(str(e))

# ----------------------------
# TAB 2: QUERY
# ----------------------------
with tab2:
    st.subheader("Ask Questions About a Filing")

    query_filing_id = st.text_input(
        "Filing ID",
        value="AAPL_10-K_000032019325000079",
        key="query_filing_id"
    )
    question = st.text_area(
        "Question",
        value="What are the main risk factors related to competition and supply chain?"
    )
    top_k_query = st.slider("Top K Chunks", min_value=3, max_value=8, value=5, key="top_k_query")

    if st.button("Run Query"):
        payload = {
            "question": question,
            "filing_id": query_filing_id,
            "top_k": top_k_query
        }

        try:
            response = requests.post(f"{API_BASE}/query", json=payload)
            data = response.json()

            if response.status_code == 200:
                st.success("Query completed")

                st.markdown("### Answer")
                st.write(data.get("answer", ""))

                st.markdown("### Citations")
                st.json(data.get("citations", []))

                st.markdown("### Evidence")
                for idx, ev in enumerate(data.get("evidence", []), start=1):
                    with st.expander(
                        f"{idx}. {ev.get('section_title')} | chunk {ev.get('chunk_index')} | rerank {ev.get('rerank_score'):.4f}"
                    ):
                        st.write(ev.get("chunk_text", ""))
            else:
                st.error(f"Error: {data}")
        except Exception as e:
            st.error(str(e))

# ----------------------------
# TAB 3: EXTRACT
# ----------------------------
with tab3:
    st.subheader("Structured Field Extraction")

    extract_filing_id = st.text_input(
        "Filing ID",
        value="AAPL_10-K_000032019325000079",
        key="extract_filing_id"
    )

    available_fields = [
        "material_risk_factors_summary",
        "legal_proceedings_summary",
        "business_segments",
        "share_repurchase_mention",
        "total_revenue_mention",
        "net_income_mention"
    ]

    selected_fields = st.multiselect(
        "Select fields to extract",
        available_fields,
        default=[
            "material_risk_factors_summary",
            "share_repurchase_mention"
        ]
    )

    if st.button("Run Extraction"):
        payload = {
            "filing_id": extract_filing_id,
            "fields": selected_fields
        }

        try:
            response = requests.post(f"{API_BASE}/extract", json=payload)
            data = response.json()

            if response.status_code == 200:
                st.success("Extraction completed")

                for result in data.get("results", []):
                    st.markdown(f"## {result.get('field')}")
                    st.write(f"**Status:** {result.get('status')}")
                    st.write(f"**Value:** {result.get('value')}")
                    st.write(f"**Reasoning:** {result.get('reasoning')}")

                    with st.expander("Citations"):
                        st.json(result.get("citations", []))

                    with st.expander("Evidence"):
                        for idx, ev in enumerate(result.get("evidence", []), start=1):
                            st.markdown(
                                f"**{idx}. {ev.get('section_title')} | chunk {ev.get('chunk_index')} | rerank {ev.get('rerank_score'):.4f}**"
                            )
                            st.write(ev.get("chunk_text", ""))
                            st.divider()
            else:
                st.error(f"Error: {data}")
        except Exception as e:
            st.error(str(e))

# ----------------------------
# TAB 4: COMPARE
# ----------------------------
with tab4:
    st.subheader("Compare Two Filings")

    base_filing_id = st.text_input(
        "Base Filing ID",
        value="AAPL_10-K_000032019324000123",
        key="base_filing_id"
    )
    compare_filing_id = st.text_input(
        "Compare Filing ID",
        value="AAPL_10-K_000032019325000079",
        key="compare_filing_id"
    )

    focus = st.selectbox(
        "Comparison Focus",
        ["risk_factors", "legal_proceedings", "capital_return", "business_segments", "financial_performance"]
    )

    top_k_compare = st.slider("Top K Chunks Per Filing", min_value=2, max_value=6, value=4, key="top_k_compare")

    if st.button("Run Comparison"):
        payload = {
            "base_filing_id": base_filing_id,
            "compare_filing_id": compare_filing_id,
            "focus": focus,
            "top_k": top_k_compare
        }

        try:
            response = requests.post(f"{API_BASE}/compare", json=payload)
            data = response.json()

            if response.status_code == 200:
                st.success("Comparison completed")

                comparison = data.get("comparison", {})

                st.markdown("### Summary")
                st.write(comparison.get("summary", ""))

                st.markdown("### New or More Emphasized in Compare Filing")
                for item in comparison.get("new_or_more_emphasized_in_compare", []):
                    st.write(f"- {item}")

                st.markdown("### Materially Similar Points")
                for item in comparison.get("materially_similar_points", []):
                    st.write(f"- {item}")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Base Citations")
                    st.json(data.get("base_citations", []))

                with col2:
                    st.markdown("### Compare Citations")
                    st.json(data.get("compare_citations", []))

                with st.expander("Base Evidence"):
                    for idx, ev in enumerate(data.get("base_evidence", []), start=1):
                        st.markdown(
                            f"**{idx}. {ev.get('section_title')} | chunk {ev.get('chunk_index')} | rerank {ev.get('rerank_score'):.4f}**"
                        )
                        st.write(ev.get("chunk_text", ""))
                        st.divider()

                with st.expander("Compare Evidence"):
                    for idx, ev in enumerate(data.get("compare_evidence", []), start=1):
                        st.markdown(
                            f"**{idx}. {ev.get('section_title')} | chunk {ev.get('chunk_index')} | rerank {ev.get('rerank_score'):.4f}**"
                        )
                        st.write(ev.get("chunk_text", ""))
                        st.divider()
            else:
                st.error(f"Error: {data}")
        except Exception as e:
            st.error(str(e))