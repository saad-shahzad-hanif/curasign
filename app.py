import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
from PIL import Image
import json
import io
import base64
from dotenv import load_dotenv
import os
load_dotenv()


# ============================================================
# MASTER PROMPT
# ============================================================
MASTER_PROMPT = """
You are a medical report explainer.
Read the medical report image and return ONLY this JSON:

{
  "patient_name": "Name or 'Not Mentioned'",
  "report_type": "e.g. Blood Test, CBC, LFT",
  "summary": "2-3 line simple English summary",
  "summary_urdu": "2-3 line simple Urdu summary",
  "findings": [
    {
      "test_name": "Test name",
      "value": "Patient value with unit",
      "normal_range": "Normal range",
      "status": "Normal or High or Low or Abnormal",
      "explanation": "Simple English explanation",
      "explanation_urdu": "Simple Urdu explanation in Urdu script"
    }
  ],
  "doctor_advice": "Simple advice in English",
  "doctor_advice_urdu": "Simple advice in Urdu script",
  "urgent": true or false
}

RULE: Return ONLY valid JSON. No extra text. No backticks.
IMPORTANT: explanation_urdu, summary_urdu, and doctor_advice_urdu must be in proper Urdu script (not Roman Urdu).
"""

# ============================================================
# GROQ BACKEND
# ============================================================
def get_text(image_bytes: bytes, api_key: str):
    try:
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        image = Image.open(io.BytesIO(image_bytes))
        fmt = image.format.lower() if image.format else "jpeg"
        media_type = f"image/{fmt}"
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64_image}"}},
                    {"type": "text", "text": MASTER_PROMPT}
                ]
            }],
            max_tokens=1500,
            temperature=0.1
        )
        raw = response.choices[0].message.content
        raw = raw.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw), None
    except json.JSONDecodeError:
        return None, "AI did not return valid JSON. Please try again."
    except Exception as e:
        return None, str(e)


# ============================================================
# HELPERS
# ============================================================
def get_color(status):
    s = status.lower()
    if s == "normal":  return "#48bb78"
    if s == "high":    return "#fc8181"
    if s == "low":     return "#f6ad55"
    return "#fc8181"

def get_note_style(status):
    s = status.lower()
    if s == "normal": return "#f0fff4", "#276749", "✅"
    if s == "high":   return "#fff5f5", "#c53030", "🔴"
    if s == "low":    return "#fffbeb", "#b7791f", "⚠️"
    return "#fff5f5", "#c53030", "⚠️"

def get_badge_style(status):
    s = status.lower()
    if s == "normal": return "#f0fff4", "#276749"
    if s == "high":   return "#fff5f5", "#c53030"
    if s == "low":    return "#fffbeb", "#b7791f"
    return "#fff5f5", "#c53030"

def get_dot_color(status):
    s = status.lower()
    if s == "normal": return "#48bb78"
    if s == "high":   return "#fc8181"
    return "#f6ad55"

def calc_percent(value_str, range_str, status):
    try:
        val = float(''.join(c for c in value_str if c.isdigit() or c == '.'))
        parts = range_str.replace('–', '-').replace('to', '-').split('-')
        nums = []
        for p in parts:
            clean = ''.join(c for c in p.strip() if c.isdigit() or c == '.')
            if clean:
                nums.append(float(clean))
        if len(nums) >= 2:
            lo, hi = nums[0], nums[-1]
            pct = int((val - lo) / (hi - lo) * 60 + 20)
            return min(max(pct, 8), 97)
    except:
        pass
    s = status.lower()
    if s == "normal": return 65
    if s == "high":   return 88
    return 25

def make_ring(pct, color, label):
    r = 45
    circ = 2 * 3.14159 * r
    dash = (pct / 100) * circ
    return f"""<svg width="120" height="120" viewBox="0 0 120 120">
  <circle cx="60" cy="60" r="{r}" fill="none" stroke="#e8e8e8" stroke-width="11"/>
  <circle cx="60" cy="60" r="{r}" fill="none" stroke="{color}" stroke-width="11"
          stroke-dasharray="{dash:.1f} {circ:.1f}" stroke-linecap="round"
          transform="rotate(-90 60 60)"/>
  <text x="60" y="55" text-anchor="middle" font-family="Nunito,sans-serif"
        font-size="19" font-weight="900" fill="{color}">{pct}%</text>
  <text x="60" y="74" text-anchor="middle" font-family="Nunito,sans-serif"
        font-size="10" font-weight="700" fill="{color}">{label}</text>
</svg>"""


# ============================================================
# DISPLAY DASHBOARD — uses components.html to avoid render bug
# ============================================================
def display_dashboard(data):
    findings = data.get("findings", [])
    urgent   = data.get("urgent", False)

    # ── Banner + Patient info (safe, no f-string HTML loops) ──
    banner_color = "#fff5f5" if urgent else "#f0fff4"
    banner_border = "#fc8181" if urgent else "#68d391"
    banner_text_color = "#c53030" if urgent else "#276749"
    banner_msg = "🚨 URGENT — Please See a Doctor Immediately" if urgent else "✅ Overall Status: Normal — Keep maintaining a healthy lifestyle!"

    st.markdown(f"""
<div style="display:flex;gap:1rem;margin-bottom:1rem;flex-wrap:wrap;">
  <div style="background:white;border-radius:12px;padding:0.7rem 1.2rem;
              box-shadow:0 2px 10px rgba(0,0,0,0.06);flex:1;min-width:180px;">
    <div style="font-size:0.7rem;color:#888;text-transform:uppercase;letter-spacing:1px;">Patient</div>
    <div style="font-family:Nunito,sans-serif;font-weight:800;font-size:1rem;color:#1a1a2e;">
      👤 {data.get('patient_name','N/A')}
    </div>
  </div>
  <div style="background:white;border-radius:12px;padding:0.7rem 1.2rem;
              box-shadow:0 2px 10px rgba(0,0,0,0.06);flex:1;min-width:180px;">
    <div style="font-size:0.7rem;color:#888;text-transform:uppercase;letter-spacing:1px;">Report Type</div>
    <div style="font-family:Nunito,sans-serif;font-weight:800;font-size:1rem;color:#1a1a2e;">
      🏥 {data.get('report_type','N/A')}
    </div>
  </div>
</div>
<div style="background:{banner_color};border:2px solid {banner_border};border-left:5px solid {banner_border};
            border-radius:14px;padding:1rem 1.5rem;margin-bottom:1.5rem;
            font-family:Nunito,sans-serif;font-weight:800;color:{banner_text_color};font-size:1rem;">
  {banner_msg}
</div>
""", unsafe_allow_html=True)

    # ── Ring Cards via components.html ──
    cards_html = ""
    col_w = max(220, 900 // max(len(findings), 1))
    for f in findings:
        status = f.get("status", "Normal")
        color  = get_color(status)
        nbg, nfg, nicon = get_note_style(status)
        pct    = calc_percent(f.get("value",""), f.get("normal_range",""), status)
        ring   = make_ring(pct, color, status)
        short_exp = f.get('explanation','')[:60] + "..." if len(f.get('explanation','')) > 60 else f.get('explanation','')

        cards_html += f"""
<div style="background:white;border-radius:18px;padding:1.2rem 0.8rem;text-align:center;
            box-shadow:0 4px 20px rgba(0,0,0,0.07);min-width:200px;flex:1;max-width:260px;">
  <div style="font-family:Nunito,sans-serif;font-size:0.75rem;font-weight:800;
              letter-spacing:1px;text-transform:uppercase;color:{color};margin-bottom:4px;">
    {f.get('test_name','')}
  </div>
  <div style="font-size:0.7rem;color:#888;margin-bottom:0.8rem;line-height:1.3;">
    {short_exp}
  </div>
  <div style="display:flex;justify-content:center;margin-bottom:0.7rem;">
    {ring}
  </div>
  <div style="font-family:Nunito,sans-serif;font-size:1.2rem;font-weight:800;color:#1a1a2e;">
    {f.get('value','')}
  </div>
  <div style="font-size:0.72rem;color:#999;margin-top:3px;">
    Normal Range<br>{f.get('normal_range','')}
  </div>
  <div style="margin-top:0.7rem;background:{nbg};color:{nfg};border-radius:8px;
              padding:0.4rem 0.6rem;font-size:0.72rem;font-weight:600;text-align:left;">
    {nicon} {f.get('explanation','')}
  </div>
  <div style="margin-top:0.4rem;background:#fafafa;border-radius:8px;
              padding:0.4rem 0.6rem;font-size:0.75rem;color:#555;text-align:right;
              direction:rtl;font-family:serif;line-height:1.6;">
    🇵🇰 {f.get('explanation_urdu','')}
  </div>
</div>"""

    components.html(f"""
<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:transparent;font-family:Nunito,sans-serif;">
  <div style="display:flex;flex-wrap:wrap;gap:1rem;justify-content:flex-start;">
    {cards_html}
  </div>
</body>
</html>
""", height=max(len(findings) // 4 + 1, 1) * 420)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Summary + Reference Table ──
    col_left, col_right = st.columns(2)

    with col_left:
        bullets = ""
        for f in findings:
            dc = get_dot_color(f.get("status", "Normal"))
            bullets += f"""
<div style="display:flex;align-items:flex-start;gap:8px;font-size:0.85rem;
            color:#444;margin-bottom:0.6rem;line-height:1.4;">
  <div style="width:10px;height:10px;border-radius:50%;background:{dc};
              flex-shrink:0;margin-top:4px;"></div>
  <div>
    <span>{f.get('explanation','')}</span>
    <div style="text-align:right;direction:rtl;font-family:serif;
                font-size:0.78rem;color:#666;margin-top:2px;line-height:1.5;">
      {f.get('explanation_urdu','')}
    </div>
  </div>
</div>"""

        components.html(f"""
<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:transparent;">
<div style="background:white;border-radius:18px;padding:1.4rem;
            box-shadow:0 4px 20px rgba(0,0,0,0.06);">
  <div style="font-family:Nunito,sans-serif;font-size:0.8rem;font-weight:800;
              letter-spacing:1px;text-transform:uppercase;color:#667eea;margin-bottom:0.8rem;">
    🧠 AI Analysis Summary
  </div>
  <div style="font-family:Nunito,sans-serif;font-size:0.92rem;font-weight:700;
              color:#1a1a2e;line-height:1.5;margin-bottom:0.8rem;">
    {data.get('patient_name','Patient')}, {data.get('summary','')}
  </div>
  <div style="background:#fff9f0;border-radius:8px;padding:8px 12px;margin-bottom:8px;
              font-size:0.88rem;color:#744210;text-align:right;direction:rtl;
              font-family:serif;line-height:1.7;border-right:3px solid #f6ad55;">
    🇵🇰 {data.get('summary_urdu','')}
  </div>
  {bullets}
  <div style="background:#f8f4ff;border-radius:10px;padding:0.8rem;margin-top:0.8rem;
              font-size:0.82rem;color:#553c9a;line-height:1.5;display:flex;gap:8px;">
    <span style="font-size:1.1rem;">⭐</span>
    <div>
      <strong>Recommendation:</strong><br>{data.get('doctor_advice','Please consult a doctor.')}
      <div style="margin-top:6px;padding-top:6px;border-top:1px solid #ddd;
                  text-align:right;direction:rtl;font-family:serif;
                  font-size:0.82rem;color:#553c9a;line-height:1.7;">
        🇵🇰 {data.get('doctor_advice_urdu','')}
      </div>
    </div>
  </div>
</div>
</body>
</html>
""", height=350 + len(findings) * 35)

    with col_right:
        rows = ""
        for f in findings:
            bbg, bfg = get_badge_style(f.get("status","Normal"))
            rows += f"""
<tr>
  <td style="padding:0.6rem 0.8rem;font-size:0.83rem;color:#333;
             border-bottom:1px solid #f0f0f0;">{f.get('test_name','')}</td>
  <td style="padding:0.6rem 0.8rem;font-size:0.83rem;color:#333;
             border-bottom:1px solid #f0f0f0;">{f.get('normal_range','')}</td>
  <td style="padding:0.6rem 0.8rem;font-size:0.83rem;font-weight:700;color:#1a1a2e;
             border-bottom:1px solid #f0f0f0;">{f.get('value','')}</td>
  <td style="padding:0.6rem 0.8rem;border-bottom:1px solid #f0f0f0;">
    <span style="background:{bbg};color:{bfg};padding:3px 10px;border-radius:20px;
                 font-size:0.73rem;font-weight:700;">{f.get('status','')}</span>
  </td>
</tr>"""

        components.html(f"""
<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:transparent;font-family:Nunito,sans-serif;">
<div style="background:white;border-radius:18px;padding:1.4rem;
            box-shadow:0 4px 20px rgba(0,0,0,0.06);">
  <div style="font-size:0.8rem;font-weight:800;letter-spacing:1px;
              text-transform:uppercase;color:#667eea;margin-bottom:0.8rem;">
    📋 Reference Ranges
  </div>
  <table style="width:100%;border-collapse:collapse;">
    <thead>
      <tr>
        <th style="font-size:0.74rem;font-weight:700;color:#555;text-transform:uppercase;
                   letter-spacing:0.5px;padding:0.5rem 0.8rem;border-bottom:2px solid #eee;text-align:left;">
          Test Parameter</th>
        <th style="font-size:0.74rem;font-weight:700;color:#555;text-transform:uppercase;
                   letter-spacing:0.5px;padding:0.5rem 0.8rem;border-bottom:2px solid #eee;text-align:left;">
          Normal Range</th>
        <th style="font-size:0.74rem;font-weight:700;color:#555;text-transform:uppercase;
                   letter-spacing:0.5px;padding:0.5rem 0.8rem;border-bottom:2px solid #eee;text-align:left;">
          Your Result</th>
        <th style="font-size:0.74rem;font-weight:700;color:#555;text-transform:uppercase;
                   letter-spacing:0.5px;padding:0.5rem 0.8rem;border-bottom:2px solid #eee;text-align:left;">
          Status</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <div style="margin-top:0.8rem;background:#f0f4ff;border-radius:8px;padding:0.6rem 0.8rem;
              font-size:0.76rem;color:#667eea;">
    ℹ️ This report is AI-generated. Please consult your physician.
  </div>
</div>
</body>
</html>
""", height=350 + len(findings) * 38)

    # ── Legend ──
    components.html("""
<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:8px 0;background:transparent;font-family:Nunito,sans-serif;">
<div style="background:white;border-radius:16px;padding:1.2rem 2rem;
            box-shadow:0 4px 20px rgba(0,0,0,0.06);
            display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;">
  <div>
    <div style="font-size:0.82rem;font-weight:700;color:#555;margin-bottom:10px;">
      UNDERSTANDING YOUR RESULTS
    </div>
    <div style="display:flex;gap:2rem;flex-wrap:wrap;">
      <div>
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">
          <div style="width:10px;height:10px;border-radius:50%;background:#fc8181;"></div>
          <span style="font-size:0.76rem;font-weight:800;color:#fc8181;">LOW</span>
          <div style="width:40px;height:3px;background:#fc8181;border-radius:2px;"></div>
        </div>
        <div style="font-size:0.69rem;color:#888;">0% – 40% &nbsp;|&nbsp; Below normal range</div>
      </div>
      <div>
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">
          <div style="width:10px;height:10px;border-radius:50%;background:#f6ad55;"></div>
          <span style="font-size:0.76rem;font-weight:800;color:#f6ad55;">NORMAL</span>
          <div style="width:40px;height:3px;background:#f6ad55;border-radius:2px;"></div>
        </div>
        <div style="font-size:0.69rem;color:#888;">40% – 70% &nbsp;|&nbsp; Within normal range</div>
      </div>
      <div>
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">
          <div style="width:10px;height:10px;border-radius:50%;background:#48bb78;"></div>
          <span style="font-size:0.76rem;font-weight:800;color:#48bb78;">HIGH</span>
          <div style="width:40px;height:3px;background:#48bb78;border-radius:2px;"></div>
        </div>
        <div style="font-size:0.69rem;color:#888;">70% – 100% &nbsp;|&nbsp; Above normal range</div>
      </div>
    </div>
  </div>
  <div style="text-align:right;">
    <div style="font-size:0.78rem;color:#555;margin-bottom:8px;">
      Good health begins with regular check-ups<br>and a balanced lifestyle.
    </div>
    <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;
                border-radius:20px;padding:0.6rem 1.4rem;font-weight:800;font-size:0.82rem;">
      💜 Stay Healthy, Stay Happy!
    </div>
  </div>
</div>
</body>
</html>
""", height=130)

    # ── 3 Feature Buttons: Voice Summary, Voice Advice, Download Report ──
    st.markdown("<br>", unsafe_allow_html=True)

    summary_text = f"Hello {data.get('patient_name','Patient')}. {data.get('summary','')}. "
    for f in findings:
        summary_text += f"{f.get('test_name','')} is {f.get('status','')}. Your value is {f.get('value','')}. Normal range is {f.get('normal_range','')}. {f.get('explanation','')}. "
    advice_text = f"Doctor advice for {data.get('patient_name','you')}: {data.get('doctor_advice','Please consult a doctor.')}"

    summary_js = summary_text.replace("'", " ").replace('"', " ").replace("\n", " ")
    advice_js  = advice_text.replace("'", " ").replace('"', " ").replace("\n", " ")

    components.html(f"""
<!DOCTYPE html><html>
<head><link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&display=swap" rel="stylesheet"></head>
<body style="margin:0;padding:0;background:transparent;font-family:Nunito,sans-serif;">
<div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:6px;">
  <button onclick="speakText(\'{summary_js}\')"
    style="flex:1;min-width:200px;background:linear-gradient(135deg,#667eea,#764ba2);
           color:white;border:none;border-radius:14px;padding:0.85rem 1.2rem;
           font-family:Nunito,sans-serif;font-size:0.88rem;font-weight:800;cursor:pointer;">
    🔊 Listen to Full Report
  </button>
  <button onclick="speakText(\'{advice_js}\')"
    style="flex:1;min-width:200px;background:linear-gradient(135deg,#f6ad55,#ed8936);
           color:white;border:none;border-radius:14px;padding:0.85rem 1.2rem;
           font-family:Nunito,sans-serif;font-size:0.88rem;font-weight:800;cursor:pointer;">
    💊 Listen to Advice
  </button>
  <button onclick="window.speechSynthesis.cancel();document.getElementById(\'vs\').innerText=\'⏹ Stopped\';"
    style="background:white;color:#e53e3e;border:2px solid #fc8181;border-radius:14px;
           padding:0.85rem 1.2rem;font-family:Nunito,sans-serif;font-size:0.88rem;
           font-weight:800;cursor:pointer;">
    ⏹ Stop
  </button>
</div>
<div id="vs" style="font-size:0.76rem;color:#667eea;min-height:16px;"></div>
<script>
function speakText(t){{
  window.speechSynthesis.cancel();
  var u=new SpeechSynthesisUtterance(t);
  u.lang="en-US";u.rate=0.92;u.pitch=1;
  u.onstart=function(){{document.getElementById("vs").innerText="🔊 Playing...";}};
  u.onend=function(){{document.getElementById("vs").innerText="✅ Done";}};
  window.speechSynthesis.speak(u);
}}
</script>
</body></html>
""", height=105)

    # ── PDF Download ──
    import datetime, base64 as b64mod
    report_date = datetime.datetime.now().strftime("%B %d, %Y — %I:%M %p")
    urgent_html = '<div style="background:#fff5f5;border:2px solid #fc8181;border-radius:8px;padding:8px 12px;color:#c53030;font-weight:700;margin:10px 0;">🚨 URGENT — Please See a Doctor Immediately</div>' if urgent else '<div style="background:#f0fff4;border:2px solid #68d391;border-radius:8px;padding:8px 12px;color:#276749;font-weight:700;margin:10px 0;">✅ Overall Status: Normal</div>'

    pdf_rows = ""
    for f in findings:
        bbg, bfg = get_badge_style(f.get("status","Normal"))
        pdf_rows += f'<tr><td>{f.get("test_name","")}</td><td>{f.get("normal_range","")}</td><td><strong>{f.get("value","")}</strong></td><td><span style="background:{bbg};color:{bfg};padding:2px 8px;border-radius:10px;font-size:11px;font-weight:700;">{f.get("status","")}</span></td><td style="font-size:11px;">{f.get("explanation","")}</td></tr>'

    pdf_html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap" rel="stylesheet">
<style>
body{{font-family:Nunito,sans-serif;background:#f0f4ff;margin:0;padding:20px;color:#1a1a2e;}}
.wrap{{max-width:800px;margin:0 auto;background:white;border-radius:16px;padding:30px;}}
.hdr{{background:linear-gradient(135deg,#667eea,#764ba2);border-radius:12px;padding:20px;color:white;margin-bottom:20px;}}
.hdr h1{{margin:0;font-size:1.5rem;font-weight:900;}}
.hdr p{{margin:0;font-size:0.8rem;opacity:0.8;}}
.irow{{display:flex;gap:12px;margin-bottom:14px;}}
.ibox{{background:#f0f4ff;border-radius:10px;padding:10px 14px;flex:1;}}
.ilbl{{font-size:0.68rem;color:#888;text-transform:uppercase;letter-spacing:1px;}}
.ival{{font-size:0.95rem;font-weight:800;}}
.stitle{{font-size:0.72rem;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#667eea;margin:16px 0 8px;}}
table{{width:100%;border-collapse:collapse;}}
th{{font-size:0.7rem;font-weight:700;color:#555;text-transform:uppercase;padding:7px;border-bottom:2px solid #eee;text-align:left;}}
td{{padding:7px;font-size:0.82rem;border-bottom:1px solid #f0f0f0;}}
.sbox{{background:#f0f4ff;border-radius:10px;padding:12px;font-size:0.84rem;line-height:1.6;color:#333;}}
.abox{{background:#f8f4ff;border-radius:10px;padding:12px;font-size:0.84rem;line-height:1.6;color:#553c9a;margin-top:8px;}}
.footer{{text-align:center;font-size:0.7rem;color:#aaa;margin-top:20px;padding-top:14px;border-top:1px solid #eee;}}
.pbtn{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:10px;
       padding:10px 24px;font-size:0.88rem;font-weight:800;cursor:pointer;margin-bottom:16px;font-family:Nunito,sans-serif;}}
@media print{{.pbtn{{display:none;}}}}
</style></head><body>
<div class="wrap">
<button class="pbtn" onclick="window.print()">🖨️ Print / Save as PDF</button>
<div class="hdr"><h1>🩺 CuraSign AI — Medical Report</h1><p>Generated on {report_date}</p></div>
<div class="irow">
  <div class="ibox"><div class="ilbl">Patient</div><div class="ival">👤 {data.get("patient_name","N/A")}</div></div>
  <div class="ibox"><div class="ilbl">Report Type</div><div class="ival">🏥 {data.get("report_type","N/A")}</div></div>
</div>
{urgent_html}
<div class="stitle">📋 Summary</div>
<div class="sbox">{data.get("summary","")}</div>
<div class="stitle">🔬 Test Results</div>
<table><thead><tr><th>Test</th><th>Normal Range</th><th>Value</th><th>Status</th><th>Explanation</th></tr></thead>
<tbody>{pdf_rows}</tbody></table>
<div class="stitle">👨‍⚕️ Doctor Advice</div>
<div class="abox">💊 {data.get("doctor_advice","Please consult a doctor.")}</div>
<div class="footer">⚠️ AI-generated report. Consult a qualified doctor. | CuraSign AI — {report_date}</div>
</div></body></html>"""

    pdf_b64 = b64mod.b64encode(pdf_html.encode()).decode()
    pt = data.get("patient_name","Patient").replace(" ","_")

    components.html(f"""
<!DOCTYPE html><html>
<head><link href="https://fonts.googleapis.com/css2?family=Nunito:wght@800;900&display=swap" rel="stylesheet"></head>
<body style="margin:0;padding:4px 0;background:transparent;">
<a href="data:text/html;base64,{pdf_b64}" download="CuraSign_{pt}.html"
   style="display:inline-flex;align-items:center;gap:8px;
          background:linear-gradient(135deg,#48bb78,#38a169);
          color:white;text-decoration:none;border-radius:14px;
          padding:0.85rem 1.5rem;font-family:Nunito,sans-serif;
          font-size:0.88rem;font-weight:800;
          box-shadow:0 4px 15px rgba(72,187,120,0.4);">
  📄 Download Report
</a>
<span style="font-size:0.73rem;color:#888;margin-left:10px;">
  Opens in browser → Ctrl+P → Save as PDF
</span>
</body></html>
""", height=65)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("🔍 View Raw JSON Data"):
        st.json(data)

    st.markdown("""
<div style="text-align:center;font-size:0.75rem;color:#aaa;margin-top:1rem;padding:1rem;">
  ⚠️ This is an AI-generated analysis. Always consult a qualified doctor before making any health decisions.
</div>
""", unsafe_allow_html=True)


# ============================================================
# MAIN
# ============================================================
def main():
    st.set_page_config(page_title="CuraSign AI", page_icon="🩺", layout="wide")

    st.markdown("""
<style>
html, body, [class*="css"] { background: #f0f4ff; }
.stApp { background: #f0f4ff; }
.block-container { padding: 1.5rem 2rem !important; max-width: 1200px; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

    # ============================================================
    #  GROQ API KEY
    # ============================================================
    API_KEY = st.secrets.get("GROQ_API_KEY", "")

    st.markdown("""
<div style="background:linear-gradient(135deg,#667eea,#764ba2);border-radius:20px;
            padding:1.5rem 2rem;margin-bottom:2rem;display:flex;align-items:center;
            gap:14px;box-shadow:0 8px 32px rgba(102,126,234,0.3);">
  <span style="font-size:2.2rem;">🩺</span>
  <div>
    <div style="font-family:Nunito,sans-serif;font-size:1.8rem;font-weight:900;color:white;margin:0;">
      CuraSign AI
    </div>
    <div style="font-size:0.85rem;color:rgba(255,255,255,0.75);margin:0;">
      Your Intelligent Healthcare Assistant — Scan. Analyze. Understand.
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload Medical Report Image",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        col_img, col_info = st.columns([1, 2])
        with col_img:
            st.image(uploaded_file, caption="Uploaded Report", use_container_width=True)
        with col_info:
            st.markdown("""
<div style="padding:1rem 0;">
  <div style="color:#48bb78;font-size:0.9rem;font-weight:700;font-family:Nunito,sans-serif;">
    ✅ Image uploaded successfully
  </div>
  <div style="color:#888;font-size:0.85rem;margin-top:6px;">AI is analyzing your report...</div>
</div>
""", unsafe_allow_html=True)

        with st.spinner("🔄 Analyzing your report..."):
            try:
                image_bytes = uploaded_file.read()
                data, error = get_text(image_bytes, API_KEY)
                if error:
                    st.error(f"❌ Error: {error}")
                    st.info("💡 Check your Groq API key at: https://console.groq.com")
                else:
                    display_dashboard(data)
            except Exception as e:
                st.error(f"❌ Something went wrong: {str(e)}")
    else:
        st.markdown("""
<div style="background:white;border-radius:24px;padding:4rem 2rem;text-align:center;
            box-shadow:0 4px 24px rgba(0,0,0,0.06);border:2px dashed #c3d0f5;margin-top:1rem;">
  <div style="font-size:4rem;margin-bottom:1rem;">📤</div>
  <div style="font-family:Nunito,sans-serif;font-size:1.4rem;font-weight:800;color:#1a1a2e;">
    Upload Your Medical Report
  </div>
  <div style="font-size:0.88rem;color:#888;margin-top:6px;">JPG or PNG</div>
  <div style="margin-top:1.5rem;display:flex;justify-content:center;gap:2rem;flex-wrap:wrap;">
    <span style="font-size:0.8rem;color:#667eea;font-weight:600;">✔ Clear, well-lit image</span>
    <span style="font-size:0.8rem;color:#667eea;font-weight:600;">✔ All values visible</span>
    <span style="font-size:0.8rem;color:#667eea;font-weight:600;">✔ No blurry images</span>
  </div>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
