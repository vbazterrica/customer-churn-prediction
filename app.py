import streamlit as st
import pandas as pd
import plotly.express as px
import warnings
warnings.filterwarnings("ignore")

# -----------------------
# Función PowerBI style
def powerbi_style(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#F3F6F9",
        plot_bgcolor="white",
        font=dict(color="#0F172A", family="Inter"),
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="x unified",
        colorway=["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#06B6D4"],
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    fig.update_xaxes(showgrid=False, linecolor="#D1D5DB")
    fig.update_yaxes(gridcolor="#E5E7EB", zeroline=False)
    return fig

# -----------------------
# Configuración página
st.set_page_config(page_title="Customer Intelligence System", layout="wide")

# -----------------------
# CSS estilo Enterprise
st.markdown("""
<style>
.stApp { background-color: #F3F6F9; }
.block-container { padding: 2rem 2.5rem; max-width: 1400px; }

/* KPI cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #2563EB, #10B981);
    color: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.12);
    text-align: center;
    transition: 0.2s;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0px 10px 28px rgba(0,0,0,0.18);
}
[data-testid="stMetricLabel"] { color: #D1FAE5 !important; font-size: 14px; }
[data-testid="stMetricValue"] { color: white !important; font-size: 30px; font-weight: 800; }

/* Sidebar */
[data-testid="stSidebar"] { background-color: white; border-right: 1px solid #D1D5DB; }

/* Tabs */
.stTabs [data-baseweb="tab"] { font-size: 18px !important; font-weight: 700 !important; padding: 16px 24px !important; color: #475569; }
.stTabs [aria-selected="true"] { color: #2563EB !important; border-bottom: 4px solid #2563EB; }

/* Headers */
h1,h2,h3 { color:#0F172A!important; }
</style>
""", unsafe_allow_html=True)

# -----------------------
# Título
st.title("📊 Customer Intelligence & Churn System")
st.markdown("Understand customer value, churn risk and revenue drivers")
st.markdown("---")

# -----------------------
# Load Data
@st.cache_data
def load_data():
    df = pd.read_csv("ecommerce_customer_churn_large.csv")
    return df

df = load_data()
df["revenue"] = df["avg_order_value"] * df["total_orders"]

# -----------------------
# Segmentación simple
def churn_segment(row):
    if row["churn"] == 1: return "Churned"
    elif row["last_purchase_days_ago"] > 60: return "At Risk"
    else: return "Active"
df["segment"] = df.apply(churn_segment, axis=1)

# -----------------------
# Sidebar Filters
df["city"] = df["city"].astype(str)
df["subscription_type"] = df["subscription_type"].astype(str)

st.sidebar.title("Filters")

city_filter = st.sidebar.multiselect(
    "City",
    df["city"].unique(),
    df["city"].unique()
)

subscription_filter = st.sidebar.multiselect(
    "Subscription Type",
    df["subscription_type"].unique(),
    df["subscription_type"].unique()
)

# -----------------------
# FILTER LOGIC (CORRECT)
filtered_df = df.copy()

if city_filter:
    filtered_df = filtered_df[filtered_df["city"].isin(city_filter)]

if subscription_filter:
    filtered_df = filtered_df[filtered_df["subscription_type"].isin(subscription_filter)]

# -----------------------
# EMPTY CHECK
if filtered_df.empty:
    st.warning("No data for selected filters")
    st.stop()

# -----------------------
# KPIs
total_customers = len(filtered_df)
total_revenue = filtered_df["revenue"].sum()
churn_rate = filtered_df["churn"].mean()
avg_order_value = filtered_df["avg_order_value"].mean()

col1,col2,col3,col4 = st.columns(4)
col1.metric("👥 Customers", total_customers)
col2.metric("💰 Revenue", f"${total_revenue:,.0f}")
col3.metric("⚠️ Churn Rate", f"{churn_rate:.2%}")
col4.metric("🧾 Avg Order Value", f"${avg_order_value:,.2f}")

# -----------------------
# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview","👥 Customers","⚠️ Churn Risk","💰 Revenue","📦 Segments","🧠 Insights"
])

# -----------------------
# TAB 1 - Overview
with tab1:
    st.subheader("📊 Executive Overview")
    segment_counts = filtered_df["segment"].value_counts().reset_index()
    segment_counts.columns = ["Segment","Count"]
    fig = px.pie(segment_counts, names="Segment", values="Count",
                 color_discrete_sequence=["#2563EB", "#10B981", "#F59E0B"])
    fig = powerbi_style(fig)
    st.plotly_chart(fig, use_container_width=True, key="overview_pie")

# -----------------------
# TAB 2 - Customer 360
with tab2:
    st.subheader("👥 Customer 360 Analysis")
    top_customers = filtered_df.groupby("customer_id")["revenue"].sum().reset_index().sort_values("revenue", ascending=False).head(10)
    fig = px.bar(top_customers, x="customer_id", y="revenue",
                 color_discrete_sequence=["#2563EB"], title="Top 10 Customers by Revenue")
    fig = powerbi_style(fig)
    st.plotly_chart(fig, use_container_width=True, key="top_customers_bar")

    customer_stats = filtered_df.groupby("customer_id").agg({"total_orders":"mean","avg_order_value":"mean","revenue":"sum"}).reset_index()
    fig = px.scatter(customer_stats, x="total_orders", y="avg_order_value", size="revenue",
                     color="revenue", color_continuous_scale=["#2563EB","#10B981","#F59E0B"], title="Orders vs Avg Order Value")
    fig = powerbi_style(fig)
    st.plotly_chart(fig, use_container_width=True, key="orders_vs_avg_scatter")

# -----------------------
# TAB 3 - Churn Risk
with tab3:
    st.subheader("⚠️ Churn Risk Analysis")
    churned = len(filtered_df[filtered_df["segment"]=="Churned"])
    at_risk = len(filtered_df[filtered_df["segment"]=="At Risk"])
    active = len(filtered_df[filtered_df["segment"]=="Active"])
    c1,c2,c3 = st.columns(3)
    c1.metric("🔴 Churned", churned)
    c2.metric("🟡 At Risk", at_risk)
    c3.metric("🟢 Active", active)

    churn_by_sub = filtered_df.groupby("subscription_type")["churn"].mean().reset_index()
    fig = px.bar(churn_by_sub, x="subscription_type", y="churn",
                 color="churn", color_continuous_scale="Reds", title="Churn Rate by Subscription")
    fig = powerbi_style(fig)
    st.plotly_chart(fig, use_container_width=True, key="churn_by_sub_bar")

# -----------------------
# TAB 4 - Revenue
with tab4:
    st.subheader("💰 Revenue Intelligence")
    revenue_by_sub = filtered_df.groupby("subscription_type")["revenue"].sum().reset_index()
    fig = px.bar(revenue_by_sub, x="subscription_type", y="revenue",
                 color="revenue", color_continuous_scale="Greens", title="Revenue by Subscription Type")
    fig = powerbi_style(fig)
    st.plotly_chart(fig, use_container_width=True, key="revenue_by_sub_bar")

# -----------------------
# TAB 5 - Segments
with tab5:
    st.subheader("📦 Customer Segments")
    revenue_segment = filtered_df.groupby("segment")["revenue"].sum().reset_index()
    fig = px.pie(revenue_segment, names="segment", values="revenue",
                 color_discrete_sequence=["#2563EB","#10B981","#F59E0B"], title="Revenue by Segment")
    fig = powerbi_style(fig)
    st.plotly_chart(fig, use_container_width=True, key="rev_by_segment_pie")

# -----------------------
# TAB 6 - Insights
with tab6:
    st.subheader("🧠 AI-Style Business Insights")
    churn_pct = filtered_df["churn"].mean()
    top_city = filtered_df.groupby("city")["revenue"].sum().idxmax()
    top_subscription = filtered_df.groupby("subscription_type")["revenue"].sum().idxmax()
    avg_tickets = filtered_df["support_tickets"].mean()
    high_risk = filtered_df[filtered_df["segment"]=="At Risk"]

    st.markdown(f"""
### 📊 Executive Summary
- ⚠️ **Churn Rate:** {churn_pct:.2%}
- 📍 **Most profitable city:** {top_city}
- 💳 **Best subscription type:** {top_subscription}
- 🎧 **Avg support tickets per customer:** {avg_tickets:.2f}
- 🟡 **At Risk customers:** {len(high_risk)}
""")

    churn_by_sub = filtered_df.groupby("subscription_type")["churn"].mean().reset_index()
    fig = px.bar(churn_by_sub, x="subscription_type", y="churn",
                 color="churn", color_continuous_scale="Reds", title="Churn Rate by Subscription Type")
    fig = powerbi_style(fig)
    st.plotly_chart(fig, use_container_width=True, key="insights_churn_bar")