import streamlit as st
from playwright.sync_api import sync_playwright
import pandas as pd
import io
from urllib.parse import urljoin

BASE_URL = "https://www.bbfc.co.uk"

# ----------------------------
# Function to search BBFC
# ----------------------------
def search_bbfc(title, director=None, year=None):
    """
    Search BBFC for a title, optionally filtering by director and production year.
    Returns a list of matching releases.
    """
    results_list = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        search_url = f"{BASE_URL}/search?q={title}"
        page.goto(search_url)
        page.wait_for_timeout(3000)  # wait for JS rendering

        # get all release links
        results = page.query_selector_all("a[href*='/release/']")
        if not results:
            browser.close()
            return []

        for r in results:
            release_url = urljoin(BASE_URL, r.get_attribute("href"))
            page.goto(release_url)
            page.wait_for_timeout(2000)

            # Extract rating
            rating = None
            for el in page.query_selector_all("span"):
                text = el.inner_text().strip()
                if text in ["U", "PG", "12", "12A", "15", "18", "R18"]:
                    rating = text
                    break

            # Extract Director / Production Year
            director_text = None
            year_text = None
            info_items = page.query_selector_all("li, dd")
            for item in info_items:
                text = item.inner_text().strip()
                if "Director" in text:
                    director_text = text.replace("Director", "").strip()
                if "Production year" in text or "Release year" in text:
                    year_text = ''.join(filter(str.isdigit, text))

            # Apply optional filters
            if director and director_text:
                if director.lower() not in director_text.lower():
                    continue
            if year and year_text:
                if str(year) != year_text:
                    continue

            # Add to results
            results_list.append({
                "Title": title,
                "Rating": rating if rating else "Rating not detected",
                "URL": release_url,
                "Director": director_text,
                "Year": year_text
            })

        browser.close()
    return results_list

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="BBFC Compliance Lookup", layout="wide")
st.title("🎬 BBFC Compliance Lookup Tool")
st.markdown(
    "Upload an Excel file with a list of titles (and optional Director/Year) "
    "to retrieve BBFC ratings, URLs, and metadata."
)

# ----------------------------
# Excel File Upload
# ----------------------------
uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type="xlsx")

if uploaded_file:
    try:
        df_input = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        st.stop()

    required_column = "Title"
    if required_column not in df_input.columns:
        st.error(f"Excel file must contain a column named '{required_column}'")
        st.stop()

    # Optional columns
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
                # If no match found
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

    # ----------------------------
    # Excel Download
    # ----------------------------
    output = io.BytesIO()
    df_output.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label="Download Results as Excel",
        data=output,
        file_name="bbfc_lookup_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )