#!/usr/bin/env python3
"""
Safety Backfire AI V0.9 — HTML Report Generator
Reads the comparison JSON and generates a visual HTML report.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMP_DIR = ROOT / "runs/comparison"
REPORT_PATH = COMP_DIR / "safety_backfire_report.html"

def load(name):
    p = COMP_DIR / name
    return json.loads(p.read_text()) if p.exists() else {}

def badge(verdict):
    colors = {
        "SAFETY_BACKFIRE_DETECTED": ("#FF2D55", "SAFETY BACKFIRE DETECTED"),
        "PARTIAL_BACKFIRE_RISK":    ("#FF9500", "PARTIAL BACKFIRE RISK"),
        "CLEAR_IMPROVEMENT":        ("#34C759", "CLEAR IMPROVEMENT"),
        "MARGINAL_IMPROVEMENT":     ("#30D158", "MARGINAL IMPROVEMENT"),
        "NO_SIGNIFICANT_CHANGE":    ("#636366", "NO SIGNIFICANT CHANGE"),
    }
    color, label = colors.get(verdict, ("#636366", verdict))
    return color, label

def metric_row(key, m):
    if m["verdict"] == "N/A": return ""
    icons = {"BACKFIRE": "▲ BACKFIRE", "IMPROVEMENT": "▼ IMPROVEMENT", "UNCHANGED": "— UNCHANGED"}
    clrs  = {"BACKFIRE": "#FF3B30",    "IMPROVEMENT": "#34C759",        "UNCHANGED": "#8E8E93"}
    pct   = f"{m['change_pct']:+.1f}%" if m["change_pct"] is not None else "—"
    b = f"{m['before']:.2f}" if isinstance(m["before"], float) else str(m["before"])
    a = f"{m['after']:.2f}"  if isinstance(m["after"], float)  else str(m["after"])
    v_text = icons[m["verdict"]]
    v_color = clrs[m["verdict"]]
    display = key.replace("_", " ").title()
    return f"""
      <tr>
        <td class="metric-name">{display}</td>
        <td class="val before">{b}</td>
        <td class="val after">{a}</td>
        <td class="val change">{pct}</td>
        <td class="verdict-cell" style="color:{v_color};font-weight:700">{v_text}</td>
      </tr>"""

def main():
    comp   = load("safety_backfire_comparison.json")
    before = load("before_baseline.json")
    after  = load("after_baseline.json")

    if not comp:
        print("No comparison data found. Run run_v09_comparison.py first.")
        return

    labels  = comp.get("comparison_labels", {})
    summary = comp.get("summary", {})
    metrics = comp.get("metrics", {})
    verdict = summary.get("overall_verdict", "UNKNOWN")
    score   = summary.get("net_backfire_score", 0)
    v_color, v_label = badge(verdict)

    rows = "".join(metric_row(k, v) for k, v in metrics.items())

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Safety Backfire AI — V0.9 Report</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
  :root {{
    --bg: #0A0A0F;
    --surface: #13131A;
    --border: rgba(255,255,255,0.08);
    --text: #E8E8F0;
    --muted: #8E8E9A;
    --accent: #007AFF;
    --red: #FF3B30;
    --green: #34C759;
    --yellow: #FF9500;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; padding:40px 24px; }}
  .container {{ max-width:960px; margin:0 auto; }}

  .header {{ text-align:center; margin-bottom:48px; }}
  .header h1 {{ font-size:13px; font-weight:500; letter-spacing:0.12em; color:var(--muted); text-transform:uppercase; margin-bottom:16px; }}
  .header h2 {{ font-size:36px; font-weight:900; letter-spacing:-0.03em; color:var(--text); margin-bottom:8px; }}
  .header p {{ color:var(--muted); font-size:14px; }}

  .verdict-card {{
    background: {v_color}18;
    border: 2px solid {v_color}60;
    border-radius:20px;
    padding:32px;
    text-align:center;
    margin-bottom:40px;
  }}
  .verdict-label {{ font-size:13px; font-weight:500; color:{v_color}; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:12px; }}
  .verdict-main {{ font-size:32px; font-weight:900; color:{v_color}; margin-bottom:8px; }}
  .verdict-score {{ font-size:14px; color:{v_color}aa; }}

  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:40px; }}
  .stat-card {{ background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:24px; }}
  .stat-label {{ font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); margin-bottom:8px; }}
  .stat-value {{ font-size:28px; font-weight:800; color:var(--text); margin-bottom:4px; }}
  .stat-sub {{ font-size:12px; color:var(--muted); }}

  .section {{ background:var(--surface); border:1px solid var(--border); border-radius:16px; overflow:hidden; margin-bottom:24px; }}
  .section-header {{ padding:20px 24px; border-bottom:1px solid var(--border); }}
  .section-title {{ font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); }}

  table {{ width:100%; border-collapse:collapse; }}
  th {{ padding:12px 20px; text-align:left; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--muted); border-bottom:1px solid var(--border); }}
  td {{ padding:14px 20px; border-bottom:1px solid var(--border); font-size:14px; }}
  tr:last-child td {{ border-bottom:none; }}
  .metric-name {{ font-weight:500; color:var(--text); font-size:13px; }}
  .val {{ font-family:'SF Mono','Fira Code',monospace; font-size:13px; color:var(--text); }}
  .before {{ color:var(--muted); }}
  .after  {{ color:var(--text); font-weight:600; }}
  .change {{ color:var(--muted); }}
  .verdict-cell {{ font-size:12px; }}

  .segments {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:24px; }}
  .seg-card {{ background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:24px; }}
  .seg-label {{ font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); margin-bottom:12px; }}
  .seg-period {{ font-size:16px; font-weight:700; color:var(--text); margin-bottom:16px; }}
  .seg-metric {{ display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid var(--border); font-size:13px; }}
  .seg-metric:last-child {{ border:none; }}
  .seg-metric-label {{ color:var(--muted); }}
  .seg-metric-val {{ font-weight:600; font-family:monospace; }}

  .note {{ background:#007AFF10; border:1px solid #007AFF30; border-radius:12px; padding:16px 20px; font-size:12px; color:var(--muted); line-height:1.6; }}

  .bar-container {{ display:flex; align-items:center; gap:12px; margin:8px 0; }}
  .bar-label {{ width:180px; font-size:12px; color:var(--muted); flex-shrink:0; }}
  .bar-track {{ flex:1; height:8px; background:#ffffff0a; border-radius:4px; overflow:hidden; }}
  .bar-fill {{ height:100%; border-radius:4px; transition:width 0.8s ease; }}
  .bar-val {{ width:60px; font-size:12px; font-family:monospace; text-align:right; flex-shrink:0; }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>Safety Backfire AI · V0.9 · Pre/Post Analysis</h1>
    <h2>Spatial Risk Comparison Report</h2>
    <p>{labels.get("before","Before")} vs {labels.get("after","After")}</p>
  </div>

  <div class="verdict-card">
    <div class="verdict-label">Overall Verdict</div>
    <div class="verdict-main">{v_label}</div>
    <div class="verdict-score">Net Backfire Score: {score:+.3f} · {summary.get('metrics_showing_backfire',0)} backfire indicators vs {summary.get('metrics_showing_improvement',0)} improvements</div>
  </div>

  <div class="segments">
    <div class="seg-card">
      <div class="seg-label">⬅ Before (Segment A)</div>
      <div class="seg-period">{labels.get("before","Pre-Intervention")}</div>
      {''.join(f'<div class="seg-metric"><span class="seg-metric-label">{k.replace("_"," ").title()}</span><span class="seg-metric-val">{(f"{v:.2f}" if isinstance(v,float) else str(v)) if v is not None else "—"}</span></div>' for k,v in before.items() if not isinstance(v, dict) and k not in ["total_frames_analyzed","closest_interacting_pair"])}
    </div>
    <div class="seg-card">
      <div class="seg-label">➡ After (Segment B)</div>
      <div class="seg-period">{labels.get("after","Post-Intervention")}</div>
      {''.join(f'<div class="seg-metric"><span class="seg-metric-label">{k.replace("_"," ").title()}</span><span class="seg-metric-val">{(f"{v:.2f}" if isinstance(v,float) else str(v)) if v is not None else "—"}</span></div>' for k,v in after.items() if not isinstance(v, dict) and k not in ["total_frames_analyzed","closest_interacting_pair"])}
    </div>
  </div>

  <div class="section">
    <div class="section-header">
      <div class="section-title">Metric-by-Metric Comparison</div>
    </div>
    <table>
      <thead>
        <tr>
          <th>Metric</th>
          <th>Before</th>
          <th>After</th>
          <th>Change</th>
          <th>Verdict</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>

  <div class="note">
    <strong>Scientific Disclaimer:</strong> {comp.get("scientific_note","")}
  </div>

</div>
</body>
</html>"""

    REPORT_PATH.write_text(html, encoding="utf-8")
    print(f"Report saved: {REPORT_PATH}")

if __name__ == "__main__":
    main()
