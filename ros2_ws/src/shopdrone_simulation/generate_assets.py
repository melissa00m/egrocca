#!/usr/bin/env python3
"""
ShopDrone Asset Generator
Generates high-resolution PBR textures and 3D Wavefront OBJ models
for Gazebo Harmonic simulation.
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

TEX_DIR = "/home/mphatic/Desktop/group project gazebo/ros2_ws/src/shopdrone_simulation/materials/textures"
MESH_DIR = "/home/mphatic/Desktop/group project gazebo/ros2_ws/src/shopdrone_simulation/meshes"
DRONE_TEX_DIR = "/home/mphatic/Desktop/group project gazebo/ros2_ws/src/shopdrone_simulation/models/shopdrone/materials/textures"

os.makedirs(TEX_DIR, exist_ok=True)
os.makedirs(MESH_DIR, exist_ok=True)
os.makedirs(DRONE_TEX_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. GENERATE TEXTURES
# -------------------------------------------------------------

def generate_helipad():
    img = Image.new('RGB', (1024, 1024), color=(35, 38, 42))
    draw = ImageDraw.Draw(img)
    
    # Concrete pad texture pattern
    for y in range(0, 1024, 4):
        v = 35 + (y % 13) - 6
        draw.line([(0, y), (1024, y)], fill=(v, v + 2, v + 4))

    # Diagonal hazard yellow/black border
    stripe_w = 40
    border_thick = 70
    for i in range(-1024, 2048, stripe_w * 2):
        draw.polygon([(i, 0), (i + stripe_w, 0), (i + stripe_w - border_thick, border_thick), (i - border_thick, border_thick)], fill=(240, 190, 10))
        draw.polygon([(i, 1024 - border_thick), (i + stripe_w, 1024 - border_thick), (i + stripe_w - border_thick, 1024), (i - border_thick, 1024)], fill=(240, 190, 10))
        draw.polygon([(0, i), (border_thick, i - border_thick), (border_thick, i + stripe_w - border_thick), (0, i + stripe_w)], fill=(240, 190, 10))
        draw.polygon([(1024 - border_thick, i - border_thick), (1024, i), (1024, i + stripe_w), (1024 - border_thick, i + stripe_w - border_thick)], fill=(240, 190, 10))

    # Inner circular boundary line
    draw.ellipse([90, 90, 934, 934], outline=(220, 220, 220), width=10)
    
    # Outer red circle
    draw.ellipse([140, 140, 884, 884], fill=(185, 28, 28), outline=(240, 240, 240), width=14)
    # Inner dark disc
    draw.ellipse([210, 210, 814, 814], fill=(28, 32, 38), outline=(240, 190, 10), width=8)

    # Large Helipad "H"
    h_col = (255, 255, 255)
    # Left vertical leg
    draw.rectangle([340, 310, 420, 714], fill=h_col)
    # Right vertical leg
    draw.rectangle([604, 310, 684, 714], fill=h_col)
    # Horizontal crossbar
    draw.rectangle([340, 472, 684, 552], fill=h_col)

    # Orientation crosshairs
    draw.line([(512, 100), (512, 190)], fill=(255, 215, 0), width=8)
    draw.line([(512, 834), (512, 924)], fill=(255, 215, 0), width=8)
    draw.line([(100, 512), (190, 512)], fill=(255, 215, 0), width=8)
    draw.line([(834, 512), (924, 512)], fill=(255, 215, 0), width=8)

    # Stenciled labeling
    draw.text((250, 235), "SHOPDRONE LOGISTICS HUB #01", fill=(240, 240, 240))
    draw.text((370, 735), "MAX TAKEOFF WT: 25 KG", fill=(240, 190, 10))
    draw.text((495, 115), "N", fill=(255, 255, 255))
    draw.text((495, 895), "S", fill=(255, 255, 255))
    draw.text((115, 495), "W", fill=(255, 255, 255))
    draw.text((895, 495), "E", fill=(255, 255, 255))

    path = os.path.join(TEX_DIR, 'helipad_hub.png')
    img.save(path)
    img.save(os.path.join(DRONE_TEX_DIR, 'helipad_hub.png'))
    print("Created:", path)

def generate_customer_pad():
    img = Image.new('RGB', (1024, 1024), color=(45, 48, 40))
    draw = ImageDraw.Draw(img)

    # Bullseye target rings
    draw.ellipse([80, 80, 944, 944], fill=(20, 24, 20), outline=(240, 200, 20), width=18)
    draw.ellipse([180, 180, 844, 844], fill=(30, 80, 40), outline=(255, 255, 255), width=12)
    draw.ellipse([290, 290, 734, 734], fill=(20, 24, 20), outline=(240, 200, 20), width=14)
    draw.ellipse([390, 390, 634, 634], fill=(220, 40, 30), outline=(255, 255, 255), width=12)
    draw.ellipse([470, 470, 554, 554], fill=(255, 255, 255))

    # Crosshairs
    draw.line([(512, 100), (512, 924)], fill=(255, 255, 255), width=6)
    draw.line([(100, 512), (924, 512)], fill=(255, 255, 255), width=6)

    # Stenciled labeling
    draw.text((220, 130), "CUSTOMER SAFE DROP TARGET - WARD 4", fill=(255, 255, 255))
    draw.text((280, 860), "STAND CLEAR - ENTER OTP ON ARRIVAL", fill=(240, 200, 20))

    path = os.path.join(TEX_DIR, 'customer_pad.png')
    img.save(path)
    print("Created:", path)

def generate_solar_panel():
    img = Image.new('RGB', (1024, 1024), color=(18, 30, 60))
    draw = ImageDraw.Draw(img)

    # Metal aluminum border frame
    draw.rectangle([0, 0, 1024, 1024], outline=(180, 190, 200), width=24)

    # Grid of 6 x 10 solar cells
    cols = 6
    rows = 10
    pad = 12
    cw = (1024 - 48 - (cols - 1) * pad) / cols
    rh = (1024 - 48 - (rows - 1) * pad) / rows

    for r in range(rows):
        for c in range(cols):
            x1 = 24 + c * (cw + pad)
            y1 = 24 + r * (rh + pad)
            x2 = x1 + cw
            y2 = y1 + rh
            # Cell base silicon
            draw.rectangle([x1, y1, x2, y2], fill=(12, 28, 70), outline=(40, 60, 110), width=2)
            # Silver busbar lines
            bus_x1 = x1 + cw * 0.3
            bus_x2 = x1 + cw * 0.7
            draw.line([(bus_x1, y1), (bus_x1, y2)], fill=(180, 210, 240), width=2)
            draw.line([(bus_x2, y1), (bus_x2, y2)], fill=(180, 210, 240), width=2)
            # Thin micro-grid horizontal wires
            for gy in range(int(y1) + 4, int(y2), 6):
                draw.line([(x1, gy), (x2, gy)], fill=(35, 60, 120), width=1)

    path = os.path.join(TEX_DIR, 'solar_panel.png')
    img.save(path)
    print("Created:", path)

def generate_container_metal():
    img = Image.new('RGB', (1024, 1024), color=(28, 55, 92))
    draw = ImageDraw.Draw(img)

    # Corrugated vertical ribbing with shading
    rib_width = 32
    for x in range(0, 1024, rib_width):
        draw.rectangle([x, 0, x + rib_width // 2, 1024], fill=(22, 45, 76))
        draw.rectangle([x + rib_width // 2, 0, x + rib_width, 1024], fill=(36, 70, 116))
        draw.line([(x, 0), (x, 1024)], fill=(12, 26, 46), width=2)
        draw.line([(x + rib_width - 1, 0), (x + rib_width - 1, 1024)], fill=(65, 110, 170), width=1)

    # Top/bottom frame beams
    draw.rectangle([0, 0, 1024, 40], fill=(18, 36, 62), outline=(10, 20, 36), width=4)
    draw.rectangle([0, 984, 1024, 1024], fill=(18, 36, 62), outline=(10, 20, 36), width=4)

    # Corner casting plates
    for (cx, cy) in [(0, 0), (960, 0), (0, 960), (960, 960)]:
        draw.rectangle([cx, cy, cx + 64, cy + 64], fill=(15, 25, 40), outline=(200, 200, 200), width=3)
        draw.ellipse([cx + 18, cy + 18, cx + 46, cy + 46], fill=(5, 10, 15))

    # Center white banner for branding
    draw.rectangle([100, 340, 924, 620], fill=(245, 245, 248), outline=(15, 25, 40), width=6)
    draw.rectangle([110, 350, 914, 380], fill=(185, 28, 28))
    draw.rectangle([110, 580, 914, 610], fill=(240, 190, 10))

    # Branding text
    draw.text((140, 400), "SHOPDRONE LOGISTICS & DISPATCH DEPOT", fill=(10, 20, 40))
    draw.text((140, 440), "NATIONAL UNIVERSITY OF SCIENCE AND TECHNOLOGY (NUST)", fill=(20, 40, 80))
    draw.text((140, 480), "RURAL HEALTH & GROCERY ACCESSIBILITY INITIATIVE", fill=(160, 20, 20))
    draw.text((140, 520), "STATION ID: MATOBO-WARD-04-HUB", fill=(30, 30, 30))

    # Diagonal hazard band at bottom
    for i in range(0, 1024, 60):
        draw.polygon([(i, 940), (i + 30, 940), (i, 980), (i - 30, 980)], fill=(240, 190, 10))

    path = os.path.join(TEX_DIR, 'container_metal.png')
    img.save(path)
    print("Created:", path)

def generate_thatch_straw():
    img = Image.new('RGB', (1024, 1024), color=(145, 110, 65))
    draw = ImageDraw.Draw(img)

    # Realistic combed layered thatch straw fibers
    for row in range(0, 1024, 40):
        # Shadow row underneath each thatch overhang
        draw.rectangle([0, row, 1024, row + 8], fill=(95, 70, 40))
        # Straw strands
        for x in range(0, 1024, 3):
            val = 140 + ((x * 17 + row * 31) % 55) - 25
            c = (val, int(val * 0.76), int(val * 0.44))
            draw.line([(x, row + 8), (x + ((x % 5) - 2), row + 40)], fill=c, width=2)

    path = os.path.join(TEX_DIR, 'thatch_straw.png')
    img.save(path)
    print("Created:", path)

def generate_mud_stone():
    img = Image.new('RGB', (1024, 1024), color=(165, 140, 115))
    draw = ImageDraw.Draw(img)

    # Masonry stone courses
    stone_h = 50
    for y in range(0, 1024, stone_h):
        draw.line([(0, y), (1024, y)], fill=(110, 90, 75), width=4)
        offset = (y // stone_h) % 2 * 60
        for x in range(offset, 1024 + 120, 110):
            draw.line([(x, y), (x, y + stone_h)], fill=(110, 90, 75), width=3)
            # Subtle stone shading
            stone_c = 160 + ((x * 7 + y * 13) % 40) - 20
            draw.rectangle([x + 3, y + 3, x + 107, y + stone_h - 3], fill=(stone_c, int(stone_c * 0.86), int(stone_c * 0.72)))

    path = os.path.join(TEX_DIR, 'mud_stone_wall.png')
    img.save(path)
    print("Created:", path)

def generate_wood_poles():
    img = Image.new('RGB', (512, 512), color=(90, 65, 45))
    draw = ImageDraw.Draw(img)
    for x in range(0, 512, 2):
        v = 85 + ((x * 37) % 35) - 15
        draw.line([(x, 0), (x, 512)], fill=(v, int(v * 0.72), int(v * 0.48)))
    path = os.path.join(TEX_DIR, 'wood_poles.png')
    img.save(path)
    print("Created:", path)

def generate_carbon_fiber():
    img = Image.new('RGB', (256, 256), color=(20, 20, 22))
    draw = ImageDraw.Draw(img)
    # 2x2 carbon weave
    step = 8
    for y in range(0, 256, step):
        for x in range(0, 256, step):
            if ((x // step) + (y // step)) % 2 == 0:
                c1 = (45, 46, 50)
                c2 = (18, 19, 21)
            else:
                c1 = (22, 23, 26)
                c2 = (55, 57, 62)
            draw.rectangle([x, y, x + step - 1, y + step - 1], fill=c1)
            draw.line([(x, y), (x + step - 1, y + step - 1)], fill=c2)

    path = os.path.join(TEX_DIR, 'carbon_fiber.png')
    img.save(path)
    img.save(os.path.join(DRONE_TEX_DIR, 'carbon_fiber.png'))
    print("Created:", path)

def generate_cargo_box():
    img = Image.new('RGB', (1024, 1024), color=(225, 110, 15))
    draw = ImageDraw.Draw(img)

    # Carbon reinforced edges
    draw.rectangle([0, 0, 1024, 1024], outline=(40, 40, 42), width=32)

    # Top Warning band
    for i in range(-100, 1100, 50):
        draw.polygon([(i, 32), (i + 25, 32), (i - 20, 110), (i - 45, 110)], fill=(20, 20, 22))

    # Center parcel info label
    draw.rectangle([80, 160, 944, 520], fill=(250, 250, 250), outline=(20, 20, 20), width=6)
    draw.text((110, 180), "SHOPDRONE PRIORITY RURAL DELIVERY", fill=(20, 20, 20))
    draw.text((110, 220), "CONSIGNEE: Hopewell Ndlovu (Matobo Ward 4)", fill=(20, 20, 20))
    draw.text((110, 260), "ORDER #1042: 2x Sugar 2kg, 1x Geisha, 1x Paracetamol", fill=(180, 20, 20))
    draw.text((110, 300), "DISPATCH HUB: Ward 4 Distribution Depot (GPS -20.553, 28.514)", fill=(60, 60, 60))
    draw.text((110, 340), "WEIGHT: 4.85 KG | STATUS: SECURED IN FLIGHT", fill=(20, 120, 20))

    # Faux barcode
    bx = 110
    for w in [3, 1, 4, 2, 6, 2, 1, 5, 3, 2, 4, 1, 5, 2, 3, 6, 2, 4, 2, 5, 3, 2, 4, 1, 5]:
        draw.rectangle([bx, 390, bx + w * 4, 490], fill=(10, 10, 10))
        bx += w * 4 + 8
    draw.text((110, 495), "* 1 0 4 2 - Z W - S H O P D R O N E *", fill=(10, 10, 10))

    # Lower Electronic Keypad Housing (SRS 4.8)
    draw.rectangle([80, 560, 944, 960], fill=(25, 28, 32), outline=(240, 190, 10), width=8)
    # LCD Display
    draw.rectangle([130, 590, 894, 690], fill=(10, 25, 15), outline=(60, 180, 80), width=4)
    draw.text((160, 610), "ENTER 4-DIGIT SECURE PIN:  [ * * * * ]", fill=(80, 240, 100))
    draw.text((160, 650), "TAMPER PROTECTION: ACTIVE (3-STRIKE LOCKOUT)", fill=(240, 80, 60))

    # Keypad Buttons (1-9, C, 0, OK)
    btn_labels = [["1", "2", "3", "CLEAR"], ["4", "5", "6", "CALL"], ["7", "8", "9", "HELP"], ["*", "0", "#", "UNLOCK"]]
    for r, row in enumerate(btn_labels):
        for c, lbl in enumerate(row):
            kx1 = 130 + c * 195
            ky1 = 710 + r * 58
            kx2 = kx1 + 175
            ky2 = ky1 + 48
            btn_col = (180, 40, 30) if lbl in ["CLEAR", "CALL"] else ((40, 160, 60) if lbl == "UNLOCK" else (45, 50, 58))
            draw.rectangle([kx1, ky1, kx2, ky2], fill=btn_col, outline=(180, 180, 180), width=2)
            draw.text((kx1 + 35, ky1 + 14), lbl, fill=(255, 255, 255))

    path = os.path.join(TEX_DIR, 'cargo_box.png')
    img.save(path)
    img.save(os.path.join(DRONE_TEX_DIR, 'cargo_box.png'))
    print("Created:", path)

def generate_dirt_road():
    img = Image.new('RGB', (1024, 1024), color=(180, 105, 55))
    draw = ImageDraw.Draw(img)

    # Red earth gravel variation
    for y in range(0, 1024, 4):
        v = 175 + (y % 23) - 10
        draw.line([(0, y), (1024, y)], fill=(v, int(v * 0.58), int(v * 0.32)))

    # Dual tire tracks (darker packed earth)
    track_left = [280, 420]
    track_right = [604, 744]
    for x1, x2 in [track_left, track_right]:
        for y in range(0, 1024, 2):
            val = 140 + ((y * 11) % 25)
            draw.line([(x1, y), (x2, y)], fill=(val, int(val * 0.52), int(val * 0.28)))

    # Dusty grassy edges
    for x in range(0, 140):
        draw.line([(x, 0), (x, 1024)], fill=(125, 120, 50))
    for x in range(884, 1024):
        draw.line([(x, 0), (x, 1024)], fill=(125, 120, 50))

    path = os.path.join(TEX_DIR, 'dirt_road.png')
    img.save(path)
    print("Created:", path)

# -------------------------------------------------------------
# 2. GENERATE 3D WAVEFRONT OBJ MESHES
# -------------------------------------------------------------

def generate_acacia_mesh():
    """Generates an African Umbrella Acacia Tree (*Acacia tortilis*) with layered flat canopies."""
    vertices = []
    faces = []

    def add_cylinder(cx, cy, z1, z2, r1, r2, sides=10):
        base_idx = len(vertices) + 1
        for i in range(sides):
            angle = 2.0 * math.pi * i / sides
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            # Bottom ring
            vertices.append((cx + r1 * cos_a, cy + r1 * sin_a, z1))
            # Top ring
            vertices.append((cx + r2 * cos_a, cy + r2 * sin_a, z2))
        for i in range(sides):
            p1 = base_idx + i * 2
            p2 = base_idx + ((i + 1) % sides) * 2
            p3 = p2 + 1
            p4 = p1 + 1
            faces.append((p1, p2, p3, p4))

    def add_canopy_disc(cx, cy, cz, radius, thickness=0.4, sides=16):
        base_idx = len(vertices) + 1
        # Center bottom & center top
        vertices.append((cx, cy, cz - thickness / 2))
        vertices.append((cx, cy, cz + thickness / 2))
        c_bot = base_idx
        c_top = base_idx + 1

        for i in range(sides):
            angle = 2.0 * math.pi * i / sides
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            vertices.append((cx + radius * cos_a, cy + radius * sin_a, cz))
        
        rim_start = base_idx + 2
        for i in range(sides):
            r1 = rim_start + i
            r2 = rim_start + ((i + 1) % sides)
            # Bottom triangle
            faces.append((c_bot, r2, r1))
            # Top triangle
            faces.append((c_top, r1, r2))

    # Main gnarled trunk
    add_cylinder(0, 0, 0.0, 3.0, 0.35, 0.25)
    # Split primary branches angled out
    add_cylinder(0.5, 0.4, 2.8, 5.0, 0.20, 0.12)
    add_cylinder(-0.6, 0.3, 2.8, 4.8, 0.20, 0.12)
    add_cylinder(0.1, -0.7, 2.8, 5.2, 0.20, 0.12)
    # Sub-branches reaching out wide
    add_cylinder(1.4, 1.0, 4.8, 6.2, 0.12, 0.08)
    add_cylinder(-1.5, 0.8, 4.6, 6.0, 0.12, 0.08)
    add_cylinder(0.2, -1.6, 5.0, 6.4, 0.12, 0.08)

    # Wide horizontal flat umbrella foliage canopies
    add_canopy_disc(1.8, 1.2, 6.3, 2.6, thickness=0.55)
    add_canopy_disc(-1.9, 0.9, 6.1, 2.8, thickness=0.6)
    add_canopy_disc(0.3, -1.9, 6.5, 2.9, thickness=0.6)
    add_canopy_disc(0.0, 0.0, 6.8, 3.8, thickness=0.7) # Master upper umbrella crown

    obj_path = os.path.join(MESH_DIR, 'acacia_tree.obj')
    with open(obj_path, 'w') as f:
        f.write("# ShopDrone Acacia Umbrella Tree OBJ\n")
        for v in vertices:
            f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
        for face in faces:
            if len(face) == 4:
                f.write(f"f {face[0]} {face[1]} {face[2]} {face[3]}\n")
            elif len(face) == 3:
                f.write(f"f {face[0]} {face[1]} {face[2]}\n")
    print("Created:", obj_path)

def generate_kopje_rocks():
    """Generates natural Matobo granite balancing rocks."""
    vertices = []
    faces = []

    def add_boulder(cx, cy, cz, rx, ry, rz, rings=8, sectors=12):
        base_idx = len(vertices) + 1
        for r in range(rings + 1):
            theta = math.pi * r / rings
            sin_t = math.sin(theta)
            cos_t = math.cos(theta)
            for s in range(sectors):
                phi = 2.0 * math.pi * s / sectors
                # Asymmetric granite boulder wobble
                wobble = 1.0 + 0.12 * math.sin(s * 3) + 0.08 * math.cos(r * 2)
                vx = cx + rx * wobble * sin_t * math.cos(phi)
                vy = cy + ry * wobble * sin_t * math.sin(phi)
                vz = cz + rz * wobble * cos_t
                vertices.append((vx, vy, vz))
        
        for r in range(rings):
            for s in range(sectors):
                p1 = base_idx + r * sectors + s
                p2 = base_idx + r * sectors + ((s + 1) % sectors)
                p3 = base_idx + (r + 1) * sectors + ((s + 1) % sectors)
                p4 = base_idx + (r + 1) * sectors + s
                faces.append((p1, p2, p3, p4))

    # Base granite rock
    add_boulder(0, 0, 1.8, 3.2, 2.8, 1.8)
    # Middle balancing stone
    add_boulder(0.3, -0.2, 4.4, 2.2, 2.0, 1.4)
    # Top balancing stone (perched at angle)
    add_boulder(0.1, 0.4, 6.4, 1.6, 1.5, 1.1)

    obj_path = os.path.join(MESH_DIR, 'kopje_rocks.obj')
    with open(obj_path, 'w') as f:
        f.write("# ShopDrone Matobo Kopje Rocks OBJ\n")
        for v in vertices:
            f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
        for face in faces:
            f.write(f"f {face[0]} {face[1]} {face[2]} {face[3]}\n")
    print("Created:", obj_path)

def generate_propeller_mesh():
    """Generates an aerodynamic folding carbon drone propeller blade."""
    vertices = []
    faces = []

    # Propeller central hub
    sides = 12
    hub_r = 0.02
    hub_h = 0.015
    base_idx = len(vertices) + 1
    for i in range(sides):
        ang = 2 * math.pi * i / sides
        vertices.append((hub_r * math.cos(ang), hub_r * math.sin(ang), -hub_h / 2))
        vertices.append((hub_r * math.cos(ang), hub_r * math.sin(ang), hub_h / 2))
    for i in range(sides):
        p1 = base_idx + i * 2
        p2 = base_idx + ((i + 1) % sides) * 2
        p3 = p2 + 1
        p4 = p1 + 1
        faces.append((p1, p2, p3, p4))

    # Two aerodynamic twisted blades
    def add_blade(direction=1.0):
        blade_len = 0.18
        steps = 6
        b_idx = len(vertices) + 1
        for s in range(steps + 1):
            t = s / steps
            dist = (hub_r + t * (blade_len - hub_r)) * direction
            chord = 0.028 * (1.0 - 0.4 * t)
            pitch_angle = math.radians(16.0 * (1.0 - 0.5 * t))
            cos_p = math.cos(pitch_angle)
            sin_p = math.sin(pitch_angle)

            # Leading & trailing edges
            vertices.append((dist, -chord / 2 * cos_p, -chord / 2 * sin_p))
            vertices.append((dist, chord / 2 * cos_p, chord / 2 * sin_p))
        
        for s in range(steps):
            p1 = b_idx + s * 2
            p2 = b_idx + (s + 1) * 2
            p3 = p2 + 1
            p4 = p1 + 1
            faces.append((p1, p2, p3, p4))

    add_blade(1.0)
    add_blade(-1.0)

    obj_path = os.path.join(MESH_DIR, 'propeller.obj')
    with open(obj_path, 'w') as f:
        f.write("# ShopDrone Propeller Blade OBJ\n")
        for v in vertices:
            f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
        for face in faces:
            f.write(f"f {face[0]} {face[1]} {face[2]} {face[3]}\n")
    
    # Also copy to model folder
    drone_mesh = os.path.join("/home/mphatic/Desktop/group project gazebo/ros2_ws/src/shopdrone_simulation/models/shopdrone/meshes", "propeller.obj")
    with open(drone_mesh, 'w') as f:
        f.write("# ShopDrone Propeller Blade OBJ\n")
        for v in vertices:
            f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
        for face in faces:
            f.write(f"f {face[0]} {face[1]} {face[2]} {face[3]}\n")
    print("Created:", obj_path)
    print("Created:", drone_mesh)


if __name__ == '__main__':
    print("Generating photorealistic PBR textures...")
    generate_helipad()
    generate_customer_pad()
    generate_solar_panel()
    generate_container_metal()
    generate_thatch_straw()
    generate_mud_stone()
    generate_wood_poles()
    generate_carbon_fiber()
    generate_cargo_box()
    generate_dirt_road()

    print("\nGenerating 3D Wavefront OBJ models...")
    generate_acacia_mesh()
    generate_kopje_rocks()
    generate_propeller_mesh()
    print("\nAll assets successfully generated!")
