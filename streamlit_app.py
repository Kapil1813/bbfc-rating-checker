import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import urllib.parse

st.set_page_config(page_title="BBFC Rating Checker", layout="wide")

st.title("🎬 BBFC Rating Checker")
st.write("Enter up to 5 titles (comma separated)")

# --- Input ---
titles_input = st.text_input("Titles:")

def get_bbfc_rating(title):
    base_url = "https://www.bbfc.co.uk/search?q="
    encoded_title = urllib.parse.quote(title)
    search_url = base_url + encoded_title

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code != 200:
            return "Error", search_url

        soup = BeautifulSoup(response.text, "lxml")

        # Attempt to find rating label in search result cards
        rating_tag = soup.find("span", class_="age-rating")

        if rating_tag:
            return rating_tag.text.strip(), search_url
        else:
            return "Not Found", search_url

    except Exception:
        return "Error", search_url


# --- Button ---
if st.button("Check Ratings"):

    if not titles_input:
        st.warning("Please enter at least one title.")
    else:
        titles = [t.strip() for t in titles_input.split(",") if t.strip()]
        
        if len(titles) > 5:
            st.error("Maximum 5 titles allowed.")
        else:
            results = []

            for title in titles:
                rating, url = get_bbfc_rating(title)
                results.append({
                    "Title": title,
                    "Rated?": "Yes" if rating not in ["Not Found", "Error"] else "No",
                    "BBFC Rating": rating,
                    "Search URL": url
                })

            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)