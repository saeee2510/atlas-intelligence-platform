import streamlit as st

from src.db.postgres import SessionLocal
from src.db.models import Company, CompanyMapping, CanonicalCompany
from src.entity_resolution.resolver import resolve
from src.entity_resolution.review_queue import add_to_review_queue
from src.evaluation.run_eval import run_eval


session = SessionLocal()

st.set_page_config(page_title="Atlas Intelligence System", layout="wide")

st.sidebar.title("Atlas Dashboard")
page = st.sidebar.radio("Navigate", [
    "Company Search",
    "Review Queue",
    "Evaluation Dashboard"
])

# =========================
# PAGE 1: COMPANY SEARCH
# =========================
if page == "Company Search":

    st.title("🔎 Company Search")

    query = st.text_input("Search Company")

    if query:

        companies = session.query(Company).all()

        results = []

        for c in companies:
            result = resolve(
                {"name": query},
                {"name": c.name, "website": c.website}
            )

            results.append((c, result))

        results.sort(key=lambda x: x[1]["score"], reverse=True)

        st.subheader("Top Matches")

        for c, r in results[:5]:

            st.write(f"**{c.name}**")
            st.write(f"Score: {r['score']:.3f}")
            st.write(f"Match: {r['match']}")
            st.divider()


# =========================
# PAGE 2: REVIEW QUEUE
# =========================
elif page == "Review Queue":

    st.title("🧑‍💻 Review Queue")

    reviews = session.query(CompanyMapping).all()

    for r in reviews:

        col1, col2, col3 = st.columns(3)

        a = session.query(Company).get(r.company_id)
        b = session.query(CanonicalCompany).get(r.canonical_company_id)

        with col1:
            st.write(a.name)

        with col2:
            st.write(b.canonical_name)

        with col3:
            st.write(f"Score: {r.match_score:.3f}")

        c1, c2 = st.columns(2)

        with c1:
            if st.button(f"Approve {r.id}"):
                r.status = "APPROVED"
                session.commit()

        with c2:
            if st.button(f"Reject {r.id}"):
                r.status = "REJECTED"
                session.commit()

        st.divider()


# =========================
# PAGE 3: EVALUATION DASHBOARD
# =========================
elif page == "Evaluation Dashboard":

    st.title("📊 Evaluation Dashboard")

    metrics = run_eval()

    st.metric("Precision", f"{metrics['precision']:.2f}")
    st.metric("Recall", f"{metrics['recall']:.2f}")
    st.metric("F1 Score", f"{metrics['f1']:.2f}")
    st.metric("Accuracy", f"{metrics['accuracy']:.2f}")

    st.success("System evaluation completed successfully")