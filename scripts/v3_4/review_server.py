"""
review_server.py
Milestone V3.4-C — Local Web UI & Adjudication Server for Human Reviewers

Features:
  - 100% Offline, Zero external pip dependencies (Standard library http.server)
  - Full RFC 7233 HTTP Range Request Support:
      * 200 OK for full file requests (with Accept-Ranges: bytes)
      * 206 Partial Content for byte ranges (explicit start-end, open-ended start-, suffix -N)
      * 416 Range Not Satisfiable for invalid ranges (Content-Range: bytes */file_size)
      * Full HEAD request support (do_HEAD)
  - Chunked video streaming (64KB buffer) to prevent memory exhaustion
  - Directory traversal protection & canonical path resolution
  - Displays ONLY the 38 ELIGIBLE_EVENTS in deterministic order
  - Strict Double-Blind Protocol: Zero AI metrics, zero YOLO, zero ByteTrack, zero Model H
  - Strict Reviewer Isolation: Reviewer 2 has zero visibility into Reviewer 1 entries
  - Formal Validation Guards:
      * BACKFIRE requires all 6 criteria to be YES
      * If secondary_risk is UNKNOWN, cannot label NO_BACKFIRE (must be AMBIGUOUS)
  - Submission lock, revision history, and audit log generation
"""

import sys
import os
import json
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Canonical project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ADJUDICATION_DIR = PROJECT_ROOT / "outputs/v3_4/adjudication"
AUDIT_DIR = ADJUDICATION_DIR / "audit"
UNION_REGISTRY_PATH = PROJECT_ROOT / "outputs/v3_4/candidates/union_events_registry.json"

DEFAULT_PORT = 8765

# Import validation and session helpers from start_reviewer_session
sys.path.insert(0, str(PROJECT_ROOT / "scripts/v3_4"))
from start_reviewer_session import (
    get_eligible_events,
    get_event_review_status,
    verify_package_integrity,
    submit_reviewer_form,
    submit_adjudication,
    check_and_update_consensus,
    compute_sha256
)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Safety Backfire AI — Human Adjudication Platform (V3.4-C)</title>
  <style>
    :root {
      --bg-dark: #0f1117;
      --bg-card: #181b24;
      --bg-card-hover: #212634;
      --border-color: #2b3142;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --accent-red: #ef4444;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg-dark);
      color: var(--text-main);
      font-family: var(--font-family);
      display: flex;
      height: 100vh;
      overflow: hidden;
    }
    /* Sidebar */
    #sidebar {
      width: 360px;
      background: var(--bg-card);
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
    }
    .sidebar-header {
      padding: 16px;
      border-bottom: 1px solid var(--border-color);
    }
    .sidebar-header h1 { font-size: 1.05rem; font-weight: 700; color: #fff; margin-bottom: 4px; }
    .sidebar-header .tagline { font-size: 0.75rem; color: var(--accent-amber); font-weight: 600; text-transform: uppercase; }
    .session-config {
      padding: 12px 16px;
      background: #11141c;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .session-config label { font-size: 0.75rem; color: var(--text-muted); font-weight: 600; }
    .session-config input, .session-config select {
      background: #1e2230;
      border: 1px solid var(--border-color);
      color: #fff;
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 0.85rem;
    }
    .event-list {
      flex: 1;
      overflow-y: auto;
      padding: 8px;
    }
    .event-item {
      padding: 10px 12px;
      border-radius: 6px;
      margin-bottom: 4px;
      cursor: pointer;
      border: 1px solid transparent;
      display: flex;
      flex-direction: column;
      gap: 4px;
      transition: all 0.15s ease;
    }
    .event-item:hover { background: var(--bg-card-hover); border-color: var(--border-color); }
    .event-item.active { background: #262c3e; border-color: var(--primary); }
    .event-id-row { display: flex; justify-content: space-between; align-items: center; }
    .event-id-text { font-size: 0.82rem; font-weight: 600; font-family: monospace; color: #fff; }
    .event-meta-text { font-size: 0.72rem; color: var(--text-muted); }
    .status-badge {
      font-size: 0.65rem;
      padding: 2px 6px;
      border-radius: 12px;
      font-weight: 700;
      text-transform: uppercase;
      background: #2b3142;
      color: #cbd5e1;
    }
    .status-badge.pending { background: #374151; color: #9ca3af; }
    .status-badge.completed { background: #064e3b; color: #34d399; }
    .status-badge.disagreement { background: #78350f; color: #fbbf24; }
    .status-badge.adjudicated { background: #1e3a8a; color: #93c5fd; }

    /* Main Area */
    #main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow-y: auto;
    }
    .top-banner {
      background: #131722;
      border-bottom: 1px solid var(--border-color);
      padding: 10px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .blinding-indicator {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.78rem;
      color: #34d399;
      background: rgba(16, 185, 129, 0.1);
      padding: 4px 10px;
      border-radius: 20px;
      border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .review-body {
      display: flex;
      flex: 1;
      gap: 20px;
      padding: 20px 24px;
    }
    .video-column {
      flex: 1.2;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .form-column {
      flex: 1.3;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      overflow-y: auto;
      max-height: calc(100vh - 100px);
    }
    /* Video Player Component */
    .video-container {
      background: #000;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid var(--border-color);
      position: relative;
      min-height: 280px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    video {
      width: 100%;
      height: auto;
      max-height: 480px;
      display: block;
      background: #000;
    }
    .video-status-overlay {
      position: absolute;
      top: 8px;
      right: 8px;
      background: rgba(0,0,0,0.7);
      color: #93c5fd;
      font-size: 0.7rem;
      padding: 4px 8px;
      border-radius: 4px;
      pointer-events: none;
      font-family: monospace;
    }
    .video-error-overlay {
      display: none;
      position: absolute;
      inset: 0;
      background: rgba(15, 23, 42, 0.9);
      color: #f87171;
      padding: 20px;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      gap: 8px;
      text-align: center;
      font-size: 0.85rem;
    }
    .phase-selector {
      display: flex;
      background: #161922;
      border-radius: 6px;
      padding: 4px;
      gap: 4px;
      border: 1px solid var(--border-color);
    }
    .phase-btn {
      flex: 1;
      padding: 8px 12px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-weight: 600;
      font-size: 0.8rem;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
    }
    .phase-btn:hover { color: #fff; background: #222736; }
    .phase-btn.active { background: var(--primary); color: #fff; }
    .phase-btn span.sub { font-size: 0.65rem; opacity: 0.8; font-weight: normal; }

    .metadata-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .meta-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
      font-size: 0.78rem;
    }
    .meta-field {
      background: #12141c;
      padding: 6px 10px;
      border-radius: 4px;
      border: 1px solid #222634;
    }
    .meta-field .label { color: var(--text-muted); font-size: 0.7rem; margin-bottom: 2px; }
    .meta-field .val { font-weight: 600; color: #fff; }

    /* Form Styles */
    .form-section-title {
      font-size: 0.88rem;
      font-weight: 700;
      color: #93c5fd;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 6px;
      margin-top: 8px;
    }
    .question-block {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .question-label {
      font-size: 0.8rem;
      font-weight: 600;
      color: #e5e7eb;
    }
    .options-row {
      display: flex;
      gap: 8px;
    }
    .opt-btn {
      flex: 1;
      padding: 6px 8px;
      background: #1e2230;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      text-align: center;
      transition: all 0.1s ease;
    }
    .opt-btn:hover { background: #282f42; color: #fff; }
    .opt-btn.selected { background: var(--primary); border-color: var(--primary); color: #fff; }
    .opt-btn.selected.yes { background: var(--accent-green); border-color: var(--accent-green); }
    .opt-btn.selected.no { background: var(--accent-red); border-color: var(--accent-red); }
    .opt-btn.selected.unknown { background: var(--accent-amber); border-color: var(--accent-amber); color: #000; }

    textarea, input[type="text"] {
      width: 100%;
      background: #11141c;
      border: 1px solid var(--border-color);
      color: #fff;
      padding: 8px 10px;
      border-radius: 4px;
      font-size: 0.8rem;
      font-family: inherit;
    }
    textarea { min-height: 55px; resize: vertical; }

    .submit-btn {
      background: var(--primary);
      color: #fff;
      border: none;
      padding: 12px;
      border-radius: 6px;
      font-size: 0.9rem;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.15s ease;
      margin-top: 10px;
    }
    .submit-btn:hover { background: var(--primary-hover); }
    .submit-btn:disabled { background: #374151; color: #9ca3af; cursor: not-allowed; }

    .alert-box {
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 0.8rem;
      display: none;
    }
    .alert-box.error { background: rgba(239, 68, 68, 0.15); border: 1px solid var(--accent-red); color: #fca5a5; display: block; }
    .alert-box.success { background: rgba(16, 185, 129, 0.15); border: 1px solid var(--accent-green); color: #6ee7b7; display: block; }

    /* Adjudication View */
    .disagreement-banner {
      background: rgba(245, 158, 11, 0.15);
      border: 1px solid var(--accent-amber);
      color: #fde68a;
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 0.8rem;
      line-height: 1.4;
    }
    .reviewer-comparison {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      background: #12141c;
      padding: 12px;
      border-radius: 6px;
      border: 1px solid var(--border-color);
    }
    .rev-card { display: flex; flex-direction: column; gap: 4px; font-size: 0.78rem; }
    .rev-card h4 { font-size: 0.8rem; color: #93c5fd; }
  </style>
</head>
<body>

  <!-- Sidebar -->
  <div id="sidebar">
    <div class="sidebar-header">
      <h1>Safety Backfire AI</h1>
      <div class="tagline">Independent Human Adjudication (V3.4-C)</div>
    </div>

    <div class="session-config">
      <label for="reviewer-slot-select">Active Slot / Protocol Role</label>
      <select id="reviewer-slot-select" onchange="onRoleChange()">
        <option value="REVIEWER_1">Reviewer 1 (Independent)</option>
        <option value="REVIEWER_2">Reviewer 2 (Double-Blind Isolated)</option>
        <option value="ADJUDICATOR">Third Human Adjudicator (Disagreements)</option>
      </select>

      <label for="reviewer-id-input">Reviewer Identifier (e.g. REVIEWER_001)</label>
      <input type="text" id="reviewer-id-input" placeholder="Enter Reviewer ID..." value="REVIEWER_001">
    </div>

    <div class="event-list" id="event-list-container">
      <!-- Events populated by JS -->
    </div>
  </div>

  <!-- Main Content -->
  <div id="main-content">
    <div class="top-banner">
      <div>
        <span id="active-event-header" style="font-weight: 700; font-size: 0.95rem;">Select an Event</span>
        <span id="active-event-facility" style="color: var(--text-muted); font-size: 0.8rem; margin-left: 12px;"></span>
      </div>
      <div class="blinding-indicator">
        <span>🛡️ Double-Blind Protocol Enforced (0 AI Overlays / 0 YOLO / 0 Model H)</span>
      </div>
    </div>

    <div class="review-body" id="review-body-container" style="display: none;">
      <!-- Video Column -->
      <div class="video-column">
        <div class="phase-selector">
          <button class="phase-btn active" id="btn-pre" onclick="switchVideoPhase('pre')">
            <span>PRE-INTERVENTION</span>
            <span class="sub" id="label-pre-time">Baseline</span>
          </button>
          <button class="phase-btn" id="btn-intervention" onclick="switchVideoPhase('intervention')">
            <span>INTERVENTION</span>
            <span class="sub" id="label-int-time">Safety Action</span>
          </button>
          <button class="phase-btn" id="btn-post" onclick="switchVideoPhase('post')">
            <span>POST-INTERVENTION</span>
            <span class="sub" id="label-post-time">Secondary Outcome</span>
          </button>
        </div>

        <div class="video-container">
          <video id="event-video" controls autoplay loop playsinline muted preload="auto">
            <source id="video-source" src="" type="video/mp4">
            Your browser does not support HTML5 video.
          </video>
          <div class="video-status-overlay" id="video-status">Initializing...</div>
          <div class="video-error-overlay" id="video-error">
            <div style="font-weight: 700; font-size: 1rem;">Video Playback Error</div>
            <div id="video-error-msg">Failed to load video stream.</div>
          </div>
        </div>

        <div class="metadata-card">
          <div style="font-size: 0.8rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px;">Spatiotemporal Context</div>
          <div class="meta-grid">
            <div class="meta-field">
              <div class="label">Camera Stream</div>
              <div class="val" id="meta-camera">-</div>
            </div>
            <div class="meta-field">
              <div class="label">Physical Scene</div>
              <div class="val" id="meta-scene">-</div>
            </div>
            <div class="meta-field">
              <div class="label">Primary Zone</div>
              <div class="val" id="meta-pzone">-</div>
            </div>
            <div class="meta-field">
              <div class="label">Secondary Zone</div>
              <div class="val" id="meta-szone">-</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Form Column -->
      <div class="form-column" id="form-column">
        <div id="alert-box" class="alert-box"></div>

        <!-- Adjudication Specific Banner (Shown only for Adjudicator role) -->
        <div id="adjudicator-context-box" style="display: none;"></div>

        <!-- Standard Review Form -->
        <div id="standard-review-fields">
          <div class="form-section-title">1. Event Classification</div>
          <div class="question-block">
            <div class="question-label">What best describes the observed event?</div>
            <select id="q-event-type" style="background: #11141c; border: 1px solid var(--border-color); color: #fff; padding: 8px; border-radius: 4px;">
              <option value="">-- Select Event Description --</option>
              <option value="SAFETY_INTERVENTION">Safety Intervention (deliberate action to reduce hazard)</option>
              <option value="NATURAL_INTERACTION">Natural Interaction (ordinary worker/vehicle routine)</option>
              <option value="NORMAL_OPERATION">Normal Operation (nominal flow without risk)</option>
              <option value="UNCERTAIN">Uncertain / Ambiguous Scene Dynamics</option>
              <option value="NO_RELEVANT_EVENT">No Relevant Event / False Lead</option>
            </select>
          </div>

          <div class="form-section-title">2. Causal Criteria Evaluation</div>

          <!-- A. intervention_visible -->
          <div class="question-block">
            <div class="question-label">A. Is the safety intervention clearly visible in the video?</div>
            <div class="options-row" data-field="intervention_visible">
              <button type="button" class="opt-btn" onclick="setOpt('intervention_visible', 'YES')">YES</button>
              <button type="button" class="opt-btn" onclick="setOpt('intervention_visible', 'NO')">NO</button>
              <button type="button" class="opt-btn" onclick="setOpt('intervention_visible', 'UNKNOWN')">UNKNOWN</button>
            </div>
          </div>

          <!-- B. primary_risk_present -->
          <div class="question-block">
            <div class="question-label">B. Was an initial hazard/risk present in the primary zone prior to intervention?</div>
            <div class="options-row" data-field="primary_risk_present">
              <button type="button" class="opt-btn" onclick="setOpt('primary_risk_present', 'YES')">YES</button>
              <button type="button" class="opt-btn" onclick="setOpt('primary_risk_present', 'NO')">NO</button>
              <button type="button" class="opt-btn" onclick="setOpt('primary_risk_present', 'UNKNOWN')">UNKNOWN</button>
            </div>
          </div>

          <!-- C. primary_risk_reduced -->
          <div class="question-block">
            <div class="question-label">C. Did the intervention successfully reduce/eliminate the primary hazard?</div>
            <div class="options-row" data-field="primary_risk_reduced">
              <button type="button" class="opt-btn" onclick="setOpt('primary_risk_reduced', 'YES')">YES</button>
              <button type="button" class="opt-btn" onclick="setOpt('primary_risk_reduced', 'NO')">NO</button>
              <button type="button" class="opt-btn" onclick="setOpt('primary_risk_reduced', 'UNKNOWN')">UNKNOWN</button>
            </div>
          </div>

          <!-- D. secondary_risk_changed -->
          <div class="question-block">
            <div class="question-label">D. Did a secondary hazard/risk emerge or increase in an adjacent zone?</div>
            <div class="options-row" data-field="secondary_risk_changed">
              <button type="button" class="opt-btn" onclick="setOpt('secondary_risk_changed', 'YES')">YES</button>
              <button type="button" class="opt-btn" onclick="setOpt('secondary_risk_changed', 'NO')">NO</button>
              <button type="button" class="opt-btn" onclick="setOpt('secondary_risk_changed', 'UNKNOWN')">UNKNOWN</button>
            </div>
          </div>

          <!-- E. causal_mechanism_observed -->
          <div class="question-block">
            <div class="question-label">E. Is a causal mechanism observed linking the intervention to the secondary outcome?</div>
            <div class="options-row" data-field="causal_mechanism_observed">
              <button type="button" class="opt-btn" onclick="setOpt('causal_mechanism_observed', 'YES')">YES</button>
              <button type="button" class="opt-btn" onclick="setOpt('causal_mechanism_observed', 'NO')">NO</button>
              <button type="button" class="opt-btn" onclick="setOpt('causal_mechanism_observed', 'UNKNOWN')">UNKNOWN</button>
            </div>
          </div>

          <!-- F. independent_evidence_present -->
          <div class="question-block">
            <div class="question-label">F. Is independent visual/physical evidence present (not relying on AI models)?</div>
            <div class="options-row" data-field="independent_evidence_present">
              <button type="button" class="opt-btn" onclick="setOpt('independent_evidence_present', 'YES')">YES</button>
              <button type="button" class="opt-btn" onclick="setOpt('independent_evidence_present', 'NO')">NO</button>
              <button type="button" class="opt-btn" onclick="setOpt('independent_evidence_present', 'UNKNOWN')">UNKNOWN</button>
            </div>
          </div>

          <!-- G. evidence_quality -->
          <div class="question-block">
            <div class="question-label">G. Visual Evidence Quality Rating</div>
            <div class="options-row" data-field="evidence_quality">
              <button type="button" class="opt-btn" onclick="setOpt('evidence_quality', 'HIGH')">HIGH</button>
              <button type="button" class="opt-btn" onclick="setOpt('evidence_quality', 'MEDIUM')">MEDIUM</button>
              <button type="button" class="opt-btn" onclick="setOpt('evidence_quality', 'LOW')">LOW</button>
              <button type="button" class="opt-btn" onclick="setOpt('evidence_quality', 'UNKNOWN')">UNKNOWN</button>
            </div>
          </div>

          <!-- Causal Link Confidence -->
          <div class="question-block">
            <div class="question-label">Causal Link Confidence</div>
            <select id="q-causal-link" style="background: #11141c; border: 1px solid var(--border-color); color: #fff; padding: 8px; border-radius: 4px;">
              <option value="NOT_ESTABLISHED">NOT_ESTABLISHED</option>
              <option value="PLAUSIBLE_BUT_UNCONFIRMED">PLAUSIBLE_BUT_UNCONFIRMED</option>
              <option value="TELEMETRY_SUPPORTED">TELEMETRY_SUPPORTED</option>
              <option value="DIRECTLY_OBSERVED">DIRECTLY_OBSERVED</option>
            </select>
          </div>

          <div class="form-section-title">3. Human Reviewer Notes</div>
          <div class="question-block">
            <div class="question-label">General Observations</div>
            <textarea id="note-observations" placeholder="Describe physical event dynamics..."></textarea>
          </div>
          <div class="question-block">
            <div class="question-label">Intervention Description</div>
            <textarea id="note-intervention" placeholder="Describe the safety intervention observed..."></textarea>
          </div>
          <div class="question-block">
            <div class="question-label">Primary Zone Observations</div>
            <textarea id="note-pzone" placeholder="Hazard status before vs after intervention..."></textarea>
          </div>
          <div class="question-block">
            <div class="question-label">Secondary Zone Observations</div>
            <textarea id="note-szone" placeholder="Secondary risk change or occlusion notes..."></textarea>
          </div>
          <div class="question-block">
            <div class="question-label">Causal Reasoning & Justification</div>
            <textarea id="note-reasoning" placeholder="Why does or does not this event constitute safety backfire?"></textarea>
          </div>

          <div class="form-section-title">4. Final Label Decision</div>
          <div class="question-block">
            <div class="question-label">Verdict Label</div>
            <div class="options-row" data-field="label_decision">
              <button type="button" class="opt-btn" onclick="setOpt('label_decision', 'BACKFIRE')">BACKFIRE</button>
              <button type="button" class="opt-btn" onclick="setOpt('label_decision', 'NO_BACKFIRE')">NO_BACKFIRE</button>
              <button type="button" class="opt-btn" onclick="setOpt('label_decision', 'AMBIGUOUS')">AMBIGUOUS</button>
            </div>
            <div id="rule-notice" style="font-size: 0.72rem; color: var(--accent-amber); margin-top: 4px;"></div>
          </div>
        </div>

        <!-- Submit Button -->
        <button type="button" class="submit-btn" id="btn-submit" onclick="submitCurrentReview()">
          Submit & Lock Review
        </button>
      </div>
    </div>
  </div>

  <script>
    let currentEventId = null;
    let currentEventData = null;
    let currentRole = "REVIEWER_1";
    let eventsList = [];
    let formState = {
      criteria: {},
      notes: {},
      event_type: null,
      causal_link: "NOT_ESTABLISHED",
      label_decision: null
    };

    const videoEl = document.getElementById("event-video");
    const videoStatus = document.getElementById("video-status");
    const videoError = document.getElementById("video-error");
    const videoErrorMsg = document.getElementById("video-error-msg");

    // Video playback event listeners
    videoEl.addEventListener("loadstart", () => {
      videoStatus.textContent = "Loading stream...";
      videoError.style.display = "none";
    });
    videoEl.addEventListener("canplay", () => {
      videoStatus.textContent = "Playing (H.264 MP4)";
      videoError.style.display = "none";
    });
    videoEl.addEventListener("playing", () => {
      videoStatus.textContent = "Playing (H.264 MP4)";
      videoError.style.display = "none";
    });
    videoEl.addEventListener("error", (e) => {
      const err = videoEl.error;
      let errStr = "Unknown media error";
      if (err) {
        if (err.code === 1) errStr = "MEDIA_ERR_ABORTED: Playback aborted by user/browser";
        else if (err.code === 2) errStr = "MEDIA_ERR_NETWORK: Network error downloading video";
        else if (err.code === 3) errStr = "MEDIA_ERR_DECODE: Media decode error";
        else if (err.code === 4) errStr = "MEDIA_ERR_SRC_NOT_SUPPORTED: Codec or format not supported";
        if (err.message) errStr += " (" + err.message + ")";
      }
      videoStatus.textContent = "Error: " + errStr;
      videoErrorMsg.textContent = errStr;
      videoError.style.display = "flex";
      console.error("HTML5 Video Error:", errStr, e);
    });

    async function init() {
      await loadEvents();
      if (eventsList.length > 0) {
        selectEvent(eventsList[0].union_id);
      }
    }

    async function loadEvents() {
      const res = await fetch("/api/events");
      eventsList = await res.json();
      renderSidebar();
    }

    function renderSidebar() {
      const container = document.getElementById("event-list-container");
      container.innerHTML = "";

      eventsList.forEach((ev, idx) => {
        const item = document.createElement("div");
        item.className = "event-item" + (ev.union_id === currentEventId ? " active" : "");
        item.onclick = () => selectEvent(ev.union_id);

        let badgeClass = "pending";
        let badgeText = "Pending";
        if (ev.status === "ADJUDICATED") {
          badgeClass = "adjudicated"; badgeText = "Adjudicated";
        } else if (ev.status === "CONSENSUS_REACHED") {
          badgeClass = "completed"; badgeText = "Consensus";
        } else if (ev.status === "ADJUDICATION_REQUIRED") {
          badgeClass = "disagreement"; badgeText = "Disagreement";
        } else if (ev.status === "REVIEWER_1_COMPLETE" || ev.status === "REVIEWER_2_COMPLETE") {
          badgeClass = "completed"; badgeText = "Partial";
        }

        item.innerHTML = `
          <div class="event-id-row">
            <span class="event-id-text">${idx + 1}. ${ev.union_id.replace('UNION_CAND_', '').replace('UNION_HEVT_', 'H_')}</span>
            <span class="status-badge ${badgeClass}">${badgeText}</span>
          </div>
          <div class="event-meta-text">${ev.scene_id} &bull; ${ev.camera_id}</div>
        `;
        container.appendChild(item);
      });
    }

    async function selectEvent(eventId) {
      currentEventId = eventId;
      renderSidebar();

      document.getElementById("review-body-container").style.display = "flex";
      document.getElementById("active-event-header").textContent = eventId;

      const res = await fetch("/api/event/" + eventId);
      currentEventData = await res.json();

      document.getElementById("active-event-facility").textContent = `${currentEventData.facility_scene} | Camera: ${currentEventData.camera_stream}`;
      document.getElementById("meta-camera").textContent = currentEventData.camera_stream;
      document.getElementById("meta-scene").textContent = currentEventData.facility_scene;
      document.getElementById("meta-pzone").textContent = currentEventData.spatial_zones?.primary_zone?.zone_id || "PROVISIONAL";
      document.getElementById("meta-szone").textContent = currentEventData.spatial_zones?.secondary_zone?.zone_id || "UNKNOWN";

      const tb = currentEventData.temporal_window_bounds || {};
      document.getElementById("label-pre-time").textContent = `${tb.pre?.duration_s || 0}s (${tb.pre?.start_frame}-${tb.pre?.end_frame})`;
      document.getElementById("label-int-time").textContent = `${tb.intervention?.duration_s || 0}s (${tb.intervention?.start_frame}-${tb.intervention?.end_frame})`;
      document.getElementById("label-post-time").textContent = `${tb.post?.duration_s || 0}s (${tb.post?.start_frame}-${tb.post?.end_frame})`;

      switchVideoPhase("intervention");
      await loadFormForCurrentRole();
    }

    function switchVideoPhase(phase) {
      document.querySelectorAll(".phase-btn").forEach(b => b.classList.remove("active"));
      document.getElementById("btn-" + phase).classList.add("active");

      const clipName = phase === "pre" ? "before.mp4" : (phase === "intervention" ? "intervention.mp4" : "after.mp4");
      const video = document.getElementById("event-video");
      const src = document.getElementById("video-source");

      videoError.style.display = "none";
      videoStatus.textContent = "Loading stream...";

      const videoUrl = `/video/${currentEventId}/${clipName}`;
      src.src = videoUrl;
      video.src = videoUrl;
      video.load();
      video.play().catch(e => {
        console.log("Autoplay caught (normal if browser policy requires click):", e);
      });
    }

    async function onRoleChange() {
      currentRole = document.getElementById("reviewer-slot-select").value;
      if (currentEventId) {
        await loadFormForCurrentRole();
      }
    }

    async function loadFormForCurrentRole() {
      resetFormInputs();
      const rId = document.getElementById("reviewer-id-input").value;
      const res = await fetch(`/api/form/${currentEventId}?slot=${currentRole}&reviewer_id=${rId}`);
      const data = await res.json();

      // Check if Adjudicator role
      if (currentRole === "ADJUDICATOR") {
        document.getElementById("adjudicator-context-box").style.display = "block";
        renderAdjudicatorContext(data);
      } else {
        document.getElementById("adjudicator-context-box").style.display = "none";
      }

      // Populate existing inputs if already partially or completed
      if (data.criteria_evaluations) {
        for (const [k, v] of Object.entries(data.criteria_evaluations)) {
          if (v) setOpt(k, v);
        }
      }
      if (data.observed_event_type) {
        document.getElementById("q-event-type").value = data.observed_event_type;
      }
      if (data.causal_link_confidence) {
        document.getElementById("q-causal-link").value = data.causal_link_confidence;
      }
      if (data.reviewer_notes) {
        document.getElementById("note-observations").value = data.reviewer_notes.observations || "";
        document.getElementById("note-intervention").value = data.reviewer_notes.intervention_description || "";
        document.getElementById("note-pzone").value = data.reviewer_notes.primary_zone_description || "";
        document.getElementById("note-szone").value = data.reviewer_notes.secondary_zone_description || "";
        document.getElementById("note-reasoning").value = data.reviewer_notes.reasoning_notes || "";
      }
      if (data.label_decision) {
        setOpt("label_decision", data.label_decision);
      }

      const alertBox = document.getElementById("alert-box");
      if (data.submission_locked) {
        alertBox.className = "alert-box success";
        alertBox.textContent = `Form is LOCKED (Revision count: ${data.revisions ? data.revisions.length : 0}). Submitting will create a new tracked revision.`;
        document.getElementById("btn-submit").textContent = "Submit Tracked Revision";
      } else {
        alertBox.className = "alert-box";
        alertBox.style.display = "none";
        document.getElementById("btn-submit").textContent = "Submit & Lock Review";
      }
    }

    function renderAdjudicatorContext(data) {
      const box = document.getElementById("adjudicator-context-box");
      if (data.disagreement) {
        box.innerHTML = `
          <div class="disagreement-banner">
            <strong>DISAGREEMENT DETECTED:</strong> ${data.disagreement_reason}<br>
            Independent Adjudication required by designated third reviewer.
          </div>
          <div class="reviewer-comparison" style="margin-top: 8px;">
            <div class="rev-card">
              <h4>Reviewer 1 Decision: ${data.reviewer_1_label || 'PENDING'}</h4>
              <p><em>Reasoning notes available in formal dossier.</em></p>
            </div>
            <div class="rev-card">
              <h4>Reviewer 2 Decision: ${data.reviewer_2_label || 'PENDING'}</h4>
              <p><em>Reasoning notes available in formal dossier.</em></p>
            </div>
          </div>
        `;
      } else {
        box.innerHTML = `
          <div style="background: #12141c; padding: 10px; border-radius: 6px; font-size: 0.8rem;">
            Consensus Status: ${data.status} | Final Label: <strong>${data.adjudicator_label}</strong>
          </div>
        `;
      }
    }

    function resetFormInputs() {
      formState = { criteria: {}, notes: {}, event_type: null, causal_link: "NOT_ESTABLISHED", label_decision: null };
      document.querySelectorAll(".opt-btn").forEach(b => b.classList.remove("selected", "yes", "no", "unknown"));
      document.getElementById("q-event-type").value = "";
      document.getElementById("q-causal-link").value = "NOT_ESTABLISHED";
      document.getElementById("note-observations").value = "";
      document.getElementById("note-intervention").value = "";
      document.getElementById("note-pzone").value = "";
      document.getElementById("note-szone").value = "";
      document.getElementById("note-reasoning").value = "";
      document.getElementById("rule-notice").textContent = "";
    }

    function setOpt(field, val) {
      if (field === "label_decision") {
        formState.label_decision = val;
      } else {
        formState.criteria[field] = val;
      }

      const row = document.querySelector(`.options-row[data-field="${field}"]`);
      if (row) {
        row.querySelectorAll(".opt-btn").forEach(btn => {
          btn.classList.remove("selected", "yes", "no", "unknown");
          if (btn.textContent.trim() === val) {
            btn.classList.add("selected");
            if (val === "YES") btn.classList.add("yes");
            if (val === "NO") btn.classList.add("no");
            if (val === "UNKNOWN") btn.classList.add("unknown");
          }
        });
      }
      checkRuleNotice();
    }

    function checkRuleNotice() {
      const notice = document.getElementById("rule-notice");
      const c = formState.criteria;
      if (formState.label_decision === "BACKFIRE") {
        const required = ["intervention_visible", "primary_risk_present", "primary_risk_reduced", "secondary_risk_changed", "causal_mechanism_observed", "independent_evidence_present"];
        const notYes = required.filter(k => c[k] !== "YES");
        if (notYes.length > 0) {
          notice.textContent = "⚠️ Rule Guard: BACKFIRE requires all 6 criteria to be YES. Incomplete criteria will reject submission.";
          return;
        }
      }
      if (formState.label_decision === "NO_BACKFIRE" && c["secondary_risk_changed"] === "UNKNOWN") {
        notice.textContent = "⚠️ Rule Guard: Cannot select NO_BACKFIRE when secondary risk is UNKNOWN (must be AMBIGUOUS).";
        return;
      }
      notice.textContent = "";
    }

    async function submitCurrentReview() {
      const alertBox = document.getElementById("alert-box");
      const rId = document.getElementById("reviewer-id-input").value.trim();
      if (!rId) {
        alertBox.className = "alert-box error";
        alertBox.textContent = "Error: Reviewer ID cannot be empty.";
        return;
      }

      formState.event_type = document.getElementById("q-event-type").value;
      formState.causal_link = document.getElementById("q-causal-link").value;
      formState.notes = {
        observations: document.getElementById("note-observations").value.trim(),
        intervention_description: document.getElementById("note-intervention").value.trim(),
        primary_zone_description: document.getElementById("note-pzone").value.trim(),
        secondary_zone_description: document.getElementById("note-szone").value.trim(),
        reasoning_notes: document.getElementById("note-reasoning").value.trim()
      };

      const payload = {
        event_id: currentEventId,
        slot: currentRole,
        reviewer_id: rId,
        observed_event_type: formState.event_type,
        criteria_evaluations: formState.criteria,
        causal_link_confidence: formState.causal_link,
        reviewer_notes: formState.notes,
        label_decision: formState.label_decision
      };

      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const respData = await res.json();

      if (respData.success) {
        alertBox.className = "alert-box success";
        alertBox.textContent = "SUCCESS: " + respData.message;
        await loadEvents();
        await loadFormForCurrentRole();
      } else {
        alertBox.className = "alert-box error";
        alertBox.textContent = "VALIDATION REJECTED: " + respData.message;
      }
    }

    window.onload = init;
  </script>
</body>
</html>
"""


ALLOWED_VIDEO_CLIPS = {"before.mp4", "intervention.mp4", "after.mp4"}


def parse_rfc7233_byte_range(range_header: str, file_size: int):
    """
    Parses an RFC 7233 Range header.
    Returns:
      (start, end) tuple if satisfiable,
      "UNSATISFIABLE" if unsatisfiable (should return 416),
      None if header is invalid or missing.
    """
    if not range_header or not range_header.startswith("bytes="):
        return None

    val = range_header[len("bytes="):].strip()
    if "," in val:
        val = val.split(",")[0].strip()

    parts = val.split("-")
    if len(parts) != 2:
        return None

    first_str, last_str = parts[0].strip(), parts[1].strip()

    if not first_str and not last_str:
        return None

    if not first_str:
        # Suffix range: bytes=-N (requesting last N bytes)
        try:
            suffix_len = int(last_str)
        except ValueError:
            return None
        if suffix_len <= 0:
            return "UNSATISFIABLE"
        start = max(0, file_size - suffix_len)
        end = file_size - 1
        return (start, end)

    elif not last_str:
        # Open-ended range: bytes=N-
        try:
            start = int(first_str)
        except ValueError:
            return None
        if start < 0 or start >= file_size:
            return "UNSATISFIABLE"
        end = file_size - 1
        return (start, end)

    else:
        # Explicit range: bytes=N-M
        try:
            start = int(first_str)
            end = int(last_str)
        except ValueError:
            return None
        if start < 0 or start >= file_size or start > end:
            return "UNSATISFIABLE"
        end = min(end, file_size - 1)
        return (start, end)


class ReviewRequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Suppress noisy standard output logs
        return

    def do_HEAD(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(HTML_PAGE.encode("utf-8"))))
            self.end_headers()
            return

        elif path.startswith("/video/"):
            parts = path.strip("/").split("/")
            if len(parts) >= 3:
                event_id, clip_name = parts[1], parts[2]
                self.handle_video_stream(event_id, clip_name, is_head=True)
                return

        elif path == "/api/status" or path == "/api/events" or path.startswith("/api/event/") or path.startswith("/api/form/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return

        self.send_error(404, "Not Found")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            body = HTML_PAGE.encode("utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        elif path == "/api/status":
            self.handle_api_status()
            return

        elif path == "/api/events":
            self.handle_api_events()
            return

        elif path.startswith("/api/event/"):
            event_id = path.split("/api/event/")[1]
            self.handle_api_event_detail(event_id)
            return

        elif path.startswith("/api/form/"):
            event_id = path.split("/api/form/")[1]
            query = urllib.parse.parse_qs(parsed.query)
            slot = query.get("slot", ["REVIEWER_1"])[0]
            reviewer_id = query.get("reviewer_id", [""])[0]
            self.handle_api_form_get(event_id, slot, reviewer_id)
            return

        elif path.startswith("/video/"):
            parts = path.strip("/").split("/")
            if len(parts) >= 3:
                event_id, clip_name = parts[1], parts[2]
                self.handle_video_stream(event_id, clip_name, is_head=False)
                return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/submit":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8"))
            except Exception as e:
                self.send_json_response({"success": False, "message": f"Malformed JSON: {e}"}, status=400)
                return

            self.handle_api_submit(data)
            return

        self.send_error(404, "Not Found")

    def send_json_response(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def handle_api_status(self):
        eligible = get_eligible_events()
        res = {
            "total_union_events": 51,
            "eligible_events": len(eligible),
            "ineligible_events": 13,
            "reviewer_1_completed": 0,
            "reviewer_2_completed": 0,
            "consensus_reached": 0,
            "disagreements": 0,
            "adjudicated": 0,
            "pending": len(eligible)
        }
        for ev in eligible:
            st = get_event_review_status(ev["union_id"])
            if st["reviewer_1_status"] == "COMPLETED":
                res["reviewer_1_completed"] += 1
            if st["reviewer_2_status"] == "COMPLETED":
                res["reviewer_2_completed"] += 1
            if st["adjudication_status"] == "CONSENSUS_REACHED":
                res["consensus_reached"] += 1
            elif st["adjudication_status"] == "ADJUDICATION_REQUIRED":
                res["disagreements"] += 1
            elif st["adjudication_status"] == "ADJUDICATED":
                res["adjudicated"] += 1
        self.send_json_response(res)

    def handle_api_events(self):
        eligible = get_eligible_events()
        output = []
        for ev in eligible:
            st = get_event_review_status(ev["union_id"])
            output.append({
                "union_id": ev["union_id"],
                "scene_id": ev["scene_id"],
                "camera_id": ev["camera_id"],
                "status": st["adjudication_status"],
                "r1_status": st["reviewer_1_status"],
                "r2_status": st["reviewer_2_status"],
                "final_label": st["final_label"]
            })
        self.send_json_response(output)

    def handle_api_event_detail(self, event_id):
        # Prevent directory traversal
        if not event_id.startswith("UNION_") or "/" in event_id or ".." in event_id:
            self.send_json_response({"error": "Invalid event ID"}, status=400)
            return

        pkg_dir = ADJUDICATION_DIR / event_id
        meta_path = pkg_dir / "review_metadata.json"
        if not meta_path.exists():
            self.send_json_response({"error": "Event not found"}, status=404)
            return

        with open(meta_path) as f:
            meta = json.load(f)

        # STRICT BLINDING: Zero detector confidences, zero YOLO boxes, zero ByteTrack IDs, zero Model H values
        blinded_detail = {
            "event_id": meta.get("event_id"),
            "facility_scene": meta.get("facility_scene"),
            "camera_stream": meta.get("camera_stream"),
            "temporal_window_bounds": meta.get("temporal_window_bounds"),
            "spatial_zones": meta.get("spatial_zones"),
            "eligibility_status": meta.get("eligibility_status")
        }
        self.send_json_response(blinded_detail)

    def handle_api_form_get(self, event_id, slot, reviewer_id):
        if not event_id.startswith("UNION_") or "/" in event_id or ".." in event_id:
            self.send_json_response({"error": "Invalid event ID"}, status=400)
            return

        pkg_dir = ADJUDICATION_DIR / event_id
        if not pkg_dir.exists():
            self.send_json_response({"error": "Package not found"}, status=404)
            return

        if slot == "REVIEWER_1":
            f_path = pkg_dir / "reviewer_1_form.json"
            with open(f_path) as f:
                data = json.load(f)
            self.send_json_response(data)

        elif slot == "REVIEWER_2":
            # STRICT DOUBLE-BLIND ISOLATION: Reviewer 2 form only
            f_path = pkg_dir / "reviewer_2_form.json"
            with open(f_path) as f:
                data = json.load(f)
            self.send_json_response(data)

        elif slot == "ADJUDICATOR":
            f_path = pkg_dir / "adjudication_form.json"
            with open(f_path) as f:
                data = json.load(f)
            self.send_json_response(data)
        else:
            self.send_json_response({"error": "Invalid slot"}, status=400)

    def handle_api_submit(self, data):
        event_id = data.get("event_id", "")
        slot = data.get("slot")
        reviewer_id = data.get("reviewer_id")

        if not event_id.startswith("UNION_") or "/" in event_id or ".." in event_id:
            self.send_json_response({"success": False, "message": "Invalid event ID"}, status=400)
            return

        pkg_dir = ADJUDICATION_DIR / event_id
        if not pkg_dir.exists():
            self.send_json_response({"success": False, "message": "Event package not found"}, status=404)
            return

        # Check integrity
        ok, msg = verify_package_integrity(pkg_dir)
        if not ok:
            self.send_json_response({"success": False, "message": f"Package integrity error: {msg}"}, status=400)
            return

        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        if slot in ["REVIEWER_1", "REVIEWER_2"]:
            success, err_or_msg = submit_reviewer_form(pkg_dir, slot, reviewer_id, data, session_id, now_iso)
            if success:
                self.send_json_response({"success": True, "message": err_or_msg})
            else:
                self.send_json_response({"success": False, "message": err_or_msg})

        elif slot == "ADJUDICATOR":
            success, err_or_msg = submit_adjudication(
                pkg_dir, reviewer_id, data.get("label_decision"),
                data.get("reviewer_notes", {}),
                data.get("criteria_evaluations", {}).get("evidence_quality", "HIGH"),
                data.get("causal_link_confidence", "PLAUSIBLE_BUT_UNCONFIRMED"),
                session_id, now_iso
            )
            if success:
                self.send_json_response({"success": True, "message": err_or_msg})
            else:
                self.send_json_response({"success": False, "message": err_or_msg})
        else:
            self.send_json_response({"success": False, "message": "Invalid reviewer slot"}, status=400)

    def handle_video_stream(self, event_id: str, clip_name: str, is_head: bool = False):
        # Security: Prevent directory traversal
        if clip_name not in ALLOWED_VIDEO_CLIPS:
            self.send_error(403, "Forbidden clip requested")
            return

        if not event_id.startswith("UNION_") or "/" in event_id or ".." in event_id:
            self.send_error(400, "Invalid event ID")
            return

        pkg_dir = ADJUDICATION_DIR / event_id
        clip_path = pkg_dir / clip_name
        if not clip_path.exists() or not clip_path.is_file():
            self.send_error(404, "Video clip not found")
            return

        file_size = clip_path.stat().st_size
        range_header = self.headers.get("Range")

        if range_header:
            range_res = parse_rfc7233_byte_range(range_header, file_size)

            if range_res == "UNSATISFIABLE":
                self.send_response(416, "Range Not Satisfiable")
                self.send_header("Content-Range", f"bytes */{file_size}")
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            elif range_res is not None:
                start, end = range_res
                chunk_len = end - start + 1

                self.send_response(206, "Partial Content")
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(chunk_len))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()

                if is_head:
                    return

                with open(clip_path, "rb") as f:
                    f.seek(start)
                    bytes_remaining = chunk_len
                    while bytes_remaining > 0:
                        read_size = min(64 * 1024, bytes_remaining)
                        chunk = f.read(read_size)
                        if not chunk:
                            break
                        try:
                            self.wfile.write(chunk)
                        except (BrokenPipeError, ConnectionResetError):
                            break
                        bytes_remaining -= len(chunk)
                return

        # Full Request (Status 200)
        self.send_response(200, "OK")
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        if is_head:
            return

        with open(clip_path, "rb") as f:
            while chunk := f.read(64 * 1024):
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break


def run_server(port=DEFAULT_PORT):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, ReviewRequestHandler)
    print("=" * 70)
    print("  SAFETY BACKFIRE AI — HUMAN ADJUDICATION DASHBOARD SERVER (V3.4-C)")
    print("=" * 70)
    print(f"  Server running locally at: http://127.0.0.1:{port}/")
    print(f"  Eligible Events Available: 38 (Deterministic order)")
    print(f"  Blinding Protocol:         Strictly Active (Zero AI scores / No YOLO)")
    print(f"  Reviewer Isolation:        Reviewer 2 Isolated from Reviewer 1")
    print("  Press Ctrl+C to terminate server.")
    print("=" * 70)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nReview server stopped gracefully.")
        httpd.server_close()


if __name__ == "__main__":
    port = DEFAULT_PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
