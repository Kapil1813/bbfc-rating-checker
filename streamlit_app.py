import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urljoin

BASE_URL = "https://www.bbfc.co.uk"
SEARCH_URL = "https://www.bbfc.co.uk/search"

def search_bbfc(title):
    params = {
        "q": title,
        "t[]": ["All", "Film", "TV Show"],
    }

    response = requests.get(SEARCH_URL, params=params, timeout=15)
    if response.status_code != 200:
        return {"error": "BBFC site not reachable"}

    soup = BeautifulSoup(response.text, "lxml")

    # Find first search result link
    result = soup.select_one("a[href^='/release/']")
    if not result:
        return {"found": False}

    release_url = urljoin(BASE_URL, result["href"])

    # Open release page
    release_page = requests.get(release_url, timeout=15)
    release_soup = BeautifulSoup(release_page.text, "lxml")

    # Try to extract rating
    rating_tag = release_soup.find("span", string=True)
    rating = None

    # Look for common BBFC rating labels
    possible_ratings = ["U", "PG", "12", "12A", "15", "18", "R18"]
    for r in possible_ratings:
        if release_soup.find(string=r):
            rating = r
            break

    if rating:
        return {
            "found": True,
            "rating": rating,
            "url": release_url
        }
    else:
        return {
            "found": True,
            "rating": "Not clearly identified",
            "url": release_url
        }


# --- Streamlit UI ---

st.set_page_config(page_title="BBFC Rating Checker", layout="centered")

st.title("🎬 BBFC Rating Lookup Tool")
st.caption("Check if a film/TV title exists in BBFC and retrieve its classification")

title_input = st.text_input("Enter Film / TV Title")

if st.button("Check Rating") and title_input:
    with st.spinner("Searching BBFC..."):
        result = search_bbfc(title_input)

    if result.get("error"):
        st.error(result["error"])

    elif not result.get("found"):
        st.warning("❌ Title not found on BBFC")

    else:
        st.success("✅ Title Found")
        st.write(f"**Rating:** {result['rating']}")
        st.write(f"**BBFC URL:** {result['url']}")