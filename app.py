from __future__ import annotations

from urllib.parse import urlparse
import pandas as pd
import streamlit as st
from fpdf import FPDF
from datetime import datetime

from seo_core import SEOTool
from utils import calculate_seo_score, generate_recommendations, get_score_color


def is_valid_url(url: str) -> bool:
    cleaned = url.strip()
    if not cleaned:
        return False
    if not cleaned.startswith(("http://", "https://")):
        cleaned = f"https://{cleaned}"
    parsed = urlparse(cleaned)
    return bool(parsed.netloc and "." in parsed.netloc)


def create_pdf(report_text: str) -> str:
    """Create a PDF from the report text"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add title
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, txt="SEO Analysis Report", ln=True, align='C')
    pdf.ln(10)
    
    # Add date
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
    pdf.ln(10)
    
    # Add report content
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=report_text)
    
    # Save PDF
    filename = f"seo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename


st.set_page_config(
    page_title="RankPilot - SEO Intelligence Tool",
    page_icon="🚀",
    layout="wide",
)

st.title("🚀 Rank__Pilot")
st.caption("AI-powered SEO audit tool")

st.markdown("---")

# -------- INPUT -------- #
url_input = st.text_input("🌐 Your Website URL")
competitor_input = st.text_input("⚔️ Competitor URL (Optional)")

analyze_clicked = st.button("Analyze Website", use_container_width=True, type="primary")

competitor_analysis = None
your_score = 0
your_analysis = None
competitor_score = None

if analyze_clicked:
    if not is_valid_url(url_input):
        st.error("Please enter a valid URL")
    else:
        with st.spinner("Analyzing..."):
            your_tool = SEOTool(url_input)
            your_analysis = your_tool.run_full_analysis()
            your_score = calculate_seo_score(your_analysis)

            if competitor_input and is_valid_url(competitor_input):
                comp_tool = SEOTool(competitor_input)
                competitor_analysis = comp_tool.run_full_analysis()
                competitor_score = calculate_seo_score(competitor_analysis)

# ---------------- TRAFFIC ESTIMATION ---------------- #
def estimate_traffic(score, keywords):
    base = score * 10
    keyword_factor = len(keywords) * 20
    return base + keyword_factor


# Only proceed if we have analysis results
if your_analysis:
    # -------- SCORES -------- #
    st.subheader("📊 SEO Score")

    if competitor_analysis:
        col1, col2 = st.columns(2)
        col1.metric("Your Score", your_score)
        col2.metric("Competitor Score", competitor_score)
    else:
        st.metric("Your Score", your_score)

    st.markdown("---")

    # -------- KEYWORD CHART -------- #
    st.subheader("🔎 Keyword Analysis")
    
    try:
        import altair as alt
        
        keyword_df = pd.DataFrame(your_analysis["keyword_density"]["top_keywords"])
        
        if not keyword_df.empty:
            keyword_df = keyword_df.rename(columns={"keyword": "Keyword", "frequency": "Frequency"})
            
            # Sort descending by frequency
            keyword_df = keyword_df.sort_values(by="Frequency", ascending=False)
            
            # Create Altair chart with explicit ordering to keep the sort
            chart = alt.Chart(keyword_df).mark_bar().encode(
                x=alt.X('Keyword', sort=keyword_df['Keyword'].tolist(), title='Keywords'),
                y=alt.Y('Frequency', title='Frequency'),
                color=alt.value('#1f77b4')
            ).properties(
                width=600,
                height=400
            )
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No keyword data available")
    except ImportError:
        # Fallback to regular bar_chart if altair not installed
        try:
            keyword_df = pd.DataFrame(your_analysis["keyword_density"]["top_keywords"])
            if not keyword_df.empty:
                keyword_df = keyword_df.rename(columns={"keyword": "Keyword", "frequency": "Frequency"})
                keyword_df = keyword_df.sort_values(by="Frequency", ascending=False)
                st.bar_chart(keyword_df.set_index("Keyword"))
            else:
                st.info("No keyword data available")
        except Exception as e:
            st.info("No keyword data available")
    except Exception as e:
        st.info("No keyword data available")

    st.markdown("---")

    # -------- KEYWORD GAP ANALYSIS -------- #
    if competitor_analysis and your_analysis:
        st.subheader("🚀 Keyword Gap Analysis")

        your_keywords = {
            kw["keyword"] for kw in your_analysis["keyword_density"]["top_keywords"]
        }

        competitor_keywords = {
            kw["keyword"] for kw in competitor_analysis["keyword_density"]["top_keywords"]
        }

        gap_keywords = competitor_keywords - your_keywords

        if gap_keywords:
            st.warning("Keywords your competitor ranks for but you don't:")

            gap_df = pd.DataFrame({"Missing Keywords": list(gap_keywords)})
            st.dataframe(gap_df, use_container_width=True, hide_index=True)

            st.info("👉 Opportunity: Target these keywords to improve your rankings.")
        else:
            st.success("No major keyword gaps found.")

        st.markdown("---")

    # -------- INSIGHTS -------- #
    st.subheader("🧠 Insights")

    if competitor_analysis:
        if competitor_score > your_score:
            st.warning("Competitor is performing better → improve your SEO strategy")
        else:
            st.success("You are performing better than competitor")
    else:
        st.info("Add competitor URL for deeper insights")

    st.markdown("---")

    # -------- RECOMMENDATIONS -------- #
    st.subheader("💡 Recommendations")
    recommendations = generate_recommendations(your_analysis)

    for rec in recommendations:
        st.warning(rec)

    # -------- FINAL SUGGESTION -------- #
    st.subheader("🚀 Growth Suggestion")

    if your_score < 70:
        st.error("Your SEO needs strong improvement. Focus on structure and metadata.")
    elif your_score < 90:
        st.warning("Good performance. Optimize further for better rankings.")
    else:
        st.success("Excellent SEO performance. Maintain consistency!")
    
    st.markdown("---")
    
    # -------- TRAFFIC ESTIMATION -------- #
    st.subheader("📈 Traffic Estimation")
    traffic = estimate_traffic(
        your_score,
        your_analysis["keyword_density"]["top_keywords"]
    )
    st.metric("Estimated Monthly Traffic", f"{traffic}")

else:
    # Show initial state when no analysis has been run
    st.info("👈 Enter a URL and click 'Analyze Website' to get started!")
