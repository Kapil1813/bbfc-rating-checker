import streamlit as st
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.bbfc.co.uk"

def search_bbfc(title, director=None, year=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        search_url = f"{BASE_URL}/search?q={title}"
        page.goto(search_url)
        page.wait_for_timeout(3000)

        # Get all search results
        results = page.query_selector_all("a[href*='/release/']")

        if not results:
            browser.close()
            return {"found": False}

        # Loop through results to find correct match
        matched_result = None
        for r in results:
            release_url = BASE_URL + r.get_attribute("href")
            page.goto(release_url)
            page.wait_for_timeout(2000)

            # Extract rating
            rating = None
            rating_elements = page.query_selector_all("span")
            for el in rating_elements:
                text = el.inner_text().strip()
                if text in ["U", "PG", "12", "12A", "15", "18", "R18"]:
                    rating = text
                    break

            # Optional: Extract Director / Production Year from page
            director_text = None
            year_text = None

            # BBFC page may have <dd> or <li> with info — adjust selectors as needed
            info_items = page.query_selector_all("li, dd")
            for item in info_items:
                text = item.inner_text().strip()
                if "Director" in text:
                    director_text = text.replace("Director", "").strip()
                if "Production year" in text or "Release year" in text:
                    year_text = ''.join(filter(str.isdigit, text))

            # Check filters
            if director and director_text:
                if director.lower() not in director_text.lower():
                    continue  # skip non-matching director
            if year and year_text:
                if str(year) != year_text:
                    continue  # skip non-matching year

            # If filters pass (or not provided), pick this result
            matched_result = {
                "found": True,
                "rating": rating if rating else "Rating not detected",
                "url": release_url,
                "director": director_text,
                "year": year_text
            }
            break  # stop at first matched filtered result

        browser.close()
        if matched_result:
            return matched_result
        else:
            return {"found": False}

# --- Streamlit UI ---
st.title("🎬 BBFC Rating Lookup with Filters")
title_input = st.text_input("Enter Film / TV Title")
director_input = st.text_input("Director (optional)")
year_input = st.text_input("Production Year (optional)")

if st.button("Check Rating") and title_input:
    with st.spinner("Searching BBFC..."):
        result = search_bbfc(title_input, director_input, year_input)

    if not result["found"]:
        st.error("❌ Title not found with the given filters")
    else:
        st.success("✅ Title Found")
        st.write(f"**Rating:** {result['rating']}")
        st.write(f"**URL:** {result['url']}")
        if result.get("director"):
            st.write(f"**Director:** {result['director']}")
        if result.get("year"):
            st.write(f"**Production Year:** {result['year']}")