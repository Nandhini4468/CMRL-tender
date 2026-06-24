import streamlit as st


def apply_portal_styling():
    # Fix Material icon names showing as text — JS directly replaces the text content
    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <script>
        (function() {
            function fixIconText() {
                document.querySelectorAll('span').forEach(function(span) {
                    if (span.childElementCount === 0) {
                        var t = span.textContent.trim();
                        if (t === 'keyboard_double_arrow_left' || t === 'keyboard_arrow_left') {
                            span.textContent = '❮❮';
                            span.style.fontFamily = 'Arial, sans-serif';
                            span.style.fontSize = '16px';
                        } else if (t === 'keyboard_double_arrow_right' || t === 'keyboard_arrow_right') {
                            span.textContent = '❯❯';
                            span.style.fontFamily = 'Arial, sans-serif';
                            span.style.fontSize = '16px';
                        }
                    }
                });
            }
            fixIconText();
            var observer = new MutationObserver(fixIconText);
            observer.observe(document.documentElement, { childList: true, subtree: true });
        })();
        </script>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* ── Global font & background ── */
        html, body, [class*="css"], .stApp, .stMarkdown, p, li {
            font-family: 'Inter', sans-serif !important;
        }
        .stApp {
            background-color: #f0f6ff;
        }
        .main .block-container {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 2rem 2.5rem;
            box-shadow: 0 2px 12px rgba(21,101,192,0.08);
        }

        /* ── Headings ── */
        h1 {
            color: #0a3d8f !important;
            font-weight: 700 !important;
            font-family: 'Inter', sans-serif !important;
            letter-spacing: -0.5px;
            text-shadow: none !important;
        }
        h2, h3 {
            color: #1565c0 !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            text-shadow: none !important;
        }
        h4, h5, h6 {
            color: #1976d2 !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
        }

        /* ── Body text ── */
        p, li, .stMarkdown p, .stMarkdown li {
            color: #1a1a2e !important;
            font-size: 0.97rem;
            line-height: 1.65;
        }

        /* ── Labels (inputs, sliders, etc.) — avoid touching file uploader internals ── */
        .stTextInput > label,
        .stSelectbox > label,
        .stSlider > label,
        .stRadio > label,
        .stMultiSelect > label,
        .stCheckbox > label {
            color: #1565c0 !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
        }

        /* ── File uploader ── */
        .stFileUploader > label {
            color: #0a3d8f !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
        }
        .stFileUploader [data-testid="stFileUploaderDropzone"] {
            border: 2px dashed #1565c0 !important;
            border-radius: 8px !important;
            background-color: #f0f6ff !important;
        }
        .stFileUploader [data-testid="stFileUploaderDropzone"] p {
            color: #1565c0 !important;
        }
        /* Hide the native browser file input button that causes "uploadUpload" */
        .stFileUploader input[type="file"] {
            opacity: 0 !important;
            position: absolute !important;
            width: 0 !important;
            height: 0 !important;
        }
        input[type="file"]::file-selector-button {
            display: none !important;
        }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a3d8f 0%, #1565c0 100%) !important;
        }

        /* ── Sidebar navigation page links ── */
        [data-testid="stSidebarNav"] {
            background: transparent !important;
            overflow: visible !important;
        }
        [data-testid="stSidebarNavItems"] {
            overflow: visible !important;
        }
        [data-testid="stSidebarNavLink"] {
            color: #ffffff !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.95rem !important;
            font-weight: 500 !important;
            border-radius: 6px !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }
        [data-testid="stSidebarNavLink"]:hover {
            background-color: rgba(255,255,255,0.15) !important;
            color: #ffffff !important;
        }
        [data-testid="stSidebarNavLink"][aria-current="page"] {
            background-color: rgba(255,255,255,0.25) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        [data-testid="stSidebarNavLink"] span,
        [data-testid="stSidebarNavLink"] p,
        [data-testid="stSidebarNavLink"] div {
            color: #ffffff !important;
            overflow: visible !important;
            white-space: nowrap !important;
        }

        /* ── Sidebar text, labels, headers ── */
        [data-testid="stSidebar"] * {
            color: #ffffff !important;
            font-family: 'Inter', sans-serif !important;
        }
        [data-testid="stSidebar"] input {
            background-color: rgba(255,255,255,0.15) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255,255,255,0.4) !important;
            border-radius: 6px !important;
        }
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
            background-color: rgba(255,255,255,0.15) !important;
        }
        [data-testid="stSidebar"] label {
            color: #cce0ff !important;
            font-weight: 500 !important;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #ffffff !important;
        }

        /* ── Sidebar collapse/expand button ── */
        [data-testid="collapsedControl"] {
            background-color: #1565c0 !important;
            border-radius: 0 8px 8px 0 !important;
        }

        /* Hide the icon name text (shows when Material Symbols font fails to load) */
        span.material-symbols-rounded,
        span.material-symbols-outlined,
        span[class*="material-symbols"] {
            font-size: 0 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 24px !important;
            height: 24px !important;
            overflow: hidden !important;
        }

        /* Replace with SVG double-left arrow for header collapse button */
        header span.material-symbols-rounded::before,
        header span.material-symbols-outlined::before,
        header span[class*="material-symbols"]::before {
            content: "" !important;
            display: inline-block !important;
            width: 22px !important;
            height: 22px !important;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23555555'%3E%3Cpath d='M17.59 18L19 16.59 14.42 12 19 7.41 17.59 6l-6 6z'/%3E%3Cpath d='M11 18l1.41-1.41L7.83 12l4.58-4.59L11 6l-6 6z'/%3E%3C/svg%3E") !important;
            background-repeat: no-repeat !important;
            background-position: center !important;
            background-size: contain !important;
        }

        /* Replace with SVG double-right arrow for sidebar expand button */
        [data-testid="collapsedControl"] span.material-symbols-rounded::before,
        [data-testid="collapsedControl"] span.material-symbols-outlined::before,
        [data-testid="collapsedControl"] span[class*="material-symbols"]::before {
            content: "" !important;
            display: inline-block !important;
            width: 22px !important;
            height: 22px !important;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ffffff'%3E%3Cpath d='M6.41 6L5 7.41 9.58 12 5 16.59 6.41 18l6-6z'/%3E%3Cpath d='M13 6l-1.41 1.41L16.17 12l-4.58 4.59L13 18l6-6z'/%3E%3C/svg%3E") !important;
            background-repeat: no-repeat !important;
            background-position: center !important;
            background-size: contain !important;
        }

        /* ── Groq API Key input — white box with blue text ── */
        [data-testid="stSidebar"] input[type="password"],
        [data-testid="stSidebar"] input[type="text"] {
            background-color: #ffffff !important;
            color: #1565c0 !important;
            border: 2px solid rgba(255,255,255,0.6) !important;
            border-radius: 6px !important;
        }
        [data-testid="stSidebar"] input[type="password"]::placeholder,
        [data-testid="stSidebar"] input[type="text"]::placeholder {
            color: #1565c0 !important;
            opacity: 0.75 !important;
        }

        /* ── Buttons ── */
        .stButton > button {
            background-color: #ffffff !important;
            color: #1565c0 !important;
            border: 2px solid #1565c0 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.92rem !important;
            transition: background-color 0.2s, color 0.2s, box-shadow 0.2s;
        }
        .stButton > button:hover {
            background-color: #1565c0 !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(21,101,192,0.35) !important;
        }
        .stButton > button[kind="primary"] {
            background-color: #1565c0 !important;
            color: #ffffff !important;
            border: none !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #0a3d8f !important;
        }

        /* ── Download buttons ── */
        .stDownloadButton > button {
            background-color: #ffffff !important;
            color: #1565c0 !important;
            border: 2px solid #1565c0 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
        .stDownloadButton > button:hover {
            background-color: #1565c0 !important;
            color: #ffffff !important;
        }

        /* ── Metric boxes ── */
        [data-testid="stMetric"] {
            background-color: #e8f0fe;
            border-left: 4px solid #1565c0;
            border-radius: 8px;
            padding: 0.7rem 1rem;
        }
        [data-testid="stMetricLabel"] {
            color: #1565c0 !important;
            font-weight: 600 !important;
        }
        [data-testid="stMetricValue"] {
            color: #0a3d8f !important;
            font-weight: 700 !important;
        }

        /* ── Tabs ── */
        .stTabs [data-baseweb="tab"] {
            color: #1565c0 !important;
            font-weight: 600 !important;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #1565c0 !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #0a3d8f !important;
        }

        /* ── Alerts ── */
        [data-testid="stAlert"] {
            border-radius: 8px;
        }
        [data-testid="stAlert"] p {
            color: inherit !important;
        }

        /* ── Divider ── */
        hr { border-color: #1565c0 !important; opacity: 0.2; }

        /* ── Progress bar ── */
        .stProgress > div > div > div > div {
            background-color: #1565c0 !important;
        }

        /* ── Captions ── */
        .stCaption, small {
            color: #1565c0 !important;
        }

        /* ── Dataframe headers ── */
        [data-testid="stDataFrame"] th {
            background-color: #1565c0 !important;
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
