import base64
import os
import streamlit as st


def apply_portal_styling():
    img_path = os.path.join(os.path.dirname(__file__), "..", "..", "train photo.webp")
    b64 = ""
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

    bg_css = f'url("data:image/webp;base64,{b64}")' if b64 else "none"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* ── Global font ── */
        html, body, [class*="css"], .stApp, .stMarkdown, p, li, span, label, div {{
            font-family: 'Inter', sans-serif !important;
        }}

        /* ── Background image ── */
        .stApp {{
            background-image: {bg_css};
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        /* ── Semi-transparent white overlay on main content (50%) ── */
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.50);
            border-radius: 12px;
            padding: 2rem 2.5rem;
        }}

        /* ── Headings — white with navy shadow for visibility ── */
        h1 {{
            color: #ffffff !important;
            font-weight: 700 !important;
            font-family: 'Inter', sans-serif !important;
            letter-spacing: -0.5px;
            text-shadow: 0 2px 8px rgba(10,61,143,0.85), 0 1px 3px rgba(0,0,0,0.6);
        }}
        h2, h3 {{
            color: #0a3d8f !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            text-shadow: 0 1px 4px rgba(255,255,255,0.7);
        }}
        h4, h5, h6 {{
            color: #1565c0 !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
        }}

        /* ── Body text — deep blue for readability on white overlay ── */
        p, li, .stMarkdown p, .stMarkdown li {{
            color: #0a3d8f !important;
            font-size: 0.97rem;
            line-height: 1.65;
        }}
        label, .stTextInput label, .stSelectbox label,
        .stFileUploader label, .stSlider label, .stRadio label {{
            color: #1565c0 !important;
            font-weight: 500 !important;
        }}

        /* ── Sidebar — deep blue gradient, white text ── */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(10,61,143,0.97) 0%, rgba(21,101,192,0.95) 100%) !important;
        }}
        [data-testid="stSidebar"] * {{
            color: #ffffff !important;
            font-family: 'Inter', sans-serif !important;
        }}
        [data-testid="stSidebar"] input {{
            background-color: rgba(255,255,255,0.15) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255,255,255,0.4) !important;
            border-radius: 6px !important;
        }}
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {{
            background-color: rgba(255,255,255,0.15) !important;
        }}
        [data-testid="stSidebar"] label {{
            color: #cce0ff !important;
            font-weight: 500 !important;
        }}
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            color: #ffffff !important;
            text-shadow: none !important;
        }}

        /* ── Buttons (default) — white bg, blue text/border ── */
        .stButton > button {{
            background-color: #ffffff !important;
            color: #1565c0 !important;
            border: 2px solid #1565c0 !important;
            border-radius: 8px;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.92rem;
            letter-spacing: 0.3px;
            transition: background-color 0.2s, color 0.2s, box-shadow 0.2s;
        }}
        .stButton > button:hover {{
            background-color: #1565c0 !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(21,101,192,0.35) !important;
        }}
        /* Primary buttons — solid blue, white text ── */
        .stButton > button[kind="primary"] {{
            background-color: #1565c0 !important;
            color: #ffffff !important;
            border: none !important;
        }}
        .stButton > button[kind="primary"]:hover {{
            background-color: #0a3d8f !important;
            box-shadow: 0 4px 12px rgba(10,61,143,0.4) !important;
        }}

        /* ── Download buttons ── */
        .stDownloadButton > button {{
            background-color: #ffffff !important;
            color: #1565c0 !important;
            border: 2px solid #1565c0 !important;
            border-radius: 8px;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
        }}
        .stDownloadButton > button:hover {{
            background-color: #1565c0 !important;
            color: #ffffff !important;
        }}

        /* ── Metric boxes ── */
        [data-testid="stMetric"] {{
            background-color: rgba(21, 101, 192, 0.12);
            border-left: 4px solid #1565c0;
            border-radius: 8px;
            padding: 0.7rem 1rem;
        }}
        [data-testid="stMetricLabel"] {{
            color: #1565c0 !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
        }}
        [data-testid="stMetricValue"] {{
            color: #0a3d8f !important;
            font-weight: 700 !important;
        }}

        /* ── Tabs ── */
        .stTabs [data-baseweb="tab"] {{
            color: #1565c0 !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
        }}
        .stTabs [data-baseweb="tab-highlight"] {{
            background-color: #1565c0 !important;
        }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            color: #0a3d8f !important;
        }}

        /* ── Alerts ── */
        [data-testid="stAlert"] {{
            border-radius: 8px;
            font-family: 'Inter', sans-serif !important;
        }}

        /* ── Divider ── */
        hr {{ border-color: #1565c0 !important; opacity: 0.25; }}

        /* ── Progress bar ── */
        .stProgress > div > div > div > div {{
            background-color: #1565c0 !important;
        }}

        /* ── Captions / small text ── */
        .stCaption, small {{
            color: #1565c0 !important;
            font-family: 'Inter', sans-serif !important;
        }}

        /* ── Data editor / dataframe headers ── */
        [data-testid="stDataFrame"] th {{
            background-color: #1565c0 !important;
            color: #ffffff !important;
            font-family: 'Inter', sans-serif !important;
        }}

        /* ── Info box text ── */
        [data-testid="stAlert"] p {{
            color: inherit !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
