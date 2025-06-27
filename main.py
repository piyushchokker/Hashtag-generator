import streamlit as st
from google import genai
from pytrends.request import TrendReq
import pandas as pd
import time
import random
import plotly.express as px
from st_copy_to_clipboard import st_copy_to_clipboard

# Set the title of the app
st.title("🔥 Hashtag Generator & Trend Visualizer")

# --- HASHTAG GENERATOR ---

st.header("🧠 Generate Hashtags")
user_input = st.text_area("Enter keywords to generate hashtags")

platform = st.selectbox(
    "Select a social media platform:",
    ("Instagram", "Snapchat", "Twitter", "Facebook", "YouTube")
)

# AI function to generate hashtags
def ai(keywords, platform_name):
    client = genai.Client(api_key="AIzaSyCOdyxSti9FVpxhyaiQihtW06h_ikoKqDU")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"with this keyword -- {keywords} -- make some good hashtags for {platform_name}. just tell 5 hashtags. no extra text."
    )
    return response.text.strip()

# Generate button
if st.button("Generate Hashtags"):
    if user_input:
        hashtags_raw = ai(user_input, platform)
        hashtags = [f"#{tag.strip()}" for tag in hashtags_raw.split("#") if tag.strip()]

        st.subheader("Click any hashtag to copy it:")

        cols = st.columns(len(hashtags))  # One column per button
        for i, tag in enumerate(hashtags):
            with cols[i]:
                st_copy_to_clipboard(tag, f"{tag}", key=f"copy_button_{i}")
    else:
        st.warning("Please enter a keyword to generate hashtags.")

# --- TREND GRAPH SECTION ---

st.header("📈 Hashtag Trend Analysis")

pytrends = TrendReq(hl='en-US', tz=330)
trend_input = st.text_area("Enter keywords or hashtags (comma-separated)")

DELAY = 10
BATCH_SIZE = 3

if st.button("Generate Trend Graphs"):
    keywords = [kw.strip().replace("#", "") for kw in trend_input.split(",") if kw.strip()]

    if not keywords:
        st.warning("Please enter at least one valid keyword.")
    else:
        trend_data = pd.DataFrame()

        for i in range(0, len(keywords), BATCH_SIZE):
            batch = keywords[i:i + BATCH_SIZE]
            pytrends.build_payload(batch, timeframe='now 7-d')

            try:
                df = pytrends.interest_over_time()
                if df.empty:
                    st.warning(f"No trend data for: {batch}")
                else:
                    if 'isPartial' in df.columns:
                        df = df.drop(columns=['isPartial'])

                    trend_data = pd.concat([trend_data, df], axis=1)
                    st.subheader(f"📊 Line Chart for: {', '.join(batch)}")
                    st.line_chart(df)

                time.sleep(DELAY)

            except Exception as e:
                st.error(f"Error fetching data for {batch}: {str(e)}")
                break

        if trend_data.empty:
            st.warning("No trend data found.")
        else:
            total_interest = trend_data.sum()

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🧁 Pie Chart: Popularity Share by Age Group")

                # Simulate Age Group data for pie chart (You can replace this with real data)
                age_groups = ['13-18', '19-25', '26-35', '36-50', '50+']
                simulated_values = [random.randint(5, 30) for _ in range(5)]  # Random data for demo

                pie_age = px.pie(
                    names=age_groups,
                    values=simulated_values,
                    title="Hashtag Popularity by Age Group"
                )
                st.plotly_chart(pie_age, use_container_width=True)

            with col2:
                st.subheader("📦 Bar Chart: Total Search Volume")
                bar_chart = px.bar(
                    x=total_interest.index,
                    y=total_interest.values,
                    labels={"x": "Keyword", "y": "Total Interest"},
                    title="Total Search Volume"
                )
                st.plotly_chart(bar_chart, use_container_width=True)

            # --- ADDITIONAL GRAPHS ---

            st.subheader("📊 Additional Trend Visualizations")

            # Histogram: Distribution of Trend Data
            st.subheader("📈 Trend Distribution (Histogram)")
            trend_data_melted = trend_data.melt(var_name='Hashtag', value_name='Interest')

            fig_hist = px.histogram(trend_data_melted, x='Interest', color='Hashtag', barmode='overlay', 
                                     title="Trend Distribution of Hashtags")
            st.plotly_chart(fig_hist, use_container_width=True)

            # Scatter Plot: Compare Two Hashtags
            st.subheader("🔴 Scatter Plot: Compare Interest Between Two Hashtags")

            if len(keywords) >= 2:
                fig_scatter = px.scatter(trend_data, x=keywords[0], y=keywords[1], 
                                         labels={keywords[0]: f"Interest in {keywords[0]}", 
                                                 keywords[1]: f"Interest in {keywords[1]}"}, 
                                         title=f"Comparison Between {keywords[0]} and {keywords[1]}")
                st.plotly_chart(fig_scatter, use_container_width=True)

            # --- REGIONAL POPULARITY ---

            st.subheader("🌍 Regional Popularity")

            pytrends.build_payload(keywords, timeframe='now 7-d')
            
            try:
                # Get interest by region
                regional_data = pytrends.interest_by_region()
                
                if regional_data.empty:
                    st.warning("No regional trend data found.")
                else:
                    # Sort and select the top regions based on interest
                    regional_data_sorted = regional_data.sort_values(by=keywords[0], ascending=False).head(10)
                    st.write("Top 10 Regions based on interest:")

                    # Plot a bar chart for regional popularity
                    bar_region = px.bar(
                        regional_data_sorted,
                        x=regional_data_sorted.index,
                        y=keywords[0],
                        labels={"x": "Region", "y": f"Interest in {keywords[0]}"},
                        title="Regional Popularity of Hashtag"
                    )
                    st.plotly_chart(bar_region, use_container_width=True)

            except Exception as e:
                st.error(f"Error fetching regional data: {str(e)}")
