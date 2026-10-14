"""
app.py - polished dark-themed Streamlit web demo of the baby monitoring system.
"""
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import time
import cv2
import streamlit as st
import voice

from detect_file import Detect_final

st.set_page_config(
    page_title="BabyGuard AI",
    page_icon="baby",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --bg: #050914;
        --card: #111c31;
        --panel: #1c2840;
        --light: #9ccbf5;
        --white: #ffffff;
        --green: #34d399;
        --blue: #60a5fa;
        --orange: #fbbf24;
        --red: #fb7185;
    }

    .stApp {
        background: linear-gradient(180deg, #04070f 0%, #081225 100%);
        color: var(--white);
    }
    .block-container {
        max-width: 1400px;
        padding-top: 0.35rem;
        padding-bottom: 0.15rem;
    }
    header, footer, #MainMenu, .stDeployButton {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    html, body, .stApp {
        overflow: hidden !important;
        height: 100vh !important;
    }
    .main .block-container {
        height: calc(100vh - 0.3rem);
        overflow: hidden !important;
    }
    .stVerticalBlock {
        gap: 0.35rem !important;
    }
    .stVerticalBlock {
        gap: 0.55rem !important;
    }

    .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.6rem;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .brand {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .logo {
        width: 58px;
        height: 58px;
        border-radius: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(145deg, rgba(34,197,94,0.22), rgba(96,165,250,0.16));
        border: 1px solid rgba(34,197,94,0.45);
        box-shadow: 0 0 28px rgba(34, 197, 94, 0.18);
    }
    .logo span {
        font-size: 2rem;
    }
    .title {
        font-size: 1.5rem;
        font-weight: 900;
        margin: 0;
        color: var(--white);
        line-height: 1.1;
    }
    .subtitle {
        color: var(--light);
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }
    .live-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        padding: 0.55rem 0.95rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 800;
        border: 1px solid #22c55e;
        color: #86efac;
        background: rgba(34,197,94,0.12);
    }
    .live-pill.offline {
        border-color: #64748b;
        color: #cbd5e1;
        background: rgba(100,116,139,0.16);
    }
    .live-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #22c55e;
        box-shadow: 0 0 14px #22c55e;
    }
    .live-pill.offline .live-dot {
        background: #64748b;
        box-shadow: none;
    }

    .status-card {
        background: linear-gradient(180deg, #162238 0%, #121b2f 100%);
        border: 1px solid rgba(96, 165, 250, 0.12);
        border-radius: 20px;
        padding: 1.15rem 1.2rem;
        min-height: 106px;
        box-shadow: 0 14px 40px rgba(0, 0, 0, 0.22);
        margin-bottom: 0.3rem;
    }
    .icon {
        width: 46px;
        height: 46px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.35rem;
        margin-bottom: 0.85rem;
    }
    .icon.green  { background: rgba(34,197,94,0.14); color: #34d399; }
    .icon.blue   { background: rgba(96,165,250,0.14); color: #60a5fa; }
    .icon.amber  { background: rgba(251,191,36,0.14); color: #fbbf24; }
    .icon.red    { background: rgba(251,113,133,0.14); color: #fb7185; }
    .status-card h4 {
        margin: 0 0 0.75rem 0;
        font-size: 0.85rem;
        letter-spacing: 0.12em;
        color: #9fb4d6;
        text-transform: uppercase;
    }
    .status-title {
        font-size: 1.55rem;
        font-weight: 850;
        margin: 0;
        color: #ffffff;
        letter-spacing: 0.02em;
    }

    .video-panel {
        background: linear-gradient(180deg, #19273f 0%, #141f32 100%);
        border: 1px solid rgba(96, 165, 250, 0.12);
        border-radius: 24px;
        padding: 1.2rem;
        margin-top: 1rem;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.32);
    }
    .video-title {
        color: #8dd3ff;
        font-weight: 800;
        letter-spacing: 0.12em;
        font-size: 0.85rem;
        margin-bottom: 0.9rem;
    }
    video { border-radius: 18px !important; }

    .tip {
        color: #8dd3ff;
        font-size: 0.82rem;
        line-height: 1.45;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def load_model():
    return Detect_final()


STATUS_COLORS = {
    "SLEEPING": "#34d399",
    "NO MOVING": "#34d399",
    "INSIDE": "#34d399",
    "AWAKE": "#fbbf24",
    "BODY MOVING": "#fbbf24",
    "OUTSIDE": "#fb7185",
    "NO FACE": "#fbbf24",
    "NO BODY": "#fbbf24",
    "NO AREA": "#fbbf24",
    "Waiting": "#60a5fa",
}


def status_card(slot, title, value, icon, icon_color):
    color = STATUS_COLORS.get(value, "#fbbf24")
    slot.markdown(
        f"""
        <div class="status-card">
            <div class="icon" style="color:{icon_color}; background:rgba(255,255,255,0.07);">
                {icon}
            </div>
            <h4>{title}</h4>
            <p class="status-title" style="color:{color};">{value}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.sidebar.title("Controls")
run = st.sidebar.toggle("Start camera", value=False)

with st.sidebar.expander("Camera", expanded=True):
    cam_index = st.number_input("Camera number", min_value=0, max_value=5, value=0, step=1)
    preview_width = st.select_slider("Preview width", options=[480, 640, 720, 960], value=640)

with st.sidebar.expander("Safe area (% of the picture)"):
    left = st.slider("Left edge", 0, 100, 10)
    right = st.slider("Right edge", 0, 100, 90)
    top = st.slider("Top edge", 0, 100, 10)
    bottom = st.slider("Bottom edge", 0, 100, 90)

with st.sidebar.expander("Alerts and detection"):
    voice_enabled = st.toggle("Voice alerts", value=True)
    motion_sensitivity = st.slider(
        "Movement sensitivity",
        min_value=0.005,
        max_value=0.150,
        value=0.030,
        step=0.005,
    )
    voice.VOICE_ENABLED = voice_enabled

st.sidebar.markdown(
    """
    <div class="tip">
    <strong>Demo tips</strong><br>
    Close other camera apps first.<br>
    Draw the area after at least 3 clicks.<br>
    Stay inside the box for a clean calm demo.
    </div>
    """,
    unsafe_allow_html=True,
)

header_left, header_right = st.columns([6, 1])

with header_left:
    st.markdown(
        """
        <div class="header">
            <div class="brand">
                <div class="logo"><span>&#128118;</span></div>
                <div>
                    <h1 class="title">Baby Monitoring System</h1>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_right:
    pill_class = "live-pill" if run else "live-pill offline"
    st.markdown(
        f"<div class='{pill_class}'><span class='live-dot'></span> LIVE</div>",
        unsafe_allow_html=True,
    )

status_cols = st.columns(3)
movement_slot = status_cols[0].empty()
status_slot = status_cols[1].empty()
boundary_slot = status_cols[2].empty()

extra_area = st.columns([2, 1])[1]
with extra_area:
    details_slot = st.empty()

st.markdown('<div class="video-panel">', unsafe_allow_html=True)
st.markdown('<div class="video-title">LIVE WEBCAM FEED</div>', unsafe_allow_html=True)
video_slot = st.empty()
st.markdown("</div>", unsafe_allow_html=True)

alert_slot = st.empty()

if not run:
    video_slot.info("Turn on Start camera in the sidebar to begin.")
    status_card(movement_slot, "Movement", "NO MOVING", "&#9889;", "#34d399")
    status_card(status_slot, "Baby status", "SLEEPING", "&#127769;", "#60a5fa")
    status_card(boundary_slot, "Boundary", "INSIDE", "&#128204;", "#34d399")
    details_slot.caption("EAR value updates when the camera starts.")
elif left >= right or top >= bottom:
    st.sidebar.error("Left must be smaller than Right, and Top smaller than Bottom.")
else:
    model = load_model()
    model.reset()
    cap = cv2.VideoCapture(int(cam_index))
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        st.error("Could not open the camera. Close other apps that use it "
                 "(Zoom, Teams, Camera) and try again.")
    else:
        try:
            frame_number = 0
            fps_start = time.time()
            frames = 0

            while True:
                ok, frame = cap.read()
                if not ok:
                    st.error("Could not read from the camera.")
                    break

                frame = cv2.flip(frame, 1)

                if frame.shape[1] > preview_width:
                    scale = preview_width / frame.shape[1]
                    frame = cv2.resize(
                        frame,
                        (preview_width, int(frame.shape[0] * scale)),
                        interpolation=cv2.INTER_AREA,
                    )

                h, w = frame.shape[:2]
                x1, x2 = int(w * left / 100), int(w * right / 100)
                y1, y2 = int(h * top / 100), int(h * bottom / 100)
                points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]

                model.motion_threshold = motion_sensitivity
                frame = model.output(frame, points)

                box_color = (60, 60, 255) if model.label_outside == "OUTSIDE" else (80, 200, 80)
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

                video_slot.image(frame, channels="BGR", use_container_width=True)

                frames += 1
                frame_number += 1
                if frame_number % 5 == 0:
                    status_card(
                        movement_slot,
                        "Movement",
                        model.label,
                        "&#9889;",
                        "#fbbf24" if model.label == "BODY MOVING" else "#34d399",
                    )
                    status_card(
                        status_slot,
                        "Baby status",
                        model.label_eye,
                        "&#127769;",
                        "#fbbf24" if model.label_eye == "AWAKE" else "#60a5fa",
                    )
                    status_card(
                        boundary_slot,
                        "Boundary",
                        model.label_outside,
                        "&#128204;",
                        "#fb7185" if model.label_outside == "OUTSIDE" else "#34d399",
                    )

                    fps = frames / max(time.time() - fps_start, 0.001)
                    details_slot.caption("EAR: %.2f | FPS: %.0f" % (model.ear, fps))

                    if model.label_outside == "OUTSIDE":
                        alert_slot.error("Warning: Baby is OUTSIDE the safe area")
                    elif model.label_eye == "AWAKE":
                        alert_slot.warning("Baby is awake")
                    elif model.label == "BODY MOVING":
                        alert_slot.warning("Baby is moving")
                    else:
                        alert_slot.success("All calm")
        finally:
            cap.release()
            voice.VOICE_ENABLED = True
