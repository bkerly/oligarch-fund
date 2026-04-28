import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="The Oligarch Fund", layout="wide")
st.title("The Oligarch Fund 🏛️")
st.markdown("Mirroring the portfolios of America's 10 wealthiest individuals.")

# 2. Load External Data
@st.cache_data
def load_data():
    history_df = pd.read_csv("fund_history.csv")
    holdings_df = pd.read_csv("current_holdings.csv")
    # Ensure Year is treated as a categorical string for charting
    history_df['Year'] = history_df['Year'].astype(str)
    return history_df, holdings_df

try:
    df_history, df_holdings = load_data()
except FileNotFoundError:
    st.error("Data files not found. Please ensure 'fund_history.csv' and 'current_holdings.csv' are in the same directory.")
    st.stop()

# 3. Calculate Top Level Metrics Dynamically
# Filter for 2026 data to get the current total value
current_value = df_history[df_history['Year'] == '2026']['Value (USD)'].sum()

st.subheader("Investor Performance Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Initial Investment (2024)", "$50,000")
col2.metric("Monthly Contribution", "$2,000")
# Format the dynamic sum to currency
col3.metric("Current Value (April 2026)", f"${current_value:,.0f}", "+21.4% Time-Weighted Return")

st.divider()

# 4. Main Chart (Recreating the Doodle for 10 people)
st.subheader("Fund Value by Oligarch Tracker")
fig_main = px.bar(
    df_history, 
    x='Oligarch', 
    y='Value_USD', 
    color='Year', 
    barmode='group',
    color_discrete_sequence=['#A6B1E1', '#424874', '#DCD6F7'],
    title="Growth of Allocated Funds (2024 - 2026)"
)
fig_main.update_layout(xaxis_title="", yaxis_title="Value (USD)")
st.plotly_chart(fig_main, use_container_width=True)

st.divider()

# 5. Drill-Down Interactive Filter
st.subheader("Holdings Drill-Down")
st.markdown("Select an oligarch below to inspect the specific asset distribution and YoY performance of their slice of the fund.")

# Extract unique oligarchs for the selector
oligarch_list = df_holdings['Oligarch'].unique().tolist()
selected_oligarch = st.selectbox("Select to view portfolio:", options=oligarch_list)

# 6. Render Specific Holdings
if selected_oligarch:
    st.write(f"### Proportional Holdings: {selected_oligarch}")
    
    # Filter the holdings dataframe for the selected individual
    df_selected = df_holdings[df_holdings['Oligarch'] == selected_oligarch].copy()
    
    colA, colB = st.columns([2, 1])
    
    with colA:
        fig_pie = px.pie(
            df_selected, 
            values='Value_USD', 
            names='Asset', 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with colB:
        # Display the dataframe with formatted currency, keeping the YoY growth string
        st.dataframe(
            df_selected[['Asset', 'Value_USD', 'YoY_Growth']].style.format({'Value_USD': '${:,.0f}'}),
            hide_index=True,
            use_container_width=True
        )