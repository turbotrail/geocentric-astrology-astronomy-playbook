from manim import *
from skyfield.api import load, Topos
from datetime import datetime, timedelta, timezone
import numpy as np

import os

# Load Ephemeris (reuses existing file if present)
eph = load('de440s.bsp')
earth = eph['earth']
moon = eph['moon']
sun = eph['sun']
ts = load.timescale()

# Config
TARGET_YEAR = os.getenv("YEAR")
TARGET_MONTH = os.getenv("MONTH")

# Set Default Resolution to Full HD (1920x1080)
config.pixel_width = 1920
config.pixel_height = 1080
config.frame_rate = 60
# (Removed frame_height override to rely on standard sizing)

class OrbitScene(Scene):
    def construct(self):
        # ----------------------
        # Setup
        # ----------------------
        # (Camera config moved to global)

        # Parse Input Date
        now = datetime.now(timezone.utc)
        start_year = int(TARGET_YEAR) if TARGET_YEAR else now.year
        start_month = int(TARGET_MONTH) if TARGET_MONTH else now.month
        
        start_dt = datetime(start_year, start_month, 1, tzinfo=timezone.utc)
        
        # Title (Standard font size)
        title = Text("Geocentric Orbit", font_size=36).to_edge(UP)
        date_label = Text(f"{start_dt.strftime('%B %Y')}", font_size=24).next_to(title, DOWN)
        self.add(title, date_label)
        
        # Earth (Static Center)
        earth_dot = Dot(ORIGIN, color=BLUE, radius=0.15)
        earth_label = Text("Earth", font_size=16, color=BLUE).next_to(earth_dot, DOWN)
        self.add(earth_dot, earth_label)
        
        # ----------------------
        # Data Generation
        # ----------------------
        # Animate for 30 days starting from input date
        duration_days = 30
        steps_per_day = 4 # Precision
        total_steps = duration_days * steps_per_day
        
        times = []
        moon_positions = []
        sun_positions = []
        
        # Scaling Factors (Optimized for Standard Frame Height 8.0)
        # Moon distance ~0.00257 AU. Target ~0.8 units (Tiny to match user req).
        MOON_SCALE = 300
        
        # Sun distance ~1.0 AU. 
        # Max visual distance with exaggeration = ~1.25. 
        # Frame limit +/- 4.0. 
        # 1.25 * S < 4.0 => S < 3.2. Let's use 2.8 for safety.
        SUN_SCALE = 2.8
        
        # Exaggerate Eccentricity?
        # Earth orbit is nearly circular (e=0.0167). 
        # To make it LOOK elliptical, we exaggerate deviation from 1.0 AU.
        SUN_ECC_EXAGGERATION = 15.0 

        def get_visual_sun_dist(d_au):
             # Mean distance is approx 1.0
             # visual = 1.0 + (actual - 1.0) * factor
             return 1.0 + (d_au - 1.0) * SUN_ECC_EXAGGERATION
        
        for i in range(total_steps + 1):
            dt = start_dt + timedelta(days=i/steps_per_day)
            times.append(dt)
            t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute)
            
            # Geocentric Vectors
            _, m_lon, m_dist = earth.at(t).observe(moon).ecliptic_latlon()
            _, s_lon, s_dist = earth.at(t).observe(sun).ecliptic_latlon()
            
            # Moon Position
            mx = m_dist.au * MOON_SCALE * np.cos(m_lon.radians)
            my = m_dist.au * MOON_SCALE * np.sin(m_lon.radians)
            moon_positions.append(np.array([mx, my, 0]))
            
            # Sun Position (Exaggerated)
            s_dist_vis = get_visual_sun_dist(s_dist.au)
            sx = s_dist_vis * SUN_SCALE * np.cos(s_lon.radians)
            sy = s_dist_vis * SUN_SCALE * np.sin(s_lon.radians)
            sun_positions.append(np.array([sx, sy, 0]))

        # ----------------------
        # Background Orbits (Static)
        # ----------------------
        # 1. Full Year Sun Orbit (to show the complete ellipse)
        sun_orbit_points = []
        year_steps = 366 * 2 # 2 steps per day is enough for smooth static line
        for i in range(year_steps):
            dt_year = start_dt + timedelta(days=i/2)
            t_year = ts.utc(dt_year.year, dt_year.month, dt_year.day)
            _, s_lon, s_dist = earth.at(t_year).observe(sun).ecliptic_latlon()
            
            # Sun Position (Exaggerated)
            s_dist_vis = get_visual_sun_dist(s_dist.au)
            sx = s_dist_vis * SUN_SCALE * np.cos(s_lon.radians)
            sy = s_dist_vis * SUN_SCALE * np.sin(s_lon.radians)
            sun_orbit_points.append(np.array([sx, sy, 0]))
            
        sun_bg_path = VMobject()
        sun_bg_path.set_points_as_corners(sun_orbit_points)
        sun_bg_path.set_stroke(YELLOW, opacity=0.15, width=2)
        # Close the loop visually (it's roughly closed anyway)
        sun_bg_path.add_line_to(sun_orbit_points[0]) 

        # 2. Current Month Moon Orbit Path (The "Track" for this animation)
        moon_bg_path = VMobject()
        moon_bg_path.set_points_as_corners(moon_positions)
        moon_bg_path.set_stroke(GRAY, opacity=0.2, width=2)

        self.add(sun_bg_path, moon_bg_path)

        # ----------------------
        # Animation Objects
        # ----------------------
        
        # Scale Legend
        scale_text = MarkupText(
            f'<span color="{GRAY}">Moon Scale: 1x</span>\n'
            f'<span color="{YELLOW}">Sun Scale: ~1/100x (Eccentricity x15)</span>',
            font_size=16
        ).to_corner(DR)
        self.add(scale_text)

        # Moon
        moon_dot = Dot(moon_positions[0], color=GRAY, radius=0.1)
        moon_path = TracedPath(moon_dot.get_center, stroke_color=GRAY, stroke_opacity=0.5, dissipating_time=2)
        moon_label = Text("Moon", font_size=12).next_to(moon_dot, UP)
        moon_label.add_updater(lambda m: m.next_to(moon_dot, UP))
        
        # Sun
        # "Bigger Yellow Ball"
        sun_icon = Dot(sun_positions[0], radius=0.35, color=YELLOW)
        sun_label = Text("Sun", font_size=12, color=YELLOW).next_to(sun_icon, UP)
        sun_label.add_updater(lambda m: m.next_to(sun_icon, UP))
        
        # Sun Trace
        sun_path = TracedPath(sun_icon.get_center, stroke_color=YELLOW, stroke_opacity=0.3, dissipating_time=3)

        # Add a "ray" or line from Earth to Sun direction
        sun_Ray = always_redraw(lambda: Line(
            earth_dot.get_center(), 
            sun_icon.get_center(), 
            color=YELLOW, stroke_opacity=0.3
        ))
        
        # Add objects
        self.add(moon_path, moon_dot, moon_label)
        self.add(sun_path, sun_icon, sun_label, sun_Ray)
        
        # ----------------------
        # Animate
        # ----------------------
        run_time = 10 # seconds
        
        def update_objects(mob, alpha):
            # Alpha goes 0 to 1
            idx = int(alpha * (len(times) - 1))
            
            # Update Date Label
            current_time = times[idx]
            # Format: "15 January 2026"
            date_str = current_time.strftime("%d %B %Y")
            date_label.set_text(date_str)
            
            # Update Positions
            moon_dot.move_to(moon_positions[idx])
            sun_icon.move_to(sun_positions[idx])
            
        # Create a dummy animation that updates everything
        self.play(
            UpdateFromAlphaFunc(Mobject(), update_objects, run_time=run_time, rate_func=linear)
        )
        
        self.wait(1)
