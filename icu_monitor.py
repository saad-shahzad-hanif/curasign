import streamlit as st
import random
import time

# ============================================================
# PARAMETER LIMITS
# ============================================================
PARAMETER_LIMITS = {
    "BP_Systolic":       (90, 180),
    "BP_Diastolic":      (60, 110),
    "SpO2":              (92, 100),
    "Heart_Rate":        (60, 100),
    "Respiratory_Rate":  (12, 20),
    "Temperature":       (36.1, 37.8),
}

PARAM_UNITS = {
    "BP_Systolic":       "mmHg",
    "BP_Diastolic":      "mmHg",
    "SpO2":              "%",
    "Heart_Rate":        "bpm",
    "Respiratory_Rate":  "breaths/min",
    "Temperature":       "°C",
}

PARAM_ICONS = {
    "BP_Systolic":       "💉",
    "BP_Diastolic":      "💉",
    "SpO2":              "🫁",
    "Heart_Rate":        "❤️",
    "Respiratory_Rate":  "🌬️",
    "Temperature":       "🌡️",
}

PATIENTS = ["Patient 1", "Patient 2", "Patient 3", "Patient 4"]

# Simulate slightly different ranges per patient for realism
PATIENT_SIMULATE = {
    "Patient 1": {"BP_Systolic": (85, 195), "SpO2": (88, 99)},
    "Patient 2": {"Heart_Rate": (55, 115)},
    "Patient 3": {"BP_Diastolic": (55, 125)},
    "Patient 4": {"SpO2": (85, 98)},
}


# ============================================================
# HELPERS
# ============================================================
def simulate_value(patient, param):
    """Generate a simulated vital sign value."""
    overrides = PATIENT_SIMULATE.get(patient, {})
    if param in overrides:
        lo, hi = overrides[param]
    else:
        lo, hi = PARAMETER_LIMITS[param]
        # Add small random noise around normal range
        lo = lo * 0.95
        hi = hi * 1.05
    return round(random.uniform(lo, hi), 1)


def check_status(param, value):
    lo, hi = PARAMETER_LIMITS[param]
    if value < lo or value > hi:
        return "CRITICAL"
    # Warning zone: within 5% of limits
    margin_lo = lo + (hi - lo) * 0.05
    margin_hi = hi - (hi - lo) * 0.05
    if value < margin_lo or value > margin_hi:
        return "WARNING"
    return "NORMAL"


def status_color(status):
    return {"CRITICAL": "#fc8181", "WARNING": "#f6ad55", "NORMAL": "#48bb78"}.get(status, "#48bb78")


def status_bg(status):
    return {"CRITICAL": "#fff5f5", "WARNING": "#fffbeb", "NORMAL": "#f0fff4"}.get(status, "#f0fff4")


def status_icon(status):
    return {"CRITICAL": "🔴", "WARNING": "⚠️", "NORMAL": "✅"}.get(status, "✅")


# ============================================================
# INITIALISE SESSION STATE
# ============================================================
def init_state():
    if "icu_data" not in st.session_state:
        st.session_state.icu_data = {
            p: {param: simulate_value(p, param) for param in PARAMETER_LIMITS}
            for p in PATIENTS
        }
    if "alarm_silenced" not in st.session_state:
        st.session_state.alarm_silenced = False
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False


def refresh_data():
    st.session_state.icu_data = {
        p: {param: simulate_value(p, param) for param in PARAMETER_LIMITS}
        for p in PATIENTS
    }
    st.session_state.alarm_silenced = False


# ============================================================
# PATIENT CARD
# ============================================================
def render_patient_card(patient):
    data   = st.session_state.icu_data[patient]
    params = PARAMETER_LIMITS.keys()

    # Determine overall patient status
    statuses  = [check_status(p, data[p]) for p in params]
    is_crit   = "CRITICAL" in statuses
    is_warn   = "WARNING"  in statuses and not is_crit
    overall   = "CRITICAL" if is_crit else ("WARNING" if is_warn else "NORMAL")
    card_border = status_color(overall)
    card_bg     = "#fff5f5" if is_crit else ("#fffdf0" if is_warn else "white")

    st.markdown(f"""
<div style="background:{card_bg};border:2px solid {card_border};border-radius:18px;
            padding:1rem 1.1rem;box-shadow:0 4px 20px rgba(0,0,0,0.07);margin-bottom:0.5rem;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem;">
    <div style="font-family:Nunito,sans-serif;font-size:1rem;font-weight:900;color:#1a1a2e;">
      🛏️ {patient}
    </div>
    <div style="background:{status_bg(overall)};color:{card_border};
                border-radius:20px;padding:3px 12px;font-size:0.72rem;font-weight:800;">
      {status_icon(overall)} {overall}
    </div>
  </div>
""", unsafe_allow_html=True)

    # Two columns of params inside the card
    col1, col2 = st.columns(2)
    param_list = list(params)
    for i, param in enumerate(param_list):
        val    = data[param]
        status = check_status(param, val)
        color  = status_color(status)
        lo, hi = PARAMETER_LIMITS[param]
        unit   = PARAM_UNITS[param]
        icon   = PARAM_ICONS[param]
        col    = col1 if i % 2 == 0 else col2

        with col:
            st.markdown(f"""
<div style="background:white;border-left:4px solid {color};border-radius:10px;
            padding:0.5rem 0.7rem;margin-bottom:0.5rem;
            box-shadow:0 2px 8px rgba(0,0,0,0.05);">
  <div style="font-size:0.68rem;color:#888;text-transform:uppercase;letter-spacing:1px;">
    {icon} {param.replace('_',' ')}
  </div>
  <div style="font-size:1.1rem;font-weight:900;color:{color};font-family:Nunito,sans-serif;">
    {val} <span style="font-size:0.7rem;font-weight:600;color:#aaa;">{unit}</span>
  </div>
  <div style="font-size:0.65rem;color:#bbb;">
    Normal: {lo}–{hi} {unit}
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# ALARM BANNER
# ============================================================
def render_alarm_banner():
    all_data = st.session_state.icu_data
    critical_patients = []
    for p in PATIENTS:
        for param, val in all_data[p].items():
            if check_status(param, val) == "CRITICAL":
                critical_patients.append(p)
                break

    if critical_patients and not st.session_state.alarm_silenced:
        names = ", ".join(critical_patients)
        st.markdown(f"""
<div style="background:#fff5f5;border:2px solid #fc8181;border-radius:14px;
            padding:0.9rem 1.5rem;margin-bottom:1.5rem;
            animation:pulse 1s infinite;text-align:center;">
  <span style="font-size:1.1rem;font-weight:900;color:#c53030;font-family:Nunito,sans-serif;">
    🚨 CRITICAL ALARM — {names} require immediate attention!
  </span>
</div>
<style>
@keyframes pulse {{
  0%  {{ box-shadow: 0 0 0 0 rgba(252,129,129,0.5); }}
  70% {{ box-shadow: 0 0 0 10px rgba(252,129,129,0); }}
  100%{{ box-shadow: 0 0 0 0 rgba(252,129,129,0); }}
}}
</style>
""", unsafe_allow_html=True)
        return True
    elif not critical_patients:
        st.markdown("""
<div style="background:#f0fff4;border:2px solid #68d391;border-radius:14px;
            padding:0.9rem 1.5rem;margin-bottom:1.5rem;text-align:center;">
  <span style="font-size:1rem;font-weight:800;color:#276749;font-family:Nunito,sans-serif;">
    ✅ All patients stable
  </span>
</div>
""", unsafe_allow_html=True)
    return False


# ============================================================
# SUMMARY TABLE
# ============================================================
def render_summary_table():
    rows = ""
    for p in PATIENTS:
        for param, val in st.session_state.icu_data[p].items():
            status = check_status(param, val)
            color  = status_color(status)
            bg     = status_bg(status)
            lo, hi = PARAMETER_LIMITS[param]
            unit   = PARAM_UNITS[param]
            rows += f"""
<tr>
  <td style="padding:7px 10px;font-size:0.82rem;border-bottom:1px solid #f0f0f0;font-weight:700;">{p}</td>
  <td style="padding:7px 10px;font-size:0.82rem;border-bottom:1px solid #f0f0f0;">{PARAM_ICONS[param]} {param.replace('_',' ')}</td>
  <td style="padding:7px 10px;font-size:0.82rem;font-weight:800;color:{color};border-bottom:1px solid #f0f0f0;">{val} {unit}</td>
  <td style="padding:7px 10px;font-size:0.75rem;color:#888;border-bottom:1px solid #f0f0f0;">{lo}–{hi} {unit}</td>
  <td style="padding:7px 10px;border-bottom:1px solid #f0f0f0;">
    <span style="background:{bg};color:{color};padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:800;">
      {status_icon(status)} {status}
    </span>
  </td>
</tr>"""

    st.markdown(f"""
<div style="background:white;border-radius:18px;padding:1.2rem;box-shadow:0 4px 20px rgba(0,0,0,0.06);overflow-x:auto;">
  <div style="font-size:0.8rem;font-weight:800;letter-spacing:1px;text-transform:uppercase;
              color:#667eea;margin-bottom:0.8rem;">📋 All Vitals — Quick Reference</div>
  <table style="width:100%;border-collapse:collapse;">
    <thead>
      <tr>
        <th style="font-size:0.73rem;font-weight:700;color:#555;text-transform:uppercase;
                   padding:7px 10px;border-bottom:2px solid #eee;text-align:left;">Patient</th>
        <th style="font-size:0.73rem;font-weight:700;color:#555;text-transform:uppercase;
                   padding:7px 10px;border-bottom:2px solid #eee;text-align:left;">Parameter</th>
        <th style="font-size:0.73rem;font-weight:700;color:#555;text-transform:uppercase;
                   padding:7px 10px;border-bottom:2px solid #eee;text-align:left;">Value</th>
        <th style="font-size:0.73rem;font-weight:700;color:#555;text-transform:uppercase;
                   padding:7px 10px;border-bottom:2px solid #eee;text-align:left;">Normal Range</th>
        <th style="font-size:0.73rem;font-weight:700;color:#555;text-transform:uppercase;
                   padding:7px 10px;border-bottom:2px solid #eee;text-align:left;">Status</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>
""", unsafe_allow_html=True)


# ============================================================
# MAIN PAGE
# ============================================================
def show():
    st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] { background: #f0f4ff; font-family: Nunito, sans-serif; }
.stApp { background: #f0f4ff; }
.block-container { padding: 1.5rem 2rem !important; max-width: 1400px; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

    init_state()

    # ── Header ──
    st.markdown("""
<div style="background:linear-gradient(135deg,#e53e3e,#c53030);border-radius:20px;
            padding:1.3rem 2rem;margin-bottom:1.5rem;display:flex;align-items:center;
            gap:14px;box-shadow:0 8px 32px rgba(229,62,62,0.3);">
  <span style="font-size:2.2rem;">🏥</span>
  <div>
    <div style="font-family:Nunito,sans-serif;font-size:1.8rem;font-weight:900;color:white;margin:0;">
      ICU Central Monitor
    </div>
    <div style="font-size:0.85rem;color:rgba(255,255,255,0.75);margin:0;">
      Real-time patient vital signs dashboard
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Controls ──
    col_refresh, col_silence, col_auto, col_spacer = st.columns([1, 1, 1, 3])

    with col_refresh:
        if st.button("🔄 Refresh Vitals", use_container_width=True):
            refresh_data()
            st.rerun()

    with col_silence:
        if st.button("🔕 Silence Alarm", use_container_width=True):
            st.session_state.alarm_silenced = True
            st.rerun()

    with col_auto:
        auto = st.toggle("⚡ Auto-refresh (5s)", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Alarm Banner ──
    render_alarm_banner()

    # ── 4 Patient Cards in 2x2 grid ──
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    with row1_col1:
        render_patient_card("Patient 1")
    with row1_col2:
        render_patient_card("Patient 2")
    with row2_col1:
        render_patient_card("Patient 3")
    with row2_col2:
        render_patient_card("Patient 4")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Summary Table ──
    render_summary_table()

    st.markdown("""
<div style="text-align:center;font-size:0.75rem;color:#aaa;margin-top:1.5rem;padding:1rem;">
  ⚠️ This dashboard uses simulated data. Connect real medical devices for clinical use.
</div>
""", unsafe_allow_html=True)

    # ── Auto-refresh ──
    if st.session_state.auto_refresh:
        time.sleep(5)
        refresh_data()
        st.rerun()


if __name__ == "__main__":
    st.set_page_config(page_title="ICU Monitor", page_icon="🏥", layout="wide")
    show()
