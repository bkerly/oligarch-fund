import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Page Configuration
st.set_page_config(page_title="The Oligarch Fund", layout="wide")
st.title("The Oligarch Fund 🏛️")
st.markdown("Mirroring the portfolios of America's 10 wealthiest individuals.")

# --- SIDEBAR: Investor Options ---
st.sidebar.header("Investor Options")
init_inv = st.sidebar.number_input("Initial Investment ($)", min_value=0, value=50000, step=5000)
monthly_cont = st.sidebar.number_input("Monthly Contribution ($)", min_value=0, value=2000, step=500)
weighting = st.sidebar.radio("Fund Weighting", ["Even Distribution (10% each)", "Net Worth Weighted"])

# 2. Load External Data
@st.cache_data
def load_data():
    return pd.read_csv("oligarch_data.csv")

try:
    df_data = load_data()
except FileNotFoundError:
    st.error("Please ensure 'oligarch_data.csv' is in the same directory.")
    st.stop()

# 3. Dynamic Fund Calculation
# Timeframe variables: 2024 to April 2026
months_invested = {'2024': 12, '2025': 24, '2026': 28}
oligarchs = df_data['Oligarch'].unique()
total_net_worth = df_data.groupby('Oligarch')['NetWorth_B'].first().sum()

history_records = []
current_allocations = {}

for year, m in months_invested.items():
    principal = init_inv + (monthly_cont * m)
    
    for oligarch in oligarchs:
        # Determine slice based on the sidebar weighting option
        if weighting == "Net Worth Weighted":
            nw = df_data[df_data['Oligarch'] == oligarch]['NetWorth_B'].iloc[0]
            weight = nw / total_net_worth
        else:
            weight = 1.0 / len(oligarchs)
            
        allocated_principal = principal * weight
        
        # Simulate active growth to reflect historical returns
        growth_multiplier = {'2024': 1.08, '2025': 1.15, '2026': 1.21}[year]
        value = allocated_principal * growth_multiplier
        
        history_records.append({'Year': year, 'Oligarch': oligarch, 'Value_USD': value})
        
        # Store the current 2026 total value for the drill-down section
        if year == '2026':
            current_allocations[oligarch] = value

df_history = pd.DataFrame(history_records)
current_total_value = df_history[df_history['Year'] == '2026']['Value_USD'].sum()

# Top Level Metrics
st.subheader("Investor Performance Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Principal Invested", f"${(init_inv + (monthly_cont * 28)):,.0f}")
col2.metric("Weighting Strategy", weighting.split()[0])
col3.metric("Current Value (April 2026)", f"${current_total_value:,.0f}", "+21.0% Simulated Return")

st.divider()

# 4. Main Chart
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

# 5. Little Cartoons Array (Directly under the chart)
cartoon_cols = st.columns(10)
for i, oligarch in enumerate(oligarchs):
    with cartoon_cols[i]:
        # Formats the name to look for a local file (e.g., 'elon_musk.png')
        filename = oligarch.lower().replace(" ", "_") + ".png"
        
        if os.path.exists(filename):
            st.image(filename, use_container_width=True)
            st.markdown(f"<div style='text-align: center;'><small>{oligarch.split()[0]}</small></div>", unsafe_allow_html=True)
        else:
            # Fallback icon if the image file isn't in your folder yet
            st.markdown(f"<div style='text-align: center; font-size: 2rem;'>👤</div><div style='text-align: center;'><small>{oligarch.split()[0]}</small></div>", unsafe_allow_html=True)

st.divider()

# 6. Drill-Down Interactive Filter
st.subheader("Holdings Drill-Down")
selected_oligarch = st.selectbox("Select to view portfolio:", options=oligarchs)

if selected_oligarch:
    st.write(f"### Proportional Holdings: {selected_oligarch}")
    
    # Isolate the specific oligarch and grab their 2026 allocated dollar total
    df_selected = df_data[df_data['Oligarch'] == selected_oligarch].copy()
    allocated_dollars = current_allocations[selected_oligarch]
    
    # Multiply their percentage split by the total dollars to get exact amounts
    df_selected['Calculated_Value'] = df_selected['Asset_Pct'] * allocated_dollars
    
    colA, colB = st.columns([2, 1])
    
    with colA:
        fig_pie = px.pie(
            df_selected, 
            values='Calculated_Value', 
            names='Asset', 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with colB:
        st.dataframe(
            df_selected[['Asset', 'Calculated_Value', 'YoY_Growth']].style.format({'Calculated_Value': '${:,.0f}'}),
            hide_index=True,
            use_container_width=True
        )