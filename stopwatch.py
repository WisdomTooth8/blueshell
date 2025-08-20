# stopwatch.py — ST7735 stopwatch using the same draw/display pattern as shapes.py
# Keys: SPACE/Enter = Lap+Reset,  c = Clear last lap,  q = Quit

import sys, time, termios, tty, select, signal
from PIL import Image, ImageDraw, ImageFont
import st7735  # Pimoroni driver (installed from their GitHub)

# --- Display init (your wiring) ---
disp = st7735.ST7735(
    port=0,
    cs=0,          # CE0 (pin 24) – use 1 if you wired CE1/pin 26
    dc=9,          # BCM9 (pin 21)
    backlight=18,  # BCM18 (pin 12) – omit if not wired
    rotation=90,
    width=160, height=80,   # 0.96" panel
    bgr=True,               # flip to False if colours look swapped
    spi_speed_hz=4_000_000
)
disp.begin()
W, H = disp.width, disp.height

# --- Fonts (monospace if available) ---
def load_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
    except Exception:
        return ImageFont.load_default()

FONT_BIG   = load_font(26)
FONT_SMALL = load_font(12)

# --- Helpers ---
def fmt_time(seconds: float) -> str:
    m, s = divmod(max(0.0, seconds), 60)
    return f"{int(m):02d}:{s:06.3f}"  # MM:SS.mmm

def render(current_s: float, last_lap_s: float | None):
    """Create a fresh image buffer, draw everything, then push it."""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)

    # Title
    d.text((2, 2), "STOPWATCH", font=FONT_SMALL, fill=(150, 150, 150))

    # Current time, centered
    cur = fmt_time(current_s)
    tw, th = d.textbbox((0, 0), cur, font=FONT_BIG)[2:]
    d.text(((W - tw) // 2, (H - th) // 2 - 6), cur, font=FONT_BIG, fill=(255, 255, 255))

    # Last lap (bottom-left)
    last_txt = "--" if last_lap_s is None else fmt_time(last_lap_s)
    d.text((2, H - 14), f"Last: {last_txt}", font=FONT_SMALL, fill=(0, 255, 128))

    # Hint (bottom-right)
    hint = "SPACE/Enter=Lap  c=Clear  q=Quit"
    hw, _ = d.textbbox((0, 0), hint, font=FONT_SMALL)[2:]
    d.text((W - hw - 2, H - 14), hint, font=FONT_SMALL, fill=(120, 120, 120))

    disp.display(img)

# --- Non-blocking keyboard (works with any USB keyboard/foot pedal) ---
TRIGGER_KEYS = {b' ', b'\n', b'\r'}  # SPACE or Enter
CLEAR_KEYS   = {b'c', b'C'}
QUIT_KEYS    = {b'q', b'Q'}

class RawStdin:
    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)  # characters arrive immediately
        return self
    def __exit__(self, exc_type, exc, tb):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)

def read_key(timeout=0.0):
    if sys.stdin in select.select([sys.stdin], [], [], timeout)[0]:
        return sys.stdin.buffer.read(1)
    return None

# --- Main loop ---
running = True
def handle_sigint(signum, frame):
    global running
    running = False
signal.signal(signal.SIGINT, handle_sigint)

start = time.monotonic()
last_lap = None
last_draw = 0.0

render(0.0, last_lap)

try:
    with RawStdin():
        while running:
            now = time.monotonic()
            elapsed = now - start

            # Key handling
            ch = read_key(0.01)
            if ch:
                if ch in QUIT_KEYS:
                    break
                if ch in TRIGGER_KEYS:
                    last_lap = elapsed
                    start = time.monotonic()  # reset stopwatch
                    render(0.0, last_lap)
                    continue
                if ch in CLEAR_KEYS:
                    last_lap = None
                    render(elapsed, last_lap)
                    continue

            # Refresh ~10 fps
            if now - last_draw >= 0.1:
                render(elapsed, last_lap)
                last_draw = now
finally:
    # Clear screen on exit
    disp.display(Image.new("RGB", (W, H), (0, 0, 0)))
