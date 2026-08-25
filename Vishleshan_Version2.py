import streamlit as st
import pandas as pd
import numpy as np

# --- Page Configuration ---
st.set_page_config(
    page_title="Fuel Station Q&Q Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR IOCL THEME & PROFESSIONAL UI ---
st.markdown("""
    <style>
    /* IOCL Color Palette: Orange (#F37021), Blue (#0055A5) */
    
    /* Main Background */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #0055A5 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Metrics / KPI Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 2px solid #F37021;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetricLabel"] {
        color: #0055A5;
        font-weight: bold;
    }
    
    /* Tables/Dataframes */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #ddd;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0055A5;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] label {
        color: white !important;
    }
    
    /* Buttons/Inputs */
    .stSelectbox label {
        color: #F37021 !important;
        font-weight: bold;
    }
    
    /* Tabs/Expanders */
    .streamlit-expanderHeader {
        background-color: #eef4fa;
        color: #0055A5;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title Section ---
c1, c2 = st.columns([1, 10])
with c1:
    # You can replace this with an actual logo image if you have one locally
    st.markdown("## ⛽") 
with c2:
    st.title("Fuel Station Q&Q Analysis Portal")
    st.markdown("**Secure Local Analysis Tool** | *Powered by Automation Data*")

st.markdown("---")

# --- Sidebar: File Uploads ---
st.sidebar.header("📂 Upload Reports")
st.sidebar.markdown("Please upload your exported files below:")
du_file = st.sidebar.file_uploader("Upload DU Logs", type=['xlsx', 'csv'])
sir_file = st.sidebar.file_uploader("Upload SIR Report", type=['xlsx', 'csv'])
preset_file = st.sidebar.file_uploader("Upload Preset Mismatch", type=['xlsx', 'csv'])

# --- Helper Function: Load Data ---
@st.cache_data
def load_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

# ==========================================
# 1. DU ERROR LOGS ANALYSIS
# ==========================================
if du_file:
    st.header("1. DU Error Log Analysis")
    try:
        df_du = load_data(du_file)
        df_du.columns = df_du.columns.str.strip()
        
        # Identify Error Column
        error_col = 'Parameter6 Value'
        if error_col not in df_du.columns:
            for col in df_du.columns:
                if df_du[col].astype(str).str.contains("Error:", na=False).any():
                    error_col = col
                    break
        
        # Extract Codes
        df_du['Error Code'] = df_du[error_col].astype(str).str.extract(r'Error:(\w+)')
        df_du['Error Code'] = df_du['Error Code'].fillna(df_du[error_col])
        
        # Parse Dates & Time
        if 'Date as per DU Log' in df_du.columns:
            df_du['Date'] = pd.to_datetime(df_du['Date as per DU Log'], dayfirst=True, errors='coerce').dt.date
        
        # Extract Hour
        if 'Time as per DU Log' in df_du.columns:
            df_du['DateTime'] = pd.to_datetime(df_du['Time as per DU Log'].astype(str), format='%H:%M:%S', errors='coerce')
            df_du['Hour'] = df_du['DateTime'].dt.hour
        
        # --- TOP 5 KPI CARDS ---
        st.subheader("🚨 Top 5 Critical Errors")
        top_errors = df_du['Error Code'].value_counts().head(5)
        
        cols = st.columns(5)
        for i, (code, count) in enumerate(top_errors.items()):
            with cols[i]:
                st.metric(label=f"Rank {i+1} (Code {code})", value=f"{count}", delta="Events")
        
        st.write("") # Spacer

        # --- INTERACTIVE DRILL DOWN ---
        with st.container():
            st.markdown("### 🔎 Error Code Drill-Down")
            st.info("Select an Error Code below, then pick a specific Date to see the time analysis.")
            
            # 1. Select Code
            selected_code = st.selectbox("Step 1: Select Error Code", top_errors.index.tolist())
            
            if selected_code:
                # Filter by Code
                subset_code = df_du[df_du['Error Code'] == selected_code]
                
                # Layout
                d_col1, d_col2 = st.columns([1, 1])
                
                # --- LEFT: Dates Table ---
                with d_col1:
                    st.markdown(f"**📅 Daily Occurrences for {selected_code}**")
                    if 'Date' in subset_code.columns:
                        date_counts = subset_code['Date'].value_counts().sort_values(ascending=False).reset_index()
                        date_counts.columns = ['Date', 'Count']
                        st.dataframe(date_counts, use_container_width=True, hide_index=True)
                        
                        # DATE SELECTOR (Based on filtered data)
                        available_dates = date_counts['Date'].tolist()
                    else:
                        st.warning("Date column not found.")
                        available_dates = []

                # --- RIGHT: Dynamic Time Analysis ---
                with d_col2:
                    st.markdown("**⏰ Peak Time Analysis**")
                    
                    if available_dates:
                        # 2. Select Date
                        selected_date = st.selectbox("Step 2: Select Date", available_dates)
                        
                        if selected_date:
                            # Filter by Date
                            subset_date = subset_code[subset_code['Date'] == selected_date]
                            
                            if 'Hour' in subset_date.columns and not subset_date.empty:
                                time_counts = subset_date['Hour'].value_counts().sort_values(ascending=False).reset_index()
                                time_counts.columns = ['Hour (24h)', 'Count']
                                time_counts['Time Window'] = time_counts['Hour (24h)'].apply(
                                    lambda x: f"{int(x):02d}:00 - {int(x)+1:02d}:00" if pd.notnull(x) else "Unknown"
                                )
                                st.dataframe(time_counts[['Time Window', 'Count']], use_container_width=True, hide_index=True)
                            else:
                                st.warning("No time data available for this date.")
                    else:
                        st.write("No dates available.")

    except Exception as e:
        st.error(f"Error processing DU Logs: {e}")
    st.markdown("---")

# ==========================================
# 2. SIR (STATISTICAL INVENTORY) ANALYSIS
# ==========================================
if sir_file:
    st.header("2. SIR (Half-Hourly) Analysis")
    try:
        df_sir = load_data(sir_file)
        df_sir.columns = df_sir.columns.str.strip()

        # Data Type Conversion
        df_sir['Variance'] = pd.to_numeric(df_sir['Variance'], errors='coerce').fillna(0)
        df_sir['Stock Date'] = pd.to_datetime(df_sir['Stock Date'], dayfirst=True, errors='coerce').dt.date
        
        # A. VARIATION MATRIX
        st.subheader("A. Half-Hourly Variance Matrix")
        st.markdown("*Red cells indicate variance beyond +/- 50 Litres.*")
        
        matrix = df_sir.pivot_table(index='Stock Date', columns='Stock Time Bucket', values='Variance', aggfunc='sum').fillna(0)
        
        # Highlight Logic
        def highlight_extreme(val):
            color = 'black'
            bg_color = ''
            if val > 50 or val < -50:
                color = 'white'
                bg_color = '#dc3545' # Red
            return f'color: {color}; background-color: {bg_color}'

        st.dataframe(matrix.style.applymap(highlight_extreme), use_container_width=True)

        # B. DAILY ANOMALY SUMMARY
        st.subheader("B. Daily Anomaly & Issue Spotter")
        
        daily_agg = df_sir.groupby('Stock Date').agg(
            Pos_Instances=('Variance', lambda x: (x > 0).sum()),
            Neg_Instances=('Variance', lambda x: (x < 0).sum()),
            Pos_Volume=('Variance', lambda x: x[x > 0].sum()),
            Neg_Volume=('Variance', lambda x: x[x < 0].sum()),
            High_Pos_Instances_50=('Variance', lambda x: (x > 50).sum()),
            High_Neg_Instances_50=('Variance', lambda x: (x < -50).sum())
        ).reset_index()
        
        daily_agg['Net_Variance'] = daily_agg['Pos_Volume'] + daily_agg['Neg_Volume']

        # Find High/Low Buckets
        pos_buckets = df_sir[df_sir['Variance'] > 0].sort_values('Variance', ascending=False).drop_duplicates('Stock Date')[['Stock Date', 'Stock Time Bucket', 'Variance']]
        pos_buckets.rename(columns={'Stock Time Bucket': 'Highest Pos Bucket', 'Variance': 'Max Gain Vol'}, inplace=True)
        
        neg_buckets = df_sir[df_sir['Variance'] < 0].sort_values('Variance', ascending=True).drop_duplicates('Stock Date')[['Stock Date', 'Stock Time Bucket', 'Variance']]
        neg_buckets.rename(columns={'Stock Time Bucket': 'Highest Neg Bucket', 'Variance': 'Max Loss Vol'}, inplace=True)

        final_summary = daily_agg.merge(pos_buckets, on='Stock Date', how='left').merge(neg_buckets, on='Stock Date', how='left').fillna("-")
        
        # Formatting
        final_cols = ['Stock Date', 'Net_Variance', 'Pos_Instances', 'Neg_Instances', 'High_Pos_Instances_50', 'High_Neg_Instances_50', 'Pos_Volume', 'Neg_Volume', 'Highest Pos Bucket', 'Max Gain Vol', 'Highest Neg Bucket', 'Max Loss Vol']
        final_summary = final_summary[final_cols]
        
        st.dataframe(final_summary.style.format({
            'Net_Variance': "{:.2f}",
            'Pos_Volume': "{:.2f}",
            'Neg_Volume': "{:.2f}",
            'Max Gain Vol': "{}", 
            'Max Loss Vol': "{}"
        }), use_container_width=True)

    except Exception as e:
        st.error(f"Error processing SIR Report: {e}")
    st.markdown("---")

# ==========================================
# 3. PRESET MISMATCH ANALYSIS
# ==========================================
if preset_file:
    st.header("3. Preset Mismatch Analysis")
    try:
        df_pre = load_data(preset_file)
        df_pre.columns = df_pre.columns.str.strip()

        mask = df_pre['Preset Amount Mismatch Flag'].notna() & \
               ~df_pre['Preset Amount Mismatch Flag'].isin(['N', 'No', '0', False])
        mismatches = df_pre[mask].copy()

        if not mismatches.empty:
            mismatches['Vol_Diff'] = pd.to_numeric(mismatches['Quantity'], errors='coerce') - pd.to_numeric(mismatches['Preset Qty'], errors='coerce')
            mismatches['Amt_Diff'] = pd.to_numeric(mismatches['Amount'], errors='coerce') - pd.to_numeric(mismatches['Preset Amount'], errors='coerce')
            
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("By Preset AMOUNT")
                amt_stats = mismatches.groupby('Preset Amount').agg(
                    Count=('Preset Amount', 'size'),
                    Avg_Amt_Diff=('Amt_Diff', 'mean'),  
                    Avg_Vol_Diff=('Vol_Diff', 'mean')   
                ).sort_values('Count', ascending=False).head(10)
                
                st.dataframe(amt_stats.style.format({'Avg_Amt_Diff': "₹ {:.2f}", 'Avg_Vol_Diff': "{:.3f} L"}), use_container_width=True)

            with c2:
                st.subheader("By Preset VOLUME")
                qty_stats = mismatches.groupby('Preset Qty').agg(
                    Count=('Preset Qty', 'size'),
                    Avg_Vol_Diff=('Vol_Diff', 'mean')
                ).sort_values('Count', ascending=False).head(10)
                
                st.dataframe(qty_stats.style.format({'Avg_Vol_Diff': "{:.3f} L"}), use_container_width=True)

            st.subheader("Detailed Mismatch Log")
            st.dataframe(mismatches[['Transaction Date', 'Preset Amount', 'Amount', 'Amt_Diff', 'Preset Qty', 'Quantity', 'Vol_Diff', 'Half Hourly Bucket']], use_container_width=True)
        else:
            st.success("No Preset Mismatches found.")

    except Exception as e:
        st.error(f"Error processing Preset Report: {e}")

# --- Footer ---
st.markdown("---")
st.caption("Developed for Fuel Automation Analysis | Version 2.0 (IOCL Theme)")
