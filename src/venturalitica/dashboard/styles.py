try:
    import streamlit as st
except ImportError:
    raise ImportError(
        "streamlit is required for the dashboard. "
        "Install with: pip install venturalitica[dashboard]"
    )


def apply_saas_theme():
    """Applies the Venturalitica navy+gold brand identity to Streamlit.

    Design tokens are aligned with the SaaS app (venturalitica/src/app/globals.css):
    - Primary Navy:  #0b3260
    - Foreground:    #082c5b
    - Accent Gold:   #ebb024
    - Background:    #fefefd
    - Card:          #ffffff
    - Border:        #d1d5db
    - Destructive:   #d64545
    - Radius:        0.625rem (10px)
    """

    st.markdown(
        """
    <style>
        /* ============================================================
           VENTURALITICA BRAND THEME — Navy + Gold
           Matches SaaS app visual identity
           Updated for Streamlit ≥ 1.54 DOM structure
           ============================================================ */

        /* --- FONTS --- */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Condensed:wght@400;600;700&family=Roboto+Mono:wght@400;500&display=swap');

        /* --- BASE TYPOGRAPHY --- */
        html, body, [class*="css"],
        .stApp, [data-testid="stMain"] {
            font-family: 'Roboto', ui-sans-serif, system-ui, -apple-system, sans-serif !important;
            color: #082c5b !important; /* foreground navy */
        }

        /* Headings use Roboto Condensed like the SaaS app */
        h1, h2, h3, h4, h5, h6,
        [data-testid="stHeading"],
        [data-testid="stMarkdown"] h1,
        [data-testid="stMarkdown"] h2,
        [data-testid="stMarkdown"] h3,
        [data-testid="stMarkdown"] h4 {
            font-family: 'Roboto Condensed', 'Roboto', sans-serif !important;
            font-weight: 700 !important;
            color: #0b3260 !important; /* primary navy */
            letter-spacing: 0.01em;
        }

        h1 { font-size: 1.75rem !important; }
        h2 { font-size: 1.35rem !important; }
        h3 { font-size: 1.15rem !important; }
        h4 { font-size: 1.05rem !important; font-weight: 600 !important; }

        /* Sub-headings (h4 in mission cards) */
        [data-testid="stMarkdown"] h4 {
            color: #0b3260 !important;
            border-bottom: 2px solid #ebb024;
            padding-bottom: 0.3rem;
            margin-bottom: 0.75rem;
        }

        /* --- BACKGROUND --- */
        .stApp, [data-testid="stAppViewContainer"] {
            background-color: #fefefd !important; /* near-white */
        }

        /* Remove default Streamlit header bar background */
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }

        /* --- LAYOUT & CONTAINERS --- */
        .block-container, [data-testid="stMainBlockContainer"] {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 100% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* --- CARD CONTAINERS (st.container(border=True)) ---
           Streamlit 1.54+ renders bordered containers as stVerticalBlock
           inside stLayoutWrapper inside stColumn's stVerticalBlock.
           The bordered block has emotion class with border styles.
           Target: stColumn stLayoutWrapper > stVerticalBlock (the nested one). */
        [data-testid="stColumn"] [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] {
            background-color: #ffffff !important;
            border: 1px solid #d1d5db !important;
            border-radius: 0.75rem !important;
            box-shadow: 0 6px 20px rgba(9, 30, 66, 0.08) !important;
            padding: 1.25rem !important;
            transition: box-shadow 0.2s ease, border-color 0.2s ease;
        }
        [data-testid="stColumn"] [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"]:hover {
            box-shadow: 0 8px 28px rgba(9, 30, 66, 0.12) !important;
            border-color: #ebb024 !important; /* gold border on hover */
        }

        /* --- SIDEBAR --- */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b3260 0%, #082c5b 100%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        /* Sidebar text → white */
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] *,
        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"],
        [data-testid="stSidebarUserContent"] * {
            color: #fefefd !important;
        }

        /* Sidebar headings → gold */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebarUserContent"] h3,
        [data-testid="stSidebar"] [data-testid="stMarkdown"] h3 {
            color: #ebb024 !important; /* gold headings */
            font-family: 'Roboto Condensed', sans-serif !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em;
        }

        /* Sidebar caption text */
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        [data-testid="stSidebar"] small,
        [data-testid="stSidebar"] [data-testid="stText"] {
            color: rgba(254, 254, 253, 0.7) !important;
        }

        /* Sidebar divider */
        [data-testid="stSidebar"] hr {
            border-color: rgba(235, 176, 36, 0.25) !important;
        }

        /* Sidebar radio buttons */
        [data-testid="stSidebar"] [data-testid="stRadio"] label {
            color: #fefefd !important;
            font-size: 0.9rem !important;
            padding: 0.4rem 0.6rem !important;
            border-radius: 0.5rem !important;
            transition: background-color 0.15s ease;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background-color: rgba(235, 176, 36, 0.12) !important;
        }
        /* Active radio option — Streamlit uses checked attribute on input */
        [data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"]:checked + div,
        [data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"]:checked ~ * {
            color: #ebb024 !important;
            font-weight: 500 !important;
        }

        /* Sidebar selectbox */
        [data-testid="stSidebar"] [data-testid="stSelectbox"] label,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
            color: rgba(254, 254, 253, 0.8) !important;
        }

        /* --- BUTTONS ---
           Streamlit 1.54 default st.button() renders as kind="secondary"
           with data-testid="stBaseButton-secondary". We style these as
           primary (navy bg) since our dashboard uses them as CTAs. */
        [data-testid="stButton"] button,
        [data-testid="stBaseButton-secondary"] {
            background-color: #0b3260 !important; /* primary navy */
            color: #fefefd !important;
            border: none !important;
            border-radius: 0.5rem !important;
            font-family: 'Roboto', sans-serif !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            padding: 0.5rem 1.25rem !important;
            transition: all 0.2s ease !important;
            letter-spacing: 0.01em;
            cursor: pointer;
        }
        [data-testid="stButton"] button:hover,
        [data-testid="stBaseButton-secondary"]:hover {
            background-color: #082c5b !important;
            box-shadow: 0 4px 12px rgba(11, 50, 96, 0.3) !important;
            transform: translateY(-1px);
        }
        [data-testid="stButton"] button:active,
        [data-testid="stBaseButton-secondary"]:active {
            transform: translateY(0);
            box-shadow: 0 2px 6px rgba(11, 50, 96, 0.2) !important;
        }
        /* Focus ring → gold */
        [data-testid="stButton"] button:focus-visible {
            outline: 2px solid #ebb024 !important;
            outline-offset: 2px;
        }

        /* Explicit primary buttons (st.button(type="primary")) */
        [data-testid="stBaseButton-primary"] {
            background-color: #ebb024 !important; /* gold for primary */
            color: #0b3260 !important;
            border: none !important;
            font-weight: 600 !important;
        }
        [data-testid="stBaseButton-primary"]:hover {
            background-color: #d4a020 !important;
            box-shadow: 0 4px 12px rgba(235, 176, 36, 0.3) !important;
        }

        /* Sidebar/header utility buttons — keep subtle */
        [data-testid="stBaseButton-headerNoPadding"],
        [data-testid="stBaseButton-header"],
        [data-testid="stBaseButton-elementToolbar"],
        [data-testid="stSidebarCollapseButton"] button {
            background-color: transparent !important;
            color: inherit !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0.25rem !important;
        }
        [data-testid="stBaseButton-headerNoPadding"]:hover,
        [data-testid="stBaseButton-header"]:hover,
        [data-testid="stBaseButton-elementToolbar"]:hover {
            background-color: rgba(11, 50, 96, 0.06) !important;
            transform: none;
            box-shadow: none !important;
        }

        /* --- FORM ELEMENTS --- */
        .stTextInput input,
        .stTextArea textarea,
        [data-testid="stSelectbox"] > div > div,
        .stMultiSelect > div > div,
        .stNumberInput input {
            border-radius: 0.5rem !important;
            border: 1px solid #d1d5db !important;
            background-color: #f4f6f8 !important;
            color: #082c5b !important;
            font-family: 'Roboto', sans-serif !important;
        }
        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus {
            border-color: #0b3260 !important;
            box-shadow: 0 0 0 2px rgba(11, 50, 96, 0.15) !important;
            background-color: #ffffff !important;
        }

        /* Labels */
        [data-testid="stWidgetLabel"] label,
        [data-testid="stWidgetLabel"] p,
        .stTextInput label,
        .stTextArea label,
        [data-testid="stSelectbox"] label,
        .stMultiSelect label,
        .stNumberInput label,
        [data-testid="stRadio"] label,
        .stCheckbox label {
            color: #082c5b !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
        }

        /* --- TABS (Phase 3 sub-tabs) --- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0 !important;
            border-bottom: 2px solid #e6e7e8 !important;
        }
        .stTabs [data-baseweb="tab"] {
            font-family: 'Roboto Condensed', sans-serif !important;
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            color: #4e6584 !important;
            padding: 0.6rem 1.2rem !important;
            border-bottom: 3px solid transparent !important;
            transition: color 0.15s ease, border-color 0.15s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #0b3260 !important;
        }
        .stTabs [aria-selected="true"] {
            color: #0b3260 !important;
            border-bottom-color: #ebb024 !important; /* gold active indicator */
            font-weight: 700 !important;
        }
        /* Tab highlight bar override */
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #ebb024 !important;
        }

        /* --- ALERTS / CALLOUTS ---
           Streamlit 1.54 uses:
             stAlert > stAlertContainer > stAlertContentInfo/Success/Warning/Error
           (changed from stNotificationContent*) */

        /* Alert container outer wrapper */
        [data-testid="stAlertContainer"] {
            border-radius: 0.625rem !important;
            overflow: hidden;
        }

        /* st.info → light navy bg */
        [data-testid="stAlertContentInfo"] {
            background-color: rgba(11, 50, 96, 0.06) !important;
            border-left: 4px solid #0b3260 !important;
            color: #082c5b !important;
            border-radius: 0.625rem !important;
            padding: 0.75rem 1rem !important;
        }

        /* st.success → green with navy text */
        [data-testid="stAlertContentSuccess"] {
            background-color: rgba(34, 197, 94, 0.08) !important;
            border-left: 4px solid #22c55e !important;
            color: #082c5b !important;
            border-radius: 0.625rem !important;
            padding: 0.75rem 1rem !important;
        }

        /* st.warning → gold-tinted */
        [data-testid="stAlertContentWarning"] {
            background-color: rgba(235, 176, 36, 0.1) !important;
            border-left: 4px solid #ebb024 !important;
            color: #082c5b !important;
            border-radius: 0.625rem !important;
            padding: 0.75rem 1rem !important;
        }

        /* st.error → brand destructive */
        [data-testid="stAlertContentError"] {
            background-color: rgba(214, 69, 69, 0.08) !important;
            border-left: 4px solid #d64545 !important;
            color: #082c5b !important;
            border-radius: 0.625rem !important;
            padding: 0.75rem 1rem !important;
        }

        /* Alert text inherits foreground navy */
        [data-testid="stAlertContentInfo"] *,
        [data-testid="stAlertContentSuccess"] *,
        [data-testid="stAlertContentWarning"] *,
        [data-testid="stAlertContentError"] * {
            color: #082c5b !important;
        }

        /* --- EXPANDERS (used in compliance map & policy view) --- */
        [data-testid="stExpander"] {
            border: 1px solid #d1d5db !important;
            border-radius: 0.625rem !important;
            background-color: #ffffff !important;
            overflow: hidden;
        }
        [data-testid="stExpander"] summary {
            font-family: 'Roboto Condensed', sans-serif !important;
            font-weight: 600 !important;
            color: #0b3260 !important;
            padding: 0.75rem 1rem !important;
        }
        [data-testid="stExpander"] summary:hover {
            background-color: rgba(11, 50, 96, 0.03) !important;
        }

        /* --- METRICS (st.metric) --- */
        [data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e6e7e8;
            border-radius: 0.625rem;
            padding: 1rem 1.25rem;
            box-shadow: 0 2px 8px rgba(9, 30, 66, 0.05);
        }
        [data-testid="stMetric"] [data-testid="stMetricLabel"] {
            color: #4e6584 !important;
            font-family: 'Roboto Condensed', sans-serif !important;
            font-size: 0.8rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.04em !important;
        }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #0b3260 !important;
            font-family: 'Roboto Condensed', sans-serif !important;
            font-weight: 700 !important;
        }
        /* Positive delta → green, negative → red (keep defaults but ensure colors) */
        [data-testid="stMetric"] [data-testid="stMetricDelta"] svg {
            fill: currentColor;
        }

        /* --- CAPTIONS --- */
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] * {
            color: #4e6584 !important; /* muted navy */
            font-size: 0.82rem !important;
        }

        /* --- BREADCRUMB / Phase indicator --- */
        [data-testid="stCaptionContainer"] strong {
            color: #0b3260 !important;
        }

        /* --- DATAFRAME / TABLE --- */
        [data-testid="stDataFrame"] {
            border: 1px solid #d1d5db !important;
            border-radius: 0.625rem !important;
            overflow: hidden;
        }
        [data-testid="stDataFrame"] th {
            background-color: #0b3260 !important;
            color: #fefefd !important;
            font-family: 'Roboto Condensed', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }

        /* --- PROGRESS BAR --- */
        .stProgress > div > div {
            background-color: #ebb024 !important; /* gold progress */
        }
        .stProgress > div {
            background-color: rgba(11, 50, 96, 0.08) !important;
        }

        /* --- SPINNERS --- */
        .stSpinner > div {
            border-top-color: #ebb024 !important;
        }

        /* --- LINKS --- */
        a, a:visited {
            color: #0b3260 !important;
            text-decoration: underline;
            text-decoration-color: rgba(235, 176, 36, 0.4);
            text-underline-offset: 2px;
        }
        a:hover {
            color: #ebb024 !important;
            text-decoration-color: #ebb024;
        }

        /* --- CODE BLOCKS --- */
        code, .stCode, pre {
            font-family: 'Roboto Mono', ui-monospace, monospace !important;
            font-size: 0.85rem !important;
        }
        code {
            background-color: rgba(11, 50, 96, 0.06) !important;
            color: #0b3260 !important;
            padding: 0.15rem 0.4rem !important;
            border-radius: 0.25rem !important;
        }

        /* --- JSON VIEWER --- */
        [data-testid="stJson"] {
            border: 1px solid #d1d5db !important;
            border-radius: 0.625rem !important;
            background-color: #fafafc !important;
        }

        /* --- TOOLTIP / HELP ICONS --- */
        [data-testid="stTooltipIcon"] svg {
            color: #4e6584 !important;
        }

        /* --- DIVIDER --- */
        hr {
            border-color: #e6e7e8 !important;
        }

        /* --- SCROLLBAR (webkit) --- */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #f4f6f8;
        }
        ::-webkit-scrollbar-thumb {
            background: #cbd6ea;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #0b3260;
        }

        /* --- BADGE-LIKE ELEMENTS (used in compliance map) --- */
        .compliance-pass {
            background-color: rgba(34, 197, 94, 0.1);
            color: #16a34a;
            padding: 0.2rem 0.6rem;
            border-radius: 1rem;
            font-size: 0.8rem;
            font-weight: 500;
        }
        .compliance-fail {
            background-color: rgba(214, 69, 69, 0.1);
            color: #d64545;
            padding: 0.2rem 0.6rem;
            border-radius: 1rem;
            font-size: 0.8rem;
            font-weight: 500;
        }
        .compliance-pending {
            background-color: rgba(235, 176, 36, 0.12);
            color: #b8860b;
            padding: 0.2rem 0.6rem;
            border-radius: 1rem;
            font-size: 0.8rem;
            font-weight: 500;
        }

        /* --- HEADING ACTION ELEMENTS (anchor links) --- */
        [data-testid="stHeaderActionElements"] {
            display: none !important; /* Hide anchor link clutter */
        }

    </style>
    """,
        unsafe_allow_html=True,
    )


def card_container():
    """
    Returns a Streamlit styled container that looks like a branded card.
    Uses st.container(border=True) which gets styled by the theme CSS above.

    Usage:
        with card_container():
            st.write("Content inside card")
    """
    return st.container(border=True)
