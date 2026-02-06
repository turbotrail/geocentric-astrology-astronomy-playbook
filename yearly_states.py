import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
from skyfield.api import load

# ----------------------
# Font Configuration (Tamil Support)
# ----------------------
# Use Tamil MN, fallback to sans-serif for symbols
plt.rcParams['font.family'] = ['Tamil MN', 'sans-serif']

# ----------------------
# Constants
# ----------------------
NAK_SIZE = 360 / 27   # 13.3333 degrees
TITHI_SIZE = 12       # 12 degrees
NAKSHATRAS = [
    "அஸ்வினி", "பரணி", "கார்த்திகை",
    "ரோகிணி", "மிருகசீரிடம்", "திருவாதிரை",
    "புனர்பூசம்", "பூசம்", "ஆயில்யம்",
    "மகம்", "பூரம்", "உத்திரம்",
    "ஹஸ்தம்", "சித்திரை", "சுவாதி",
    "விசாகம்", "அனுஷம்", "கேட்டை",
    "மூலம்", "பூராடம்", "உத்திராடம்",
    "திருவோணம்", "அவிட்டம்", "சதயம்",
    "பூரட்டாதி", "உத்திரட்டாதி", "ரேவதி"
]

# Tithi Names (Root)
TITHI_ROOTS = [
    "பிரதமை", "துவிதியை", "திருதியை", "சதுர்த்தி", "பஞ்சமி",
    "சஷ்டி", "சப்தமி", "அஷ்டமி", "நவமி", "தசமி",
    "ஏகாதசி", "துவாதசி", "திரயோதசி", "சதுர்த்தசி", "பௌர்ணமி", # 15
    "பிரதமை", "துவிதியை", "திருதியை", "சதுர்த்தி", "பஞ்சமி",
    "சஷ்டி", "சப்தமி", "அஷ்டமி", "நவமி", "தசமி",
    "ஏகாதசி", "துவாதசி", "திரயோதசி", "சதுர்த்தசி", "அமாவாசை"  # 30
]

def get_full_tithi_name(i):
    # i is 0-29 index from code logic
    # Tithi 1-15 (Valarpirai), 16-30 (Theipirai)
    tithi_num = i + 1
    root = TITHI_ROOTS[i]
    
    if tithi_num == 15: return "பௌர்ணமி"
    if tithi_num == 30: return "அமாவாசை"
    
    prefix = "வளர்பிறை" if tithi_num < 15 else "தேய்பிறை"
    return f"{prefix} {root}"

# ----------------------
# Core computations
# ----------------------
# Load NASA/JPL ephemeris
eph = load('de440s.bsp')
ts = load.timescale()

def true_ecliptic_longitudes(dt):
    """
    Returns (moon_lon, sun_lon) in degrees using NASA/JPL ephemeris.
    dt: timezone-aware datetime in UTC
    """
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    earth = eph['earth']
    moon = eph['moon']
    sun = eph['sun']

    moon_vec = earth.at(t).observe(moon)
    sun_vec = earth.at(t).observe(sun)

    _, moon_lon, _ = moon_vec.ecliptic_latlon()
    _, sun_lon, _ = sun_vec.ecliptic_latlon()

    # Lahiri Ayanamsa
    ayanamsa = 23.85 + (dt.year - 2000) * 0.01397
    return moon_lon.degrees - ayanamsa, sun_lon.degrees - ayanamsa

def get_indices(dt):
    m_lon, s_lon = true_ecliptic_longitudes(dt)
    
    # Wrap to 0-360
    m_lon %= 360
    s_lon %= 360
    
    nak_idx = int(m_lon // NAK_SIZE) # 0-26
    
    phase = (m_lon - s_lon) % 360
    tithi_idx = int(phase // TITHI_SIZE) # 0-29 (using 0-29 logic for array indexing)
    
    return nak_idx, tithi_idx

# ----------------------
# App UI
# ----------------------
st.set_page_config(page_title="Yearly Orbit Scanner", layout="wide")

st.title("🌌 Yearly Nakshatra-Tithi Trajectory Scanner")
st.markdown("""
This tool simulates the Moon's transit through all **810 possibilities** (27 Nakshatras × 30 Tithis) for a selected year.
It visualizes which states are visited and the path taken.
""")

year = st.number_input("Select Year", min_value=1900, max_value=2100, value=2026, step=1)

if st.button("Generate Trajectory"):
    st.write(f"Simulating trajectory for **{year}**... (Please wait)")
    
    # ----------------------
    # Simulation Loop
    # ----------------------
    start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    
    # Step size: 4 hours (6 samples per day * 365 = ~2190 points)
    # Enough to catch state changes (avg state duration ~20-24 hrs)
    step = timedelta(hours=4)
    
    times = []
    curr = start_date
    while curr < end_date:
        times.append(curr)
        curr += step
        
    n_points = len(times)
    nak_history = []
    tithi_history = []
    
    progress_bar = st.progress(0)
    
    for i, t in enumerate(times):
        n, ti = get_indices(t)
        nak_history.append(n)
        tithi_history.append(ti)
        
        if i % 100 == 0:
            progress_bar.progress(i / n_points)
            
    progress_bar.progress(1.0)
    
    # ----------------------
    # Visualization
    # ----------------------
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Plot Grid Logic
    # X axis: Nakshatra (0-26)
    # Y axis: Tithi (0-29)
    
    ax.plot(nak_history, tithi_history, color='blue', alpha=0.15, linewidth=0.8, marker='o', markersize=2)
    
    # Highlight start/end
    ax.scatter(nak_history[0], tithi_history[0], c='green', s=100, label='Start (Jan 1)', zorder=10)
    ax.scatter(nak_history[-1], tithi_history[-1], c='red', s=100, label='End (Dec 31)', zorder=10)
    
    # Labels
    ax.set_xticks(range(27))
    ax.set_xticklabels(NAKSHATRAS, rotation=90, fontsize=8)
    
    ax.set_yticks(range(30))
    # Numeric Tithi Labels
    ax.set_yticklabels([str(i+1) for i in range(30)], fontsize=8)
    
    ax.set_xlabel("Nakshatra (Space)")
    ax.set_ylabel("Tithi (Time/Phase)")
    ax.set_title(f"Annual State Trajectory - {year}")
    
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    st.pyplot(fig)

    # ----------------------
    # Radial Visualization (Spirograph)
    # ----------------------
    st.markdown("### 🌀 Radial 'Spirograph' View")
    st.info("Explanation: **Angle** = Nakshatra, **Distance** = Tithi. This reveals the cyclical pattern.")
    
    fig2, ax2 = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})
    
    # Map Data to Polar
    theta = np.array(nak_history) * (2 * np.pi / 27)
    r = np.array(tithi_history) + 10
    
    ax2.plot(theta, r, color='purple', alpha=0.3, linewidth=0.8)
    ax2.scatter(theta[0], r[0], c='green', s=100, label='Start', zorder=10)
    ax2.scatter(theta[-1], r[-1], c='red', s=100, label='End', zorder=10)
    
    # Grid & Labels
    ax2.set_xticks(np.linspace(0, 2*np.pi, 27, endpoint=False))
    ax2.set_xticklabels(NAKSHATRAS, fontsize=8)
    
    # Remove Radial labels (y-ticks) as Tithi numbers might cluster
    ax2.set_yticks([])
    ax2.spines['polar'].set_visible(False)
    
    ax2.set_title(f"Nakshatra-Tithi Cycle (Spirograph) - {year}", pad=20)
    
    st.pyplot(fig2)
    
    # Stats
    unique_states = set(zip(nak_history, tithi_history))
    coverage = len(unique_states) / (27 * 30) * 100
    st.success(f"**Analysis**: In {year}, the Moon visited **{len(unique_states)}** out of 810 possible states ({coverage:.1f}%).")
