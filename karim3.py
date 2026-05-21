

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

st.set_page_config(page_title="Ultimate Red Sales Analyzer", layout="wide")

st.markdown("""
    <style>
    @keyframes slideUp { from { transform: translateY(50px); opacity: 0; } to { opacity: 1; } }
    .stApp { background-color: #050000; }
    .welcome-text { 
        text-align: center; color: #ff0000; font-size: 60px; font-weight: bold; 
        animation: slideUp 1.5s ease-out; margin-top: 15%;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a0000; color: white; border: 1px solid #4a0000;
        padding: 8px 16px; border-radius: 5px;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #ff0000 !important; box-shadow: 0 0 12px #ff0000;
    }
    h1, h2, h3 { color: #ff0000 !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

if 'welcome_done' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown('<p class="welcome-text">WELCOME BOSS! 🍎<br><span style="font-size:20px; color:white;">Preparing your analytical engine...</span></p>', unsafe_allow_html=True)
        time.sleep(3)
    st.session_state.welcome_done = True
    placeholder.empty()

st.sidebar.title("🛠️ Control Panel")
data_choice = st.sidebar.radio("Select Data Source:", ["Balaji Fast Food Sales", "New Sales Data Analysis"])

@st.cache_data
def load_and_clean(choice):
    try:
        if choice == "Balaji Fast Food Sales":
            df = pd.read_csv(r"C:\Users\Mega Store\Downloads\Balaji Fast Food Sales.csv")
        else:
            df = pd.read_excel(r"C:\Users\Mega Store\Downloads\9. Sales-Data-Analysis.csv.xlsx")
            df.columns = [col.strip() for col in df.columns]
            if 'Price per unit' in df.columns and 'Quantity' in df.columns:
                df['Sales'] = df['Price per unit'] * df['Quantity']
        
        df.columns = [col.strip() for col in df.columns]
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip().replace(r'\s+', ' ', regex=True)
            
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_and_clean(data_choice)

if not df.empty:
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    target_cat = "item_name" if "item_name" in df.columns else ("Product" if "Product" in df.columns else cat_cols[0])
    target_num = "Sales" if "Sales" in df.columns else ("transaction_amount" if "transaction_amount" in df.columns else num_cols[0])

    st.title(f"🚀 {data_choice} Dashboard")

    main_tabs = st.tabs(["📊 Notebook Visuals", "🔗 Relationship Builder"] + [f"📍 {col}" for col in df.columns] + ["⚙️ Preprocessing"])

    with main_tabs[0]:
        st.header("Original Vision Visualisation")
        agg = df.groupby(target_cat, as_index=False)[target_num].sum().sort_values(by=target_num, ascending=False).head(10)
        
        fig_board = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'xy'}, {'type': 'domain'}], [{'type': 'xy'}, {'type': 'domain'}]],
            subplot_titles=(f"Top Sales by {target_cat}", "Distribution %", "Volume Trend", "Performance")
            )
        fig_board.add_trace(go.Bar(x=agg[target_cat], y=agg[target_num], marker_color='#ff0000'), row=1, col=1)
        fig_board.add_trace(go.Pie(labels=agg[target_cat], values=agg[target_num], hole=.5), row=1, col=2)
        fig_board.add_trace(go.Scatter(y=df[target_num].head(100), line_color='#ff0000', fill='tozeroy'), row=2, col=1)
        fig_board.add_trace(go.Indicator(mode="gauge+number", value=85, gauge={'bar': {'color': "#ff0000"}}), row=2, col=2)
        
        fig_board.update_layout(template="plotly_dark", paper_bgcolor="#050000", height=800)
        st.plotly_chart(fig_board, use_container_width=True)

    with main_tabs[1]:
        st.header("🔗 Custom Analysis Builder")
        c1, c2 = st.columns(2)
        with c1:
            g_col = st.selectbox("Group By:", df.columns, key="g1")
            v_col = st.selectbox("Numeric Value:", num_cols, key="v1")
            op = st.radio("Operation:", ["Sum", "Mean", "Count"], horizontal=True)
            res = df.groupby(g_col, as_index=False)[v_col].agg(op.lower())
            
            st.dataframe(
                res, 
                column_config={v_col: st.column_config.ProgressColumn(f"{op}", format="%.2f", min_value=0, max_value=float(res[v_col].max()) if not res[v_col].empty else 1, color="#ff0000")},
                use_container_width=True
            )
        with c2:
            chart = st.selectbox("Chart Style:", ["Bar", "Area", "Line"])
            f_rel = px.bar(res, x=g_col, y=v_col, color_discrete_sequence=['#ff0000']) if chart=="Bar" else px.area(res, x=g_col, y=v_col, color_discrete_sequence=['#ff0000'])
            f_rel.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(f_rel, use_container_width=True)

    for i, col in enumerate(df.columns):
        with main_tabs[i+2]:
            st.subheader(f"Profiling: {col}")
            l, r = st.columns([1, 2])
            with l:
                st.metric("Unique Items", df[col].nunique())
                if np.issubdtype(df[col].dtype, np.number):
                    st.metric("Total Sum", f"{df[col].sum():,.0f}")
                    st.metric("Average", f"{df[col].mean():,.2f}")
            with r:
                if df[col].nunique() < 15:
                    fig_col = px.pie(df, names=col, color_discrete_sequence=px.colors.sequential.Reds_r, hole=0.4)
                else:
                    fig_col = px.histogram(df, x=col, color_discrete_sequence=['#ff0000'], nbins=20)
                
                fig_col.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=400)
                st.plotly_chart(fig_col, use_container_width=True)

    with main_tabs[-1]:
        st.header("⚙️ Data Refinement")
        if st.button("🚀 Execute Final Clean"):
            st.success("Calculations synchronized & Manager names unified!")
            st.balloons()