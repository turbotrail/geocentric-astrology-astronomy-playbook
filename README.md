# Thirukanitham: Tamil Astrology Visualization Suite

This project provides a suite of tools to calculate and visualize astrological data (Nakshatras and Tithis) based on the **Thirukanitham (Nirayana)** system used in Tamil Astrology. It combines precise astronomical data from NASA with traditional Vedic calculations.

## 🚀 Key Features

*   **Accurate Methodology**: Uses **NASA JPL Ephemeris** (via Skyfield) + **Lahiri Ayanamsa** for precision.
*   **Mixed Localization**:
    *   **UI Shell**: English (for clarity).
    *   **Data Names**: Tamil (e.g., Nakshatra names like "அஸ்வினி").
    *   **Metrics**: Numeric Tithis (1-30) for simpler reading.
*   **Visualization**: Supports interactive dashboards, yearly plots, and high-quality video animations.

---

## 🛠 Scripts & Usage

### 1. Daily Astrology Dashboard (`script.py`)
An interactive Streamlit web app that shows the current Nakshatra, Tithi, and planetary positions using typical astrological dials.

**Run:**
```bash
streamlit run script.py
```

### 2. Yearly State Trajectory (`yearly_states.py`)
Generates a static plot visualizing the transition of Tithis and Nakshatras over the entire current year.

**Run:**
```bash
python yearly_states.py
```
*Output: Saves a plot image (e.g., `yearly_states.png` or interactive window).*

### 3. Geocentric Orbit Animation (`animate_orbit.py`)
A **Manim** script that generates a high-definition (1080p) video of the Sun and Moon orbiting Earth from a geocentric perspective.

**Features:**
*   **True Moon Scale**: Visually scaled to look realistic.
*   **Exaggerated Sun Orbit**: The Sun's elliptical path is **exaggerated 15x** so you can clearly see the difference between Aphelion (farthest) and Perihelion (closest).
*   **Adjustable Dates**: Run for any specific month/year.

**Run (Default - Current Date):**
```bash
manim -pqh animate_orbit.py OrbitScene
```

**Run (Specific Date - e.g., December 2026):**
```bash
YEAR=2026 MONTH=12 manim -pqh animate_orbit.py OrbitScene
```
*(Note: `-pqh` generates a High Quality 1080p preview)*

---

## 📚 Technical Background

### The Concept: Sidereal Zodiac (Nirayana)
Unlike Western Astrology (Tropical), which is fixed to the seasons, **Thiru Kanitham** uses the **Sidereal Zodiac**, which is fixed to the actual constellations.

The difference between the two is called **Ayanamsa**.

### The Formula
We use the **Lahiri Ayanamsa** (Standard Indian Govt. Correction).

1.  **Get Tropical Position**: Fetch raw longitude from NASA Ephemeris (`de440s.bsp`).
2.  **Apply Correction**:
    ```python
    # Approximation of Lahiri Ayanamsa
    ayanamsa = 23.85 + (Year - 2000) * 0.01397
    sidereal_longitude = tropical_longitude - ayanamsa
    ```

### Definitions
*   **Nakshatra (Star)**: The $360^\circ$ zodiac divided into 27 sectors ($13.33^\circ$ each).
*   **Tithi (Lunar Day)**: The angular distance between the Moon and Sun, divided into 30 phases ($12^\circ$ each).

---

## 📦 Installation

1.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Requires `skyfield`, `streamlit`, `manim`, `matplotlib`, `numpy`)*

2.  **System Dependencies for Manim:**
    *   You may need to install **ffmpeg** and **LaTeX** on your system to render animations.
    *   [Manim Installation Guide](https://docs.manim.community/en/stable/installation.html)
