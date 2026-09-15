import numpy as np
import plotly.graph_objects as go
import streamlit as st

from bond_math import approximation_curves, bond_price, risk_measures


st.set_page_config(
    page_title="Duration & Convexity Analyzer",
    page_icon="〽️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1280px; padding-top: 2rem;}
    [data-testid="stMetric"] {background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, .25);
        padding: 1rem; border-radius: .75rem;}
    .eyebrow {color: var(--text-color); opacity: .65; font-size:.78rem; font-weight:700;
        letter-spacing:.12em; text-transform:uppercase; margin-bottom:.35rem;}
    .note {color: var(--text-color); font-size:.92rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="eyebrow">Fixed income analytics</div>', unsafe_allow_html=True)
st.title("Duration & Convexity Analyzer")
st.caption(
    "Explore how a bond's price responds to yield changes—and where the linear "
    "duration estimate begins to break down."
)

with st.sidebar:
    st.header("Bond assumptions")
    face_value = st.number_input("Face value", 100.0, 100_000.0, 1_000.0, 100.0)
    coupon_pct = st.slider("Annual coupon rate", 0.0, 15.0, 5.0, 0.25, format="%.2f%%")
    maturity = st.slider("Years to maturity", 1, 40, 10)
    frequency_label = st.selectbox("Coupon frequency", ["Annual", "Semiannual", "Quarterly"], index=1)
    frequency = {"Annual": 1, "Semiannual": 2, "Quarterly": 4}[frequency_label]

    st.divider()
    st.header("Rate scenario")
    base_yield_pct = st.slider("Current yield to maturity", 0.25, 15.0, 5.0, 0.25, format="%.2f%%")
    shock_bps = st.slider("Yield range around current yield", 25, 500, 300, 25, format="±%d bps")

coupon_rate = coupon_pct / 100
base_yield = base_yield_pct / 100
price, macaulay, modified, convexity = risk_measures(
    face_value, coupon_rate, maturity, base_yield, frequency
)

max_downward_move = max(0.0, base_yield - 0.0001)
low_yield = max(0.0001, base_yield - min(shock_bps / 10_000, max_downward_move))
high_yield = base_yield + shock_bps / 10_000
yields = np.linspace(low_yield, high_yield, 241)
duration_prices, convexity_prices = approximation_curves(
    price, modified, convexity, base_yield, yields
)
exact_prices = bond_price(face_value, coupon_rate, maturity, yields, frequency)

metric_cols = st.columns(4)
metric_cols[0].metric("Current price", f"${price:,.2f}")
metric_cols[1].metric("Macaulay duration", f"{macaulay:.2f} yrs")
metric_cols[2].metric("Modified duration", f"{modified:.2f}")
metric_cols[3].metric("Convexity", f"{convexity:.2f}")

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=yields * 100,
        y=exact_prices,
        name="Exact bond price",
        line=dict(color="#94a3b8", width=2),
        hovertemplate="Yield: %{x:.2f}%<br>Price: $%{y:,.2f}<extra></extra>",
    )
)
fig.add_trace(
    go.Scatter(
        x=yields * 100,
        y=duration_prices,
        name="Duration (linear)",
        line=dict(color="#3b82f6", width=3),
        hovertemplate="Yield: %{x:.2f}%<br>Duration price: $%{y:,.2f}<extra></extra>",
    )
)
fig.add_trace(
    go.Scatter(
        x=yields * 100,
        y=convexity_prices,
        name="Duration + convexity",
        line=dict(color="#ef7d32", width=3, dash="dash"),
        hovertemplate="Yield: %{x:.2f}%<br>Convexity price: $%{y:,.2f}<extra></extra>",
    )
)
fig.add_trace(
    go.Scatter(
        x=[base_yield_pct],
        y=[price],
        mode="markers",
        name="Current position",
        marker=dict(color="#8b5cf6", size=11, line=dict(color="white", width=2)),
        hovertemplate="Current yield: %{x:.2f}%<br>Current price: $%{y:,.2f}<extra></extra>",
    )
)
fig.add_vline(x=base_yield_pct, line_width=1, line_dash="dot", line_color="#94a3b8")
fig.update_layout(
    height=570,
    margin=dict(l=20, r=20, t=55, b=20),
    title=dict(text="Price–yield relationship", font=dict(size=20)),
    xaxis_title="Yield to maturity (%)",
    yaxis_title="Bond price ($)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
)
fig.update_xaxes(showgrid=True, ticksuffix="%")
fig.update_yaxes(showgrid=True, tickprefix="$", separatethousands=True)
st.plotly_chart(fig, width="stretch", theme="streamlit")

left, right = st.columns([1.4, 1])
with left:
    st.subheader("How to read the chart")
    st.markdown(
        "The **gray line** is the exact bond price: the present value of every future "
        "cash flow, discounted at the yield to maturity. It assumes one rate discounts "
        "all cash flows and that settlement is on a coupon date. "
        "The **solid blue line** uses duration alone, so it is a straight-line estimate. "
        "The **dashed orange line** adds convexity, bending toward the bond's actual "
        "price–yield relationship. Near the current yield, the two estimates nearly "
        "overlap. As the yield move grows, the convexity adjustment becomes more visible."
    )
with right:
    # Bound downward moves the same way as the chart range (line ~55): the
    # yield floor is 1 bp, so options never produce a clamped scenario.
    max_down_bps = min(shock_bps, (round(base_yield * 10_000) - 1) // 25 * 25)
    scenario_move = st.select_slider(
        "Inspect a yield change",
        options=list(range(-max_down_bps, shock_bps + 1, 25)),
        value=min(100, shock_bps),
        format_func=lambda value: f"{value:+,} bps",
    )
    scenario_yield = base_yield + scenario_move / 10_000
    scenario_duration, scenario_convexity = approximation_curves(
        price, modified, convexity, base_yield, np.array([scenario_yield])
    )
    scenario_exact = bond_price(face_value, coupon_rate, maturity, scenario_yield, frequency)
    duration_error = scenario_duration[0] - scenario_exact
    convexity_error = scenario_convexity[0] - scenario_exact
    st.markdown(
        f"""
        <div class="note">
        At a <b>{scenario_yield * 100:.2f}% yield</b>:<br>
        Exact repricing: <b>${scenario_exact:,.2f}</b><br>
        Duration estimate: <b>${scenario_duration[0]:,.2f}</b>
        (error ${duration_error:+,.2f}, {duration_error / scenario_exact:+.2%})<br>
        Duration + convexity: <b>${scenario_convexity[0]:,.2f}</b>
        (error ${convexity_error:+,.2f}, {convexity_error / scenario_exact:+.2%})
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption(
    "Educational model for a plain fixed-rate bond. It assumes level yields, fixed cash "
    "flows, and no credit, liquidity, tax, or embedded-option effects."
)
