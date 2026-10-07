"""
Visualization Overlay module for Safety Backfire AI V0.8.
Renders:
- Floor-anchored dynamic safety halos (Caution/Danger).
- Footprint markers and trajectory trails.
- Dynamic proximity lines with real-time metric distance badges.
- Industrial safety telemetry HUD with live risk severity meters.
"""
import cv2
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

class RiskOverlay:
    def __init__(self, width: int = 640, height: int = 360):
        self.width = width
        self.height = height

    def render(
        self,
        frame: np.ndarray,
        frame_idx: int,
        time_sec: float,
        persons: Dict[int, Tuple[float, float]],       # id -> footprint
        forklifts: Dict[int, Tuple[float, float]],     # id -> footprint
        halos: Dict[int, Dict[str, Any]],              # id -> {'danger': (...), 'caution': (...)}
        trails: Dict[int, List[Tuple[float, float]]],  # id -> path points
        interactions: List[Dict[str, Any]],            # active interactions
    ) -> np.ndarray:
        out = frame.copy()
        overlay = out.copy()

        # 1. Draw Forklift Safety Halos on Floor (Semi-Transparent)
        for f_id, halo_data in halos.items():
            # Danger Zone (Red)
            (dcx, dcy), (drx, dry), dangle = halo_data["danger"]
            cv2.ellipse(overlay, (dcx, dcy), (drx, dry), dangle, 0, 360, (0, 0, 220), -1)

            # Caution Zone (Yellow)
            (ccx, ccy), (crx, cry), cangle = halo_data["caution"]
            cv2.ellipse(overlay, (ccx, ccy), (crx, cry), cangle, 0, 360, (0, 215, 255), 2)

        # Blend halos with 25% alpha for floor transparency
        cv2.addWeighted(overlay, 0.28, out, 0.72, 0, out)

        # 2. Draw Motion Trajectory Trails
        for tid, path in trails.items():
            if len(path) > 1:
                for i in range(1, len(path)):
                    pt1 = (int(path[i - 1][0]), int(path[i - 1][1]))
                    pt2 = (int(path[i][0]), int(path[i][1]))
                    alpha_color = (180, 180, 180)
                    cv2.line(out, pt1, pt2, alpha_color, 1, cv2.LINE_AA)

        # 3. Draw Footprint Anchors
        for p_id, (px, py) in persons.items():
            cv2.circle(out, (int(px), int(py)), 4, (255, 140, 0), -1)
            cv2.circle(out, (int(px), int(py)), 7, (255, 200, 0), 1)

        for f_id, (fx, fy) in forklifts.items():
            cv2.circle(out, (int(fx), int(fy)), 5, (0, 140, 255), -1)
            cv2.circle(out, (int(fx), int(fy)), 9, (0, 165, 255), 2)

        # 4. Draw Pairwise Proximity Lines & Distance Badges
        max_frame_severity = 0.0
        frame_status = "NORMAL"

        # Sort interactions so safe co-presence is drawn first,
        # followed by warnings, and critical near-misses on top
        severity_rank = {
            "CO_PRESENCE_SAFE": 1,
            "PROXIMITY_WARNING": 2,
            "NEAR_MISS_INCIDENT": 3,
        }
        sorted_interactions = sorted(
            interactions,
            key=lambda x: (severity_rank.get(x["event_type"], 0), x["severity_score"])
        )

        placed_badges: List[Tuple[int, int, int, int]] = []

        for inter in sorted_interactions:
            px, py = [int(v) for v in inter["person_footprint"]]
            fx, fy = [int(v) for v in inter["forklift_footprint"]]
            p_id = inter["person_id"]
            f_id = inter["forklift_id"]
            dist_m = inter["distance_meters"]
            severity = inter["severity_score"]
            event_type = inter["event_type"]

            if severity > max_frame_severity:
                max_frame_severity = severity

            if event_type == "NEAR_MISS_INCIDENT":
                line_color = (0, 0, 255) # Red
                line_thick = 3
                frame_status = "CRITICAL NEAR-MISS"
            elif event_type == "PROXIMITY_WARNING":
                line_color = (0, 220, 255) # Yellow
                line_thick = 2
                if frame_status != "CRITICAL NEAR-MISS":
                    frame_status = "PROXIMITY WARNING"
            else:
                line_color = (0, 200, 100) # Green
                line_thick = 1

            # Proximity line
            cv2.line(out, (px, py), (fx, fy), line_color, line_thick, cv2.LINE_AA)

            # Midpoint distance badge with pair identification
            mid_x = (px + fx) // 2
            mid_y = (py + fy) // 2
            badge_text = f"P{p_id}-F{f_id}: {dist_m:.2f}m"
            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.40, 1)

            bx, by = mid_x, mid_y
            x1, y1, x2, y2 = bx - 4, by - th - 4, bx + tw + 4, by + 4

            # Collision avoidance for overlapping badges
            for px1, py1, px2, py2 in placed_badges:
                if not (x2 < px1 or x1 > px2 or y2 < py1 or y1 > py2):
                    by = py2 + th + 6
                    if by > self.height - 15:
                        by = py1 - th - 6
                    x1, y1, x2, y2 = bx - 4, by - th - 4, bx + tw + 4, by + 4

            placed_badges.append((x1, y1, x2, y2))

            cv2.rectangle(out, (x1, y1), (x2, y2), (18, 20, 24), -1)
            cv2.rectangle(out, (x1, y1), (x2, y2), line_color, 1)
            cv2.putText(out, badge_text, (bx, by), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1, cv2.LINE_AA)

        # 5. Top Telemetry HUD
        hud = out.copy()
        cv2.rectangle(hud, (0, 0), (self.width, 34), (15, 18, 24), -1)
        cv2.addWeighted(hud, 0.85, out, 0.15, 0, out)
        cv2.line(out, (0, 34), (self.width, 34), (60, 65, 80), 1)

        # Status badge color
        if frame_status == "CRITICAL NEAR-MISS":
            badge_bg = (0, 0, 220)
            status_text = "[!] CRITICAL NEAR-MISS"
        elif frame_status == "PROXIMITY WARNING":
            badge_bg = (0, 165, 255)
            status_text = "[*] PROXIMITY ALERT"
        else:
            badge_bg = (30, 140, 50)
            status_text = "[OK] ZONE CLEAR"

        # Status badge
        cv2.rectangle(out, (8, 6), (195, 28), badge_bg, -1)
        cv2.putText(out, status_text, (14, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        # Telemetry stats
        telemetry = f"T: {time_sec:4.1f}s | Workers: {len(persons)} | Forklifts: {len(forklifts)} | Risk Index: {max_frame_severity:4.0f}%"
        cv2.putText(out, telemetry, (208, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 225, 235), 1, cv2.LINE_AA)

        return out
