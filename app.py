import streamlit as st

from src.db.postgres import SessionLocal
from src.db.models import Company, CanonicalCompany, CompanyMapping
from src.entity_resolution.resolver import resolve
from src.entity_resolution.vector_search import cosine_search_candidates
from src.entity_resolution.graph_search import get_company_graph
from src.evaluation.run_eval import run_eval


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

            company = session.query(Company).get(c["id"])

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

    reviews = session.query(CompanyMapping).all()

    for r in reviews:

        a = session.query(Company).get(r.company_id)
        b = session.query(CanonicalCompany).get(r.canonical_company_id)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(a.name if a else "Unknown")

        with col2:
            st.write(b.canonical_name if b else "Unknown")

        with col3:
            st.write(f"{r.match_score:.3f}")

        c1, c2 = st.columns(2)

        with c1:
            if st.button(f"Approve {r.id}"):
                r.status = "APPROVED"
                session.commit()
                st.rerun()

        with c2:
            if st.button(f"Reject {r.id}"):
                r.status = "REJECTED"
                session.commit()
                st.rerun()

        st.divider()


# =========================================================
# PAGE 3 — EVALUATION DASHBOARD
# =========================================================
elif page == "Evaluation Dashboard":

    st.title("📊 Evaluation Dashboard")

    metrics = run_eval()

    st.metric("Precision", f"{metrics['precision']:.2f}")
    st.metric("Recall", f"{metrics['recall']:.2f}")
    st.metric("F1 Score", f"{metrics['f1']:.2f}")
    st.metric("Accuracy", f"{metrics['accuracy']:.2f}")

    st.success("Evaluation complete")


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