import streamlit as st

from src.db.postgres import SessionLocal
from src.db.models import Company, ReviewQueue
from src.entity_resolution.resolver import resolve
from src.entity_resolution.vector_search import cosine_search_candidates
from src.entity_resolution.graph_search import get_company_graph
from src.evaluation.run_eval import latest_results


session = SessionLocal()

st.set_page_config(page_title="Atlas Intelligence System", layout="wide")

st.sidebar.title("Atlas Navigation")

page = st.sidebar.radio("Go to", [
    "Company Search",
    "Review Queue",
    "Evaluation Dashboard",
    "Knowledge Graph"
])

# =========================================================
# PAGE 1 — COMPANY SEARCH (VECTOR + RESOLVER)
# =========================================================
if page == "Company Search":

    st.title("🔎 Company Search")

    query = st.text_input("Search Company")

    if query:

        st.subheader("Top Matches (Vector Search)")

        candidates = cosine_search_candidates(query)

        for c in candidates[:10]:

            company = session.get(Company, c["id"])

            if not company:
                continue

            result = resolve(
                {"name": query},
                {"name": company.name, "website": company.website}
            )

            st.write(f"### {company.name}")
            st.write(f"Score: {result['score']:.4f}")
            st.write(f"Match: {result['match']}")

            st.divider()


# =========================================================
# PAGE 2 — REVIEW QUEUE
# =========================================================
elif page == "Review Queue":

    st.title("🧑‍💻 Review Queue")
    st.caption("Pairs the LLM judge decided with low confidence")

    reviews = session.query(ReviewQueue).filter(ReviewQueue.status == "PENDING").all()
    if not reviews:
        st.info("Nothing to review.")

    for r in reviews:
        a = session.get(Company, r.company_a)
        b = session.get(Company, r.company_b)
        col1, col2, col3 = st.columns(3)
        col1.write(a.name if a else "Unknown")
        col2.write(b.name if b else "Unknown")
        col3.write(f"{r.score:.3f}")
        c1, c2 = st.columns(2)
        if c1.button(f"Approve {r.id}"):
            r.status = "APPROVED"
            session.commit()
            st.rerun()
        if c2.button(f"Reject {r.id}"):
            r.status = "REJECTED"
            session.commit()
            st.rerun()
        st.divider()


# =========================================================
# PAGE 3 — EVALUATION DASHBOARD
# =========================================================
elif page == "Evaluation Dashboard":

    st.title("📊 Evaluation Dashboard")
    results = latest_results()
    if not results:
        st.warning("No results yet. Run: python -m src.evaluation.run_ablation")
    else:
        final = results["results"]["hybrid_llm"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Precision", f"{final['precision']:.3f}")
        c2.metric("Recall", f"{final['recall']:.3f}")
        c3.metric("F1", f"{final['f1']:.3f}")
        c4.metric("LLM call rate", f"{final['llm_call_rate'] * 100:.0f}%")
        st.subheader("Ablation (held-out test split)")
        st.dataframe([{"configuration": k, **{m: v.get(m) for m in ("precision", "recall", "f1", "llm_calls")}}
                      for k, v in results["results"].items()], use_container_width=True)
        st.subheader("Blocking")
        st.json(results["blocking"])
        st.subheader("Remaining errors")
        st.dataframe(results["test_errors"], use_container_width=True)


# =========================================================
# PAGE 4 — KNOWLEDGE GRAPH
# =========================================================
elif page == "Knowledge Graph":

    st.title("🕸️ Knowledge Graph Explorer")

    query = st.text_input("Enter Company")

    if query:

        graph = get_company_graph(query)

        if not graph:
            st.warning("No company found in graph")
        else:

            st.subheader(graph["company"])

            for rel in graph["relations"]:

                st.write(
                    f"**{graph['company']}** "
                    f"→ {rel['type']} → "
                    f"**{rel['company']}** "
                    f"(confidence {rel['confidence']:.2f})"
                )