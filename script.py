import streamlit as st
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
from skyfield.api import load
from math import atan2, degrees

# ----------------------
# Font Configuration (Tamil Support)
# ----------------------
# Use Tamil MN for Tamil text, fallback to sans-serif for symbols like degree sign
plt.rcParams['font.family'] = ['Tamil MN', 'sans-serif']

# ----------------------
# Constants
# ----------------------
# ----------------------
# Constants
# ----------------------
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

# Raasi Names (Zodiac Signs)
RAASI_NAMES = [
    "மேஷம்", "ரிஷபம்", "மிதுனம்", "கடகம்", 
    "சிம்மம்", "கன்னி", "துலாம்", "விருச்சிகம்", 
    "தனுசு", "மகரம்", "கும்பம்", "மீனம்"
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
    tithi_num = i + 1
    root = TITHI_ROOTS[i]
    if tithi_num == 15: return "பௌர்ணமி"
    if tithi_num == 30: return "அமாவாசை"
    prefix = "வளர்பிறை" if tithi_num < 15 else "தேய்பிறை"
    return f"{prefix} {root}"

NAK_SIZE = 360 / 27
TITHI_SIZE = 12

# ----------------------
# Core computations
# ----------------------
# Load NASA/JPL ephemeris (cached locally by Skyfield)
eph = load('de440s.bsp')
ts = load.timescale()

def true_ecliptic_longitudes(dt):
    """
    Returns (moon_lon, sun_lon) in degrees using NASA/JPL ephemeris.
    
    dt: timezone-aware datetime in UTC
    """
    t = ts.utc(
        dt.year, dt.month, dt.day,
        dt.hour, dt.minute, dt.second
    )

    earth = eph['earth']
    moon = eph['moon']
    sun = eph['sun']

    # TRUE geocentric astrometric vectors (no light-time / aberration correction)
    moon_vec = earth.at(t).observe(moon)
    sun_vec = earth.at(t).observe(sun)

    # Skyfield returns (lat, lon, distance)
    _, moon_lon, _ = moon_vec.ecliptic_latlon()
    _, sun_lon, _ = sun_vec.ecliptic_latlon()

    # Lahiri Ayanamsa (approximate formula)
    ayanamsa = 23.85 + (dt.year - 2000) * 0.01397

    # Return UNWRAPPED longitudes
    return moon_lon.degrees - ayanamsa, sun_lon.degrees - ayanamsa

def get_geocentric_data(dt):
    """
    Returns (moon_lon, moon_dist_au, sun_lon, sun_dist_au)
    Longitudes are Sidereal (Nirayana).
    """
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    earth = eph['earth']
    moon = eph['moon']
    sun = eph['sun']
    
    moon_vec = earth.at(t).observe(moon)
    sun_vec = earth.at(t).observe(sun)
    
    _, moon_lon, moon_dist = moon_vec.ecliptic_latlon()
    _, sun_lon, sun_dist = sun_vec.ecliptic_latlon()
    
    ayanamsa = 23.85 + (dt.year - 2000) * 0.01397
    return (
        moon_lon.degrees - ayanamsa, moon_dist.au,
        sun_lon.degrees - ayanamsa, sun_dist.au
    )

def nakshatra_index(moon_lon):
    return int(moon_lon // NAK_SIZE)

def raasi_index(lon):
    return int(lon // 30)

def tithi_index(moon_lon, sun_lon):
    phase = (moon_lon - sun_lon) % 360
    return int(phase // TITHI_SIZE) + 1

def get_moon_phase_name(tithi_i):
    """Map Tithi index (1-30) to descriptive moon phase."""
    if tithi_i == 30:
        return "அமாவாசை"
    elif tithi_i == 15:
        return "பௌர்ணமி"
    elif 1 <= tithi_i <= 7:
        return "வளர்பிறை (ஆரம்பம்)"
    elif 8 <= tithi_i <= 14:
        return "வளர்பிறை (முடிவு)"
    elif 16 <= tithi_i <= 22:
        return "தேய்பிறை (ஆரம்பம்)"
    else: # 23-29
        return "தேய்பிறை (முடிவு)"

# ----------------------
# UI
# ----------------------
st.set_page_config(page_title="Thiru Kanitham Panchangam", layout="wide")

st.title("🌙 Thiru Kanitham Panchangam")
st.caption("Nakshatra (Space) + Tithi (Time) | **Timezone: IST (UTC+05:30)**")

# Sidebar controls
IST = timezone(timedelta(hours=5, minutes=30))

if "selected_time" not in st.session_state:
    st.session_state.selected_time = datetime.now(IST).time()

if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.now(IST).date()

# Min/Max dates
min_date = datetime(1900, 1, 1).date()
max_date = datetime(2100, 12, 31).date()

date = st.sidebar.date_input(
    "Select Date (IST)",
    st.session_state.selected_date,
    min_value=min_date,
    max_value=max_date,
    key="date_picker"
)
time = st.sidebar.time_input(
    "Select Time (IST)",
    st.session_state.selected_time,
    key="time_picker"
)

st.session_state.selected_date = date
st.session_state.selected_time = time

# Combine to IST datetime
base_time_ist = datetime(
    date.year, date.month, date.day,
    time.hour, time.minute, time.second,
    tzinfo=IST
)

offset_hours = st.sidebar.slider(
    "Time Scrub (Hours)", -72, 72, 0, step=1
)

current_time_ist = base_time_ist + timedelta(hours=offset_hours)
current_time_utc = current_time_ist.astimezone(timezone.utc)

st.sidebar.markdown(f"**Selected Time (IST)**: `{current_time_ist.strftime('%Y-%m-%d %H:%M:%S')}`")

moon_lon, sun_lon = true_ecliptic_longitudes(current_time_utc)

# Wrapped versions
moon_lon_wrapped = moon_lon % 360
sun_lon_wrapped = sun_lon % 360

nak_i = nakshatra_index(moon_lon_wrapped)
tithi_i = tithi_index(moon_lon_wrapped, sun_lon_wrapped)
phase_name = get_moon_phase_name(tithi_i)

# ----------------------
# Visuals
# ----------------------
def draw_moon_phase(phase_angle_deg):
    """
    Draw a simple 2D moon phase.
    phase_angle_deg: 0 (New), 90 (First Quarter), 180 (Full), 270 (Last Quarter)
    """
    fig, ax = plt.subplots(figsize=(0.5, 0.5))
    ax.set_aspect('equal')
    ax.axis('off')
    # Remove whitespace
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    
    # Background: Dark circle (Shadow part)
    circle = plt.Circle((0, 0), 1, color='black')
    ax.add_artist(circle)
    
    # Set limits explicitly to avoid cropping/sector look
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    
    # Phase logic
    # ... (rest of logic)
    
    # Draw White Circle first
    if 0 < phase_angle_deg < 180: # Waxing
        # Right side is lit.
        # Draw semi-circle (Right half) white
        wedge1 = matplotlib.patches.Wedge((0, 0), 1, -90, 90, color='#F0F0F0') # Right half
        ax.add_artist(wedge1)
        
        lit_color = '#FFFFFF'
        shadow_color = 'black'
        
        w = np.cos(np.radians(phase_angle_deg)) # 1 at 0, 0 at 90, -1 at 180
        
        # Note: height=2 for radius 1 circle
        ellipse = matplotlib.patches.Ellipse((0, 0), width=2*abs(w), height=2, angle=0, 
                                             color=shadow_color if w > 0 else lit_color)
        ax.add_artist(ellipse)

    else: # Waning (180-360)
        # Lit from Left.
        # Base: Left White, Right Black.
        ax.add_patch(matplotlib.patches.Wedge((0, 0), 1, 90, 270, color='#FFFFFF'))
        
        w = np.cos(np.radians(phase_angle_deg))
        
        ellipse = matplotlib.patches.Ellipse((0, 0), width=2*abs(w), height=2, angle=0,
                                             color='#FFFFFF' if w < 0 else 'black')
        ax.add_artist(ellipse)
            
    fig.patch.set_alpha(0)
    return fig

# ----------------------
# State display
# ----------------------
col1, col2, col3, col4, col5, col6 = st.columns(6)
# Calculate phase angle (0-360)
phase_ang = (moon_lon_wrapped - sun_lon_wrapped) % 360
raasi_i = raasi_index(moon_lon_wrapped)

col1.metric("Nakshatra", NAKSHATRAS[nak_i])
col2.metric("Raasi (Sign)", RAASI_NAMES[raasi_i])
col3.metric("Tithi", f"{tithi_i}") 
col4.metric("Moon Phase", phase_name) 
col5.metric("Moon Longitude", f"{moon_lon_wrapped:.2f}°")
col6.metric("Angle (Moon-Sun)", f"{phase_ang:.2f}°")

# Show Moon Visual in col4
with col4:
    moon_fig = draw_moon_phase(phase_ang)
    st.pyplot(moon_fig)

st.divider()

# =====================================================
# 1) Circular Dials
# =====================================================
# Much smaller dials
col_dial, col_metrics = st.columns([1, 2])

with col_dial:
    fig1, ax1 = plt.subplots(figsize=(2, 2), subplot_kw={'projection': 'polar'})
    ax1.set_title("Astrological Dials", pad=10, fontsize=8)
    ax1.set_yticklabels([])
    ax1.set_xticklabels([])
    ax1.grid(alpha=0.3)

    nak_angle = 2 * np.pi * (moon_lon_wrapped / 360)
    tithi_angle = 2 * np.pi * (((moon_lon_wrapped - sun_lon_wrapped) % 360) / 360)

    ax1.plot([0, nak_angle], [0, 1], linewidth=2, label="Nakshatra", color='tab:blue')
    ax1.plot([0, tithi_angle], [0, 0.7], linewidth=2, label="Tithi", color='tab:orange')
    
    # Legend outside to save space
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=6, frameon=False)

    st.pyplot(fig1)

# =====================================================
# 2) State Space Trajectory
# =====================================================
with col_metrics:
    st.subheader("Nakshatra–Tithi State Space")

    history_times = [
        current_time_utc + timedelta(hours=h)
        for h in np.linspace(-360, 360, 400)
    ]

    moon_hist = []
    sun_hist = []

    for t_h in history_times:
        m, s = true_ecliptic_longitudes(t_h)
        moon_hist.append(m)
        sun_hist.append(s)

    moon_hist = np.array(moon_hist)
    sun_hist = np.array(sun_hist)

    nak_hist = (moon_hist % 360 // NAK_SIZE).astype(int)
    tithi_hist = ((moon_hist % 360 - sun_hist % 360) % 360 // TITHI_SIZE).astype(int)

    fig2, ax2 = plt.subplots(figsize=(6, 3))
    ax2.plot(nak_hist, tithi_hist, alpha=0.6, label="Trajectory")
    ax2.set_xlabel("Nakshatra", fontsize=8)
    ax2.set_ylabel("Tithi", fontsize=8)
    ax2.set_title("State Transition Trajectory")
    
    # Highlight current position
    ax2.scatter(nak_i, tithi_i, c='red', s=100, zorder=10, label="Current")
    
    ax2.set_xlim(-0.5, 26.5)
    ax2.set_ylim(-0.5, 30.5)
    
    ax2.grid(True, alpha=0.3)
    
    # Custom ticks
    ax2.set_xticks(range(27))
    # ax2.set_xticklabels([n.split(' ')[0] for n in NAKSHATRAS], rotation=90, fontsize=6)
    ax2.set_xticklabels([]) # Simplify for now or use Tamil names if space permits
    
    ax2.set_yticks([0, 14, 29])
    ax2.set_yticklabels(["1", "15", "30"], fontsize=6)
    
    ax2.legend(fontsize=8)
    
    st.pyplot(fig2)

# =====================================================
# 3) Geocentric Orbit Visualization
# =====================================================
st.subheader("Geocentric 2D Orbit (Sidereal)")
col_orbit, col_legend = st.columns([3, 1])

with col_orbit:
    fig3, ax3 = plt.subplots(figsize=(5, 5), subplot_kw={'projection': 'polar'})
    ax3.set_title("Earth-Centered View (Actual Orbit)", pad=15)
    
    # 1. Plot Earth at Center
    ax3.scatter(0, 0, s=100, c='blue', label='Earth', zorder=10)
    
    # 2. Calculate Moon's Orbit Trace (~27 days)
    # We want to show perigee (closest) and apogee (farthest)
    orbit_times = [
        current_time_utc + timedelta(hours=h)
        for h in np.linspace(-360, 360, 200) # +/- 15 days
    ]
    
    m_lons = []
    m_dists = []
    
    for ot in orbit_times:
        ml, md, _, _ = get_geocentric_data(ot)
        m_lons.append(np.radians(ml))
        m_dists.append(md)
        
    # Scale distances for plotting?
    # Moon distance ~0.0025 AU. Sun ~1.0 AU.
    # We plot Moon at actual scale.
    # Sun will be an arrow indicating direction.
    
    # Plot Orbit Path
    ax3.plot(m_lons, m_dists, color='gray', linestyle='--', alpha=0.5, label='Moon Path')
    
    # 3. Plot Current Moon Data
    cur_mlon, cur_mdist, cur_slon, cur_sdist = get_geocentric_data(current_time_utc)
    
    # Plot Current Moon
    ax3.scatter(np.radians(cur_mlon), cur_mdist, s=50, c='silver', edgecolors='black', label='Moon', zorder=5)
    
    # 4. Plot Sun (Direction Only)
    # Sun is way too far (400x). We place it just outside the Moon's orbit for visualization.
    # Max Moon dist is approx 0.0027 AU. Let's place Sun at 0.0035 AU.
    plot_limit = max(m_dists) * 1.3
    sun_plot_dist = plot_limit * 0.90
    
    ax3.scatter(np.radians(cur_slon), sun_plot_dist, s=150, c='gold', marker='*', label='Sun (Dir)', zorder=6)
    
    # Draw line to Sun
    ax3.plot([0, np.radians(cur_slon)], [0, sun_plot_dist], color='gold', linestyle=':', alpha=0.8)
    
    # 5. Decoration
    ax3.set_rticks([])  # Hide radial ticks (distance)
    ax3.set_theta_zero_location('N') # 0 deg at top? 
    # Sidereal 0 (Mesham/Aries) is usually East or Top. Let's stick to standard polar (E=0).
    # But conventionally North is 0?
    # Astronomy standard: 0 = Vernal Equinox.
    
    ax3.grid(True, alpha=0.2)
    ax3.legend(loc='lower right', fontsize=8, bbox_to_anchor=(1.2, 0))
    
    st.pyplot(fig3)

with col_legend:
    st.info("""
    **Visual Guide:**
    - **Earth**: Center (Blue)
    - **Moon**: Silver dot on elliptical path.
    - **Sun**: Gold Star (Direction only).
    *Note: Sun distance is not to scale.*
    """)

# =====================================================
# Explanation & Education
# =====================================================

TAMIL_MONTHS = [
    "Chithirai (Mesham)", "Vaikasi (Rishabham)", "Aani (Mithunam)",
    "Aadi (Katakam)", "Avani (Simham)", "Purattasi (Kanni)",
    "Aippasi (Tulaam)", "Karthigai (Vrischikam)", "Margazhi (Dhanusu)",
    "Thai (Makaram)", "Maasi (Kumbham)", "Panguni (Meenam)"
]
sun_rasi_index = int((sun_lon_wrapped % 360) // 30)
current_month = TAMIL_MONTHS[sun_rasi_index]

st.divider()

st.markdown(f"### 🌞 **Current Season / Solar Month**: **{current_month}**")

with st.expander("📖 **How to read these charts & Understanding the Science**", expanded=True):
    st.markdown("""
    ### 1. The Dials
    The circular dials show the current progress through the **Space Window (Nakshatra)** and the **Phase Window (Tithi)**.
    - **Nakshatra Hand**: Points to where the Moon is in the 360° sky.
    - **Tithi Hand**: Points to the Moon's angle *relative* to the Sun (Phase).

    ### 2. State Space Trajectory
    This graph maps the system's movement over time (Past 15 days to Future 15 days).
    - **X-Axis (Nakshatra)**: Represents the **Moon's motion** around Earth (West to East).
    - **Y-Axis (Tithi)**: Represents the **Moon Phase**.
        - 0 (New Moon) → 15 (Full Moon) → 30 (New Moon).

    ### 3. Location & Accuracy
    **"Where is this calculated for?"**
    - **Geocentric**: Calculated from the Center of the Earth.
    - **Timezone**: Input is in **IST (Indian Standard Time)**. Internally converted to UTC for NASA's ephemeris.
    """)