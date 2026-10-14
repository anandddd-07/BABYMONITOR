r"""
apply_fixes.py - small fixes for app.py and detect_file.py.

Run it ONCE from the inner project folder:
    ..\venv311\Scripts\python.exe apply_fixes.py

It makes a backup of each file first (app_backup_before_fixes.py and
detect_file_backup_before_fixes.py), then applies each fix separately.
If a fix cannot be applied (for example because you edited that part of the
file yourself), it is skipped and the script tells you which one.
Running it twice is safe: fixes that are already applied are left alone.
"""
import os
import shutil

PATCHES = {}

# ----------------------------------------------------------------- detect_file.py
PATCHES["detect_file.py"] = [
    (
        "Add settings for smoothing, sensitivity and the on-video panel",
        r'''        self.recent_motion = deque(maxlen=3)
''',
        r'''        self.recent_motion = deque(maxlen=3)
        self.recent_area = deque(maxlen=5)
        self.motion_threshold = 0.03   # set by the web app's sensitivity slider
        self.show_panel = True         # the web app turns this off (cards show the status)
''',
    ),
    (
        "reset() also clears the area history",
        r'''        self.ear_seq.clear()
        self.recent_motion.clear()
''',
        r'''        self.ear_seq.clear()
        self.recent_motion.clear()
        self.recent_area.clear()
''',
    ),
    (
        "Make the movement sensitivity slider actually do something",
        r'''        m = self.motion_model
''',
        r'''        # Sensitivity slider: 0.03 = trained behaviour, lower = reacts to smaller movements
        feats = feats * (0.03 / max(self.motion_threshold, 0.001))
        m = self.motion_model
''',
    ),
    (
        "Smooth INSIDE/OUTSIDE over the last 5 checks (stops flickering)",
        r'''        self.label_outside = self.check_area(body_results.pose_landmarks,
                                             points, w, h)
''',
        r'''        raw_area = self.check_area(body_results.pose_landmarks,
                                   points, w, h)
        self.recent_area.append(raw_area)
        if raw_area in ("INSIDE", "OUTSIDE"):
            # majority of the last 5 checks, so one noisy frame cannot flip it
            outs = sum(1 for a in self.recent_area if a == "OUTSIDE")
            ins = sum(1 for a in self.recent_area if a == "INSIDE")
            self.label_outside = "OUTSIDE" if outs > ins else "INSIDE"
        else:
            self.label_outside = raw_area
''',
    ),
    (
        "Split the red alert banner from the grey status panel",
        r'''        if self.label_outside == "OUTSIDE":
            h, w = frame.shape[:2]
            cv2.rectangle(frame, (0, h - 50), (w, h), RED, -1)
            cv2.putText(frame, "ALERT: OUTSIDE THE SAFE AREA", (20, h - 15),
                        FONT, 0.9, WHITE, 2)
        return frame
''',
        r'''        return self.draw_banner(frame)

    def draw_banner(self, frame):
        """Red banner at the bottom when the baby is outside the safe area."""
        if self.label_outside == "OUTSIDE":
            h, w = frame.shape[:2]
            cv2.rectangle(frame, (0, h - 50), (w, h), RED, -1)
            cv2.putText(frame, "ALERT: OUTSIDE THE SAFE AREA", (20, h - 15),
                        FONT, 0.9, WHITE, 2)
        return frame
''',
    ),
    (
        "Only draw the grey panel when show_panel is True",
        r'''        return self.draw_panel(frame)
''',
        r'''        if self.show_panel:
            return self.draw_panel(frame)
        return self.draw_banner(frame)
''',
    ),
]

# ------------------------------------------------------------------------ app.py
PATCHES["app.py"] = [
    (
        "Remember the last labels shown",
        r'''            frame_number = 0
            fps_start = time.time()
            frames = 0
''',
        r'''            frame_number = 0
            fps_start = time.time()
            frames = 0
            shown = None
''',
    ),
    (
        "Update the cards the moment a label changes (no more lag)",
        r'''                if frame_number % 5 == 0:
''',
        r'''                current = (model.label, model.label_eye, model.label_outside)
                if current != shown or frame_number % 20 == 0:
                    shown = current
''',
    ),
    (
        "Move the alert box above the video so it is never cut off",
        r'''st.markdown('<div class="video-panel">', unsafe_allow_html=True)
st.markdown('<div class="video-title">LIVE WEBCAM FEED</div>', unsafe_allow_html=True)
video_slot = st.empty()
st.markdown("</div>", unsafe_allow_html=True)

alert_slot = st.empty()
''',
        r'''alert_slot = st.empty()   # alerts now sit above the video so they are always visible

st.markdown('<div class="video-panel">', unsafe_allow_html=True)
st.markdown('<div class="video-title">LIVE WEBCAM FEED</div>', unsafe_allow_html=True)
video_slot = st.empty()
st.markdown("</div>", unsafe_allow_html=True)
''',
    ),
    (
        "Hide the duplicate grey panel on the video",
        r'''                model.motion_threshold = motion_sensitivity
''',
        r'''                model.motion_threshold = motion_sensitivity
                model.show_panel = False   # the cards already show the status; set True to bring the panel back
''',
    ),
]


def apply(filename, patches):
    print()
    print("== %s ==" % filename)
    try:
        with open(filename, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print("   NOT FOUND in this folder - skipped. Run this from the inner project folder.")
        return

    backup = filename.replace(".py", "_backup_before_fixes.py")
    if os.path.exists(backup):
        print("   backup already exists (kept as it is):", backup)
    else:
        shutil.copy(filename, backup)
        print("   backup saved as", backup)

    applied = 0
    for description, old, new in patches:
        if new in text:
            print("   already applied :", description)
        elif text.count(old) == 1:
            text = text.replace(old, new)
            applied += 1
            print("   APPLIED         :", description)
        else:
            print("   SKIPPED (could not find the exact text):", description)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print("   %d fix(es) applied" % applied)


for name, patch_list in PATCHES.items():
    apply(name, patch_list)

print()
print("Done. Restart the app to see the changes.")
