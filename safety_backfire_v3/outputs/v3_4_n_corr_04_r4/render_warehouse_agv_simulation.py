#!/usr/bin/env python3
"""
Synthetic Warehouse & AGV Motion Simulation Video Generator.
Produces a photorealistic/vector Full HD (1920x1080 @ 30 FPS) MP4 video
simulating an industrial warehouse corridor, an AGV vehicle moving in 3D perspective,
an E-Stop de-energization event, and an optical tracking HUD.
"""

import math
import os
import sys
from pathlib import Path
import cv2
import numpy as np

OUTPUT_DIR = Path("/Users/xah187/Projects/safety-backfire-ai/outputs/v3_4_n_corr_04_r4")
SCRATCH_DIR = Path("/Users/xah187/.gemini/antigravity-ide/brain/466f5a34-2608-4f9d-8f34-b1f6e5e6c88b/scratch")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

TARGET_FILE = OUTPUT_DIR / "warehouse_agv_simulation.mp4"
SCRATCH_FILE = SCRATCH_DIR / "warehouse_agv_simulation.mp4"

WIDTH = 1920
HEIGHT = 1080
FPS = 30.0
TOTAL_FRAMES = 360  # 12.0 seconds

# Vanishing point for warehouse perspective
VP_X = WIDTH // 2       # 960
VP_Y = 400              # Horizon height

def get_projection(x_world, y_world, z_world):
    """
    Project 3D world coordinates (meters) to 2D screen pixels.
    x: -left, +right from center aisle (meters)
    y: 0 at floor, +upwards (meters)
    z: distance down aisle from camera (meters, > 0)
    """
    # Camera intrinsic focal scale
    f = 1200.0
    cam_height = 2.8  # camera mounted at 2.8m above floor
    
    if z_world <= 0.5:
        z_world = 0.5
        
    screen_x = int(VP_X + (x_world * f) / z_world)
    screen_y = int(VP_Y + ((cam_height - y_world) * f) / z_world)
    return screen_x, screen_y

def draw_warehouse_background():
    """Render the static 3D warehouse environment: concrete floor, ceiling, racks."""
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    
    # 1. Ceiling (dark industrial charcoal with overhead beams)
    img[0:VP_Y, :] = [28, 26, 24]
    
    # 2. Polished Concrete Floor
    for y in range(VP_Y, HEIGHT):
        # Subtle gradient from horizon to foreground
        ratio = (y - VP_Y) / (HEIGHT - VP_Y)
        gray = int(45 + 50 * (ratio ** 1.3))
        img[y, :] = [gray - 3, gray, gray + 4]
        
    # 3. Floor Perspective Grid & Safety Lines
    # Main aisle width: -3.5m to +3.5m (7m wide main aisle)
    for z in np.linspace(2.0, 45.0, 30):
        p_left = get_projection(-3.5, 0.0, z)
        p_right = get_projection(3.5, 0.0, z)
        if 0 <= p_left[1] < HEIGHT:
            cv2.line(img, p_left, p_right, (60, 65, 70), 1, cv2.LINE_AA)
            
    # Yellow Safety Boundary Lines on left and right aisle edges
    pts_left = [get_projection(-3.5, 0.0, z) for z in np.linspace(2.0, 45.0, 50)]
    pts_right = [get_projection(3.5, 0.0, z) for z in np.linspace(2.0, 45.0, 50)]
    for i in range(len(pts_left) - 1):
        cv2.line(img, pts_left[i], pts_left[i+1], (20, 180, 220), 4, cv2.LINE_AA)
        cv2.line(img, pts_right[i], pts_right[i+1], (20, 180, 220), 4, cv2.LINE_AA)
        
    # Cross-aisle junction at z = 18m to z = 24m (Zebra crossing / Secondary zone entrance)
    for z_cross in np.linspace(18.0, 24.0, 8):
        c_l = get_projection(-3.4, 0.0, z_cross)
        c_r = get_projection(3.4, 0.0, z_cross)
        cv2.line(img, c_l, c_r, (180, 185, 190), 3, cv2.LINE_AA)

    # 4. Storage Racks (Pallet racking structure on Left and Right)
    # Upright columns along aisle
    rack_z_stations = [4.0, 8.0, 12.0, 16.0, 26.0, 31.0, 36.0, 42.0]
    for rz in rack_z_stations:
        # Left rack uprights
        pt_base_l = get_projection(-3.6, 0.0, rz)
        pt_top_l = get_projection(-3.6, 6.0, rz)
        cv2.line(img, pt_base_l, pt_top_l, (180, 80, 30), 4, cv2.LINE_AA)  # Industrial blue/orange
        
        # Right rack uprights
        pt_base_r = get_projection(3.6, 0.0, rz)
        pt_top_r = get_projection(3.6, 6.0, rz)
        cv2.line(img, pt_base_r, pt_top_r, (180, 80, 30), 4, cv2.LINE_AA)

    # Horizontal rack shelf beams (3 tiers: y = 1.8m, 3.6m, 5.4m)
    for shelf_y in [1.8, 3.6, 5.4]:
        # Left shelves
        pts_s_l = [get_projection(-3.6, shelf_y, z) for z in np.linspace(3.0, 45.0, 40)]
        pts_s_r = [get_projection(3.6, shelf_y, z) for z in np.linspace(3.0, 45.0, 40)]
        for i in range(len(pts_s_l) - 1):
            cv2.line(img, pts_s_l[i], pts_s_l[i+1], (40, 120, 220), 3, cv2.LINE_AA)
            cv2.line(img, pts_s_r[i], pts_s_r[i+1], (40, 120, 220), 3, cv2.LINE_AA)

    # Shelved pallet cargo boxes (colored cubes on racks)
    for rz in [6.0, 10.0, 14.0, 28.0, 34.0, 40.0]:
        for sy in [0.1, 1.9, 3.7]:
            # Left cargo
            p1 = get_projection(-4.8, sy, rz)
            p2 = get_projection(-3.7, sy + 1.4, rz)
            cv2.rectangle(img, (p1[0], p2[1]), (p2[0], p1[1]), (60, 90, 140), -1)
            cv2.rectangle(img, (p1[0], p2[1]), (p2[0], p1[1]), (30, 50, 90), 1)
            
            # Right cargo
            p3 = get_projection(3.7, sy, rz)
            p4 = get_projection(4.8, sy + 1.4, rz)
            cv2.rectangle(img, (p3[0], p4[1]), (p4[0], p3[1]), (70, 110, 80), -1)
            cv2.rectangle(img, (p3[0], p4[1]), (p4[0], p3[1]), (30, 60, 40), 1)

    # High-Bay LED Lights along ceiling (glowing ellipses)
    for lz in [6.0, 14.0, 22.0, 30.0, 38.0]:
        lp = get_projection(0.0, 7.0, lz)
        radius = max(2, int(80.0 / lz))
        cv2.circle(img, lp, radius + 8, (120, 110, 100), -1)
        cv2.circle(img, lp, radius, (250, 250, 240), -1)

    return img

def render_agv_vehicle(frame, x, y, z, amber_angle, brake_lights_on, e_stop_active):
    """
    Render 3D box model of an industrial Automated Guided Vehicle (AGV/Forklift).
    Dimensions: width=1.4m, height=1.9m, length=2.4m
    """
    w_half = 0.7
    l_half = 1.2
    h = 1.85
    
    # 8 bounding vertices of AGV chassis in 3D
    corners_3d = [
        # Base (floor level)
        (x - w_half, y, z - l_half),  # 0: front-left
        (x + w_half, y, z - l_half),  # 1: front-right
        (x + w_half, y, z + l_half),  # 2: rear-right
        (x - w_half, y, z + l_half),  # 3: rear-left
        # Roof / Top
        (x - w_half, y + h, z - l_half),  # 4: top front-left
        (x + w_half, y + h, z - l_half),  # 5: top front-right
        (x + w_half, y + h, z + l_half),  # 6: top rear-right
        (x - w_half, y + h, z + l_half)   # 7: top rear-left
    ]
    
    pts_2d = [get_projection(cx, cy, cz) for cx, cy, cz in corners_3d]
    
    # Floor contact shadow (dark ellipse under AGV)
    center_proj = get_projection(x, 0.0, z)
    shadow_w = int(max(10, 700.0 / z))
    shadow_h = int(max(4, 250.0 / z))
    cv2.ellipse(frame, center_proj, (shadow_w, shadow_h), 0, 0, 360, (20, 22, 25), -1, cv2.LINE_AA)

    # Chassis Color: Safety Industrial Yellow with Charcoal Trims
    body_color = (25, 175, 235)       # High-vis yellow-orange
    trim_color = (40, 45, 50)         # Charcoal dark gray
    
    # Side faces
    # Left face: [0, 3, 7, 4]
    left_poly = np.array([pts_2d[0], pts_2d[3], pts_2d[7], pts_2d[4]], np.int32)
    cv2.fillPoly(frame, [left_poly], (20, 140, 190), cv2.LINE_AA)
    
    # Right face: [1, 2, 6, 5]
    right_poly = np.array([pts_2d[1], pts_2d[2], pts_2d[6], pts_2d[5]], np.int32)
    cv2.fillPoly(frame, [right_poly], (20, 150, 210), cv2.LINE_AA)
    
    # Rear face (facing camera): [3, 2, 6, 7]
    rear_poly = np.array([pts_2d[3], pts_2d[2], pts_2d[6], pts_2d[7]], np.int32)
    cv2.fillPoly(frame, [rear_poly], body_color, cv2.LINE_AA)
    cv2.polylines(frame, [rear_poly], True, trim_color, 2, cv2.LINE_AA)
    
    # Roof face: [4, 5, 6, 7]
    roof_poly = np.array([pts_2d[4], pts_2d[5], pts_2d[6], pts_2d[7]], np.int32)
    cv2.fillPoly(frame, [roof_poly], (30, 190, 250), cv2.LINE_AA)
    
    # Chevron safety hazard stripes on rear face
    p_bl = pts_2d[3]
    p_br = pts_2d[2]
    p_tl = pts_2d[7]
    p_tr = pts_2d[6]
    
    h_rear = abs(p_bl[1] - p_tl[1])
    w_rear = abs(p_br[0] - p_bl[0])
    if h_rear > 15 and w_rear > 20:
        stripe_y = p_bl[1] - int(h_rear * 0.35)
        cv2.line(frame, (p_bl[0] + 5, stripe_y), (p_br[0] - 5, stripe_y), (30, 30, 30), max(2, int(h_rear * 0.15)), cv2.LINE_AA)
        cv2.putText(frame, "AGV-04", (p_bl[0] + max(4, int(w_rear * 0.2)), stripe_y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, max(0.3, 3.5 / z), (30, 30, 30), 2, cv2.LINE_AA)

    # Brake Lights on rear (Red LEDs on left and right edges)
    b_light_color = (30, 30, 250) if brake_lights_on else (20, 20, 90)
    b_radius = max(2, int(45.0 / z))
    light_l = (pts_2d[3][0] + int(w_rear * 0.15), pts_2d[3][1] - int(h_rear * 0.5))
    light_r = (pts_2d[2][0] - int(w_rear * 0.15), pts_2d[2][1] - int(h_rear * 0.5))
    cv2.circle(frame, light_l, b_radius, b_light_color, -1, cv2.LINE_AA)
    cv2.circle(frame, light_r, b_radius, b_light_color, -1, cv2.LINE_AA)
    if brake_lights_on:
        # Glow halo
        cv2.circle(frame, light_l, b_radius + 4, (60, 60, 255), 2, cv2.LINE_AA)
        cv2.circle(frame, light_r, b_radius + 4, (60, 60, 255), 2, cv2.LINE_AA)

    # Rotating Amber Beacon on Roof Center
    roof_center = get_projection(x, y + h + 0.15, z)
    beacon_color = (0, 215, 255) if (math.sin(amber_angle) > 0 or e_stop_active) else (0, 100, 160)
    if e_stop_active and int(amber_angle * 3) % 2 == 0:
        beacon_color = (0, 0, 255)  # Flashing emergency RED under E-Stop
    b_sz = max(3, int(50.0 / z))
    cv2.circle(frame, roof_center, b_sz, beacon_color, -1, cv2.LINE_AA)
    cv2.circle(frame, roof_center, b_sz + 3, beacon_color, 1, cv2.LINE_AA)

    # 2D Bounding Box overlay (Target Detection Bounding Box for Optical Tracker test)
    min_x = min(pt[0] for pt in pts_2d) - 6
    max_x = max(pt[0] for pt in pts_2d) + 6
    min_y = min(pt[1] for pt in pts_2d) - 10
    max_y = max(pt[1] for pt in pts_2d) + 4
    
    box_color = (0, 240, 255)  # Cyan tracking box
    if e_stop_active:
        box_color = (0, 80, 255)  # Orange/Red during E-Stop
        
    cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), box_color, 2, cv2.LINE_AA)
    # Corner brackets
    corner_len = max(5, int((max_x - min_x) * 0.15))
    cv2.line(frame, (min_x, min_y), (min_x + corner_len, min_y), (255, 255, 255), 3)
    cv2.line(frame, (min_x, min_y), (min_x, min_y + corner_len), (255, 255, 255), 3)
    cv2.line(frame, (max_x, max_y), (max_x - corner_len, max_y), (255, 255, 255), 3)
    cv2.line(frame, (max_x, max_y), (max_x, max_y - corner_len), (255, 255, 255), 3)
    
    label_text = f"ID:AGV_04 [conf:0.98] z={z:.1f}m"
    cv2.putText(frame, label_text, (min_x, min_y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.48, box_color, 1, cv2.LINE_AA)

def draw_hud_overlay(frame, frame_idx, t_sec, velocity_mps, i_rms_amp, state_str, e_stop_active):
    """Render high-tech telemetry HUD overlay."""
    # Top HUD Bar
    cv2.rectangle(frame, (0, 0), (WIDTH, 70), (18, 18, 20), -1)
    cv2.line(frame, (0, 70), (WIDTH, 70), (45, 50, 55), 2)
    
    # Left: Camera & Site info
    cv2.putText(frame, "FACILITY: WH-026 | CAM: NORTH_CORRIDOR_01 [PTP SYNC LOCKED]", 
                (30, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (200, 210, 220), 1, cv2.LINE_AA)
    cv2.putText(frame, "OPTICAL BENCHMARK SIMULATION | 1920x1080 @ 30.00 FPS", 
                (30, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (120, 130, 140), 1, cv2.LINE_AA)
                
    # Center: Frame counter & Timecode
    timecode = f"TC: 00:00:{int(t_sec):02d}.{int((t_sec % 1.0) * 1000):03d}"
    frame_text = f"FRAME: #{frame_idx:04d} / #{TOTAL_FRAMES:04d}"
    cv2.putText(frame, timecode, (WIDTH // 2 - 140, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 230, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, frame_text, (WIDTH // 2 - 140, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (160, 170, 180), 1, cv2.LINE_AA)

    # Right: Operating State Badge
    badge_bg = (30, 120, 30) if not e_stop_active else (20, 20, 180)
    if "DEENERGIZED" in state_str:
        badge_bg = (160, 100, 0)
    cv2.rectangle(frame, (WIDTH - 420, 12), (WIDTH - 30, 58), badge_bg, -1)
    cv2.rectangle(frame, (WIDTH - 420, 12), (WIDTH - 30, 58), (255, 255, 255), 1)
    cv2.putText(frame, state_str, (WIDTH - 405, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

    # Bottom Telemetry Dashboard
    panel_y = HEIGHT - 110
    cv2.rectangle(frame, (0, panel_y), (WIDTH, HEIGHT), (16, 16, 18), -1)
    cv2.line(frame, (0, panel_y), (WIDTH, panel_y), (45, 50, 55), 2)
    
    # 1. Velocity Gauge
    v_kmh = velocity_mps * 3.6
    cv2.putText(frame, "VEHICLE TELEMETRY", (30, panel_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (140, 150, 160), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Velocity: {velocity_mps:4.2f} m/s ({v_kmh:4.1f} km/h)", 
                (30, panel_y + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (240, 240, 245), 2, cv2.LINE_AA)
    # Velocity bar
    v_ratio = min(1.0, max(0.0, velocity_mps / 2.5))
    cv2.rectangle(frame, (30, panel_y + 68), (350, panel_y + 82), (40, 45, 50), -1)
    cv2.rectangle(frame, (30, panel_y + 68), (int(30 + 320 * v_ratio), panel_y + 82), (0, 200, 255), -1)

    # 2. Stator Current & Persistence Monitor (CORR-04 Metrology display)
    cv2.putText(frame, "ELECTRICAL DE-ENERGIZATION (RMS-PROC-V1.0)", (420, panel_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (140, 150, 160), 1, cv2.LINE_AA)
    i_color = (80, 230, 120) if i_rms_amp <= 0.410 else (40, 100, 240)
    cv2.putText(frame, f"I_stator(RMS): {i_rms_amp:6.3f} A  [Guarded Limit <= 0.410 A]", 
                (420, panel_y + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.65, i_color, 2, cv2.LINE_AA)
    i_ratio = min(1.0, max(0.0, i_rms_amp / 45.0))
    cv2.rectangle(frame, (420, panel_y + 68), (780, panel_y + 82), (40, 45, 50), -1)
    cv2.rectangle(frame, (420, panel_y + 68), (int(420 + 360 * i_ratio), panel_y + 82), i_color, -1)

    # 3. Model H & Governance Notice
    cv2.putText(frame, "MODEL_H: k0=2.40 beta_d=0.08 beta_l=0.12 beta_pitch=0.22", 
                (840, panel_y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (140, 150, 160), 1, cv2.LINE_AA)
    cv2.putText(frame, "GOVERNANCE: SYNTHETIC TEST SIMULATION ONLY -- ZERO REAL FIELD DATA", 
                (840, panel_y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 180, 255), 1, cv2.LINE_AA)

    # 4. Crosshair at Center
    cv2.drawMarker(frame, (VP_X, VP_Y), (80, 90, 100), cv2.MARKER_CROSS, 20, 1)

def main():
    print(f"Generating Synthetic Warehouse Simulation Video: {WIDTH}x{HEIGHT} @ {FPS} FPS ({TOTAL_FRAMES} frames)...")
    
    # Pre-render static background to maximize rendering speed
    base_bg = draw_warehouse_background()
    
    # Video Writer (Use avc1 with fallback to mp4v)
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter(str(TARGET_FILE), fourcc, FPS, (WIDTH, HEIGHT))
    if not out.isOpened():
        print("Falling back to mp4v codec...")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(TARGET_FILE), fourcc, FPS, (WIDTH, HEIGHT))
        
    # Trajectory & Physical Kinematics Parameters
    # AGV travels down the aisle from z = 6.0m to z = 22.0m
    z_pos = 6.0
    velocity = 2.2      # m/s cruising velocity
    i_stator = 42.5     # Amperes RMS cruising current
    
    # E-stop trigger at frame 180 (t = 6.0s)
    e_stop_frame = 180
    e_stop_active = False
    
    for f in range(TOTAL_FRAMES):
        t = f / FPS
        frame = base_bg.copy()
        
        # Physical State Evolution
        if f < e_stop_frame:
            # Cruising phase
            z_pos += velocity * (1.0 / FPS)
            state_str = "STATE: NORMAL_CRUISE"
            brake_lights = False
            e_stop_active = False
            i_stator = 42.0 + 1.5 * math.sin(f * 0.4)
        else:
            # E-Stop Triggered phase
            e_stop_active = True
            brake_lights = True
            
            # Mechanical Deceleration (braking from 2.2 m/s to 0 m/s in 2.5s)
            brake_time = (f - e_stop_frame) / FPS
            velocity = max(0.0, 2.2 - (2.2 / 2.5) * brake_time)
            z_pos += velocity * (1.0 / FPS)
            
            # Electrical Stator Current Exponential Decay (tau_eff = 2.8 ms)
            # Decays from ~42 A down to noise floor (< 0.1 A) in ~20 ms
            decay_time_ms = brake_time * 1000.0
            tau_ms = 2.8
            if decay_time_ms < 60.0:
                i_stator = 42.0 * math.exp(-decay_time_ms / tau_ms) + 0.05 * math.sin(f * 1.5)
            else:
                i_stator = 0.05 + 0.02 * math.sin(f * 2.0)  # Residual noise floor
                
            if velocity > 0.0:
                state_str = "STATE: E_STOP_DECELERATING"
            else:
                if i_stator <= 0.410:
                    state_str = "STATE: TRACTION_DEENERGIZED_PERSISTED"
                else:
                    state_str = "STATE: KINETIC_STOP_WAITING_DEENERGIZATION"

        # Beacon rotation angle
        amber_angle = f * 0.35
        
        # Render AGV in 3D perspective
        render_agv_vehicle(frame, x=0.0, y=0.0, z=z_pos, 
                           amber_angle=amber_angle, 
                           brake_lights_on=brake_lights, 
                           e_stop_active=e_stop_active)
                           
        # Render Telemetry HUD
        draw_hud_overlay(frame, f + 1, t, velocity, i_stator, state_str, e_stop_active)
        
        out.write(frame)
        
        if (f + 1) % 60 == 0:
            print(f"Rendered frame {f+1}/{TOTAL_FRAMES} (t={t:.1f}s)...")
            
    out.release()
    print("Video encoding completed successfully.")
    
    # Also save a copy to the brain scratch directory
    import shutil
    shutil.copy2(TARGET_FILE, SCRATCH_FILE)
    print(f"Artifact copied to: {SCRATCH_FILE}")
    print(f"Target file: {TARGET_FILE} (Size: {os.path.getsize(TARGET_FILE)} bytes)")

if __name__ == "__main__":
    main()
