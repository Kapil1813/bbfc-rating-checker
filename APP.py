import streamlit as st
import pandas as pd
import io
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.bbfc.co.uk"

# ----------------------------
# Function to search BBFC
# ----------------------------
def search_bbfc(title, director=None, year=None):
    results_list = []

    # Search BBFC
    search_url = f"{BASE_URL}/search?q={title}"
    r = requests.get(search_url)
    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    links = soup.select("a[href*='/release/']")

    if not links:
        return []

    for a in links:
        release_url = BASE_URL + a["href"]
        page = requests.get(release_url)
        if page.status_code != 200:
            continue
        psoup = BeautifulSoup(page.text, "html.parser")

        # Extract rating
        rating = None
        for span in psoup.find_all("span"):
            text = span.text.strip()
            if text in ["U","PG","12","12A","15","18","R18"]:
                rating = text
                break

        # Extract Director / Year
        director_text = None
        year_text = None
        for li in psoup.find_all(["li", "dd"]):
            t = li.text.strip()
            if "Director" in t:
                director_text = t.replace("Director", "").strip()
            if "Production year" in t or "Release year" in t:
                year_text = ''.join(filter(str.isdigit, t))

        # Apply filters
        if director and director_text:
            if director.lower() not in director_text.lower():
                continue
        if year and year_text:
            if str(year) != year_text:
                continue

        results_list.append({
            "Title": title,
            "Rating": rating if rating else "Rating not detected",
            "URL": release_url,
            "Director": director_text,
            "Year": year_text
        })

    return results_list

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="BBFC Compliance Lookup", layout="wide")
st.title("🎬 BBFC Compliance Lookup Tool")
st.markdown(
    "Upload an Excel file with `Title` column (and optional `Director` / `Year`) "
    "to retrieve BBFC ratings, URLs, and metadata."
)

# Excel Upload
uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type="xlsx")
if uploaded_file:
    try:
        df_input = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        st.stop()

    if "Title" not in df_input.columns:
        st.error("Excel must contain a 'Title' column")
        st.stop()

    has_director = "Director" in df_input.columns
    has_year = "Year" in df_input.columns

    output_rows = []

    with st.spinner("Searching BBFC for all titles..."):
        for _, row in df_input.iterrows():
            title = row.get("Title")
            director = row.get("Director") if has_director else None
            year = row.get("Year") if has_year else None

            matches = search_bbfc(title, director, year)
            if matches:
                output_rows.extend(matches)
            else:
                output_rows.append({
                    "Title": title,
                    "Rating": "Not Found",
                    "URL": "",
                    "Director": director,
                    "Year": year
                })

    df_output = pd.DataFrame(output_rows)
    st.success(f"✅ Completed BBFC lookup for {len(df_input)} titles")
    st.dataframe(df_output)

    # Excel download
    output = io.BytesIO()
    df_output.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    st.download_button(
        label="Download Results as Excel",
        data=output,
        file_name="bbfc_lookup_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )