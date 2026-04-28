import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="The Oligarch Fund", layout="wide")
st.title("The Oligarch Fund 🏛️")
st.markdown("Mirroring the portfolios of America's wealthiest individuals.")

# 2. Load External Data FIRST (so we can generate dynamic sliders)
@st.cache_data
def load_data():
    df = pd.read_csv("oligarch_data.csv")
    # Convert the YoY_Growth string (e.g. "+150%") into a usable math decimal (1.50)
    df['YoY_Float'] = df['YoY_Growth'].astype(str).str.replace('+', '', regex=False).str.replace('%', '', regex=False).astype(float) / 100.0
    return df

try:
    df_data = load_data()
except FileNotFoundError:
    st.error("Please ensure 'oligarch_data.csv' is in the same directory.")
    st.stop()

oligarchs = df_data['Oligarch'].unique()

# --- SIDEBAR: Investor Options & Custom Sliders ---
st.sidebar.header("Investment Inputs")
init_inv = st.sidebar.number_input("Initial Investment ($)", min_value=0, value=50000, step=5000)
monthly_cont = st.sidebar.number_input("Monthly Contribution ($)", min_value=0, value=2000, step=500)

st.sidebar.divider()
st.sidebar.header("Fund Allocation")
st.sidebar.markdown("Adjust your relative exposure. Set to 0 to remove them from the fund entirely.")

# Generate a slider for every oligarch found in the CSV
raw_weights = {}
for oligarch in oligarchs:
    # Defaulting everyone to an equal relative weight of 10
    raw_weights[oligarch] = st.sidebar.slider(oligarch, min_value=0, max_value=100, value=10, step=1)

# Normalize the weights so they always equal 100% of the principal
total_raw_weight = sum(raw_weights.values())

if total_raw_weight == 0:
    st.sidebar.error("⚠️ Please allocate weight to at least one individual.")
    st.stop()

normalized_weights = {k: v / total_raw_weight for k, v in raw_weights.items()}

# 3. Dynamic Fund Calculation
months_invested = {'2024': 12, '2025': 24, '2026': 28}

# Pre-calculate a unique growth factor for each oligarch based on their assets
oligarch_growth_rates = {}
for oligarch in oligarchs:
    subset = df_data[df_data['Oligarch'] == oligarch]
    weighted_growth = (subset['Asset_Pct'] * subset['YoY_Float']).sum()
    oligarch_growth_rates[oligarch] = weighted_growth

history_records = []
current_allocations = {}
growth_scaling = {'2024': 0.33, '2025': 0.66, '2026': 1.0}

for year, m in months_invested.items():
    principal = init_inv + (monthly_cont * m)
    
    for oligarch in oligarchs:
        # Use the normalized weight from the user's sliders
        weight = normalized_weights[oligarch]
        
        # If weight is 0, skip the math to keep the data clean
        if weight == 0:
            if year == '2026':
                current_allocations[oligarch] = 0
            continue
            
        allocated_principal = principal * weight
        
        base_growth = oligarch_growth_rates[oligarch]
        scaled_growth = base_growth * growth_scaling[year]
        
        multiplier = max(0.0, 1.0 + scaled_growth)
        value = allocated_principal * multiplier
        
        history_records.append({'Year': year, 'Oligarch': oligarch, 'Value_USD': value})
        
        if year == '2026':
            current_allocations[oligarch] = value

df_history = pd.DataFrame(history_records)
current_total_value = df_history[df_history['Year'] == '2026']['Value_USD'].sum()
total_principal_2026 = init_inv + (monthly_cont * months_invested['2026'])

return_pct = ((current_total_value - total_principal_2026) / total_principal_2026) * 100

# Top Level Metrics
st.subheader("Investor Performance Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Principal Invested", f"${total_principal_2026:,.0f}")
col2.metric("Active Allocations", sum(1 for w in normalized_weights.values() if w > 0))
col3.metric("Current Value (April 2026)", f"${current_total_value:,.0f}", f"{return_pct:+.1f}% Total Return")

st.divider()

# 4. Portfolio Growth Over Time Chart
st.subheader("Fund Growth vs. Principal Invested")

summary_records = []
for year in ['2024', '2025', '2026']:
    year_total = df_history[df_history['Year'] == year]['Value_USD'].sum()
    m = months_invested[year]
    year_principal = init_inv + (monthly_cont * m)
    
    summary_records.append({'Year': year, 'Metric': 'Principal (Cash In)', 'USD': year_principal})
    summary_records.append({'Year': year, 'Metric': 'Total Fund Value', 'USD': year_total})

df_summary = pd.DataFrame(summary_records)

fig_line = px.line(
    df_summary, 
    x='Year', 
    y='USD', 
    color='Metric', 
    markers=True,
    color_discrete_sequence=['#888888', '#2ECB71'],
    title="Portfolio Value Trajectory"
)
fig_line.update_layout(xaxis_title="", yaxis_title="Amount (USD)")
st.plotly_chart(fig_line, use_container_width=True)

st.divider()

# 5. Main Chart (Oligarch Bar Chart)
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
fig_main.update_layout(xaxis_title="Oligarch", yaxis_title="Value (USD)")
st.plotly_chart(fig_main, use_container_width=True)

st.divider()

# 6. Drill-Down Interactive Filter
st.subheader("Holdings Drill-Down")

# Only show oligarchs in the dropdown who actually have a weight > 0
active_oligarchs = [o for o in oligarchs if normalized_weights[o] > 0]

if active_oligarchs:
    selected_oligarch = st.selectbox("Select to view portfolio:", options=active_oligarchs)

    if selected_oligarch:
        st.write(f"### Proportional Holdings: {selected_oligarch}")
        
        df_selected = df_data[df_data['Oligarch'] == selected_oligarch].copy()
        allocated_dollars = current_allocations[selected_oligarch]
        
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
else:
    st.info("Adjust the sliders in the sidebar to allocate funds and view specific holdings.")