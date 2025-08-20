# stopwatch.py — ST7735 stopwatch (shapes.py-style drawing)
# SPACE/Enter = Lap+Reset | c = Clear last | b = Clear best | q = Quit

import sys, time, termios, tty, select, signal
from PIL import Image, ImageDraw, ImageFont
import st7735  # Pimoroni driver from GitHub

# --- Display init: exactly like shapes.py style ---
disp = st7735.ST7735(
    port=0,
    cs=0,           # CE0 (pin 24). Use 1 ONLY if you wired CE1 (pin 26)
    dc=9,           # BCM9 (pin 21)
    backlight=18,   # BCM18 (pin 12) - omit if not wired
    rotation=90,
    spi_speed_hz=4_000_000
)
disp.begin()

# Match shapes.py: derive size from the driver; one persistent buffer
WIDTH, HEIGHT = disp.width, disp.height
img  = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
draw = ImageDraw.Draw(img)

def load_font(size):
    # Monospace helps the digits look steady; fallback if not present
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

FONT_BIG   = load_font(34)  # main stopwatch (bigger)
FONT_MED   = load_font(18)  # Last (green, sits between clock and hints)
FONT_SMALL = load_font(12)  # Best + hints

def fmt_time(t):
    m, s = divmod(max(0.0, t), 60)
    return f"{int(m):02d}:{s:06.3f}"

def text_size(txt, font):
    x0, y0, x1, y1 = draw.textbbox((0, 0), txt, font=font)
    return (x1 - x0), (y1 - y0)

def render(current_s, last_s, best_s):
    # Clear buffer
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))

    # --- Best (top-left, small) ---
    best_txt = "--" if best_s is None else fmt_time(best_s)
    draw.text((2, 2), f"Best: {best_txt}", font=FONT_SMALL, fill=(0, 200, 255))

    # --- Main clock (center) ---
    cur = fmt_time(current_s)
    tw, th = text_size(cur, FONT_BIG)
    cur_y = (HEIGHT - th) // 2 - 8   # nudge up a little to make room for Last below
    draw.text(((WIDTH - tw)//2, cur_y), cur, font=FONT_BIG, fill=(255, 255, 255))

    # --- Last (green, centered under the big clock) ---
    last_txt = "--" if last_s is None else fmt_time(last_s)
    ltw, lth = text_size(last_txt, FONT_MED)
    # place it just below the big digits, centered
    last_y = cur_y + th + 2
    draw.text(((WIDTH - ltw)//2, last_y), last_txt, font=FONT_MED, fill=(0, 255, 128))

    # --- Hints (bottom, small) ---
    hint = "SPACE/Enter=Lap  c=Clear last  b=Clear best  q=Quit"
    hw, hh = text_size(hint, FONT_SMALL)
    draw.text(((WIDTH - hw)//2, HEIGHT - hh - 2), hint, font=FONT_SMALL, fill=(140, 140, 140))

    # Push the buffer
    disp.display(img)

# --- Non-blocking keyboard (USB keyboard or foot switch) ---
TRIG  = {b' ', b'\n', b'\r'}  # SPACE / Enter
CLEAR_LAST = {b'c', b'C'}
CLEAR_BEST = {b'b', b'B'}
QUIT  = {b'q', b'Q'}

class RawIn:
    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        return self
    def __exit__(self, *_):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)

def read_key(timeout=0.0):
    if sys.stdin in select.select([sys.stdin], [], [], timeout)[0]:
        return sys.stdin.buffer.read(1)
    return None

# --- Main loop ---
running  = True
signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

start     = time.monotonic()
last_lap  = None
best_lap  = None
last_draw = 0.0

# First frame
render(0.0, last_lap, best_lap)

try:
    with RawIn():
        while True:
            now = time.monotonic()
            elapsed = now - start

            ch = read_key(0.01)
            if ch:
                if ch in QUIT:
                    break
                if ch in TRIG:
                    # record last; update best; reset
                    last_lap = elapsed
                    if best_lap is None or last_lap < best_lap:
                        best_lap = last_lap
                    start = time.monotonic()
                    render(0.0, last_lap, best_lap)
                    continue
                if ch in CLEAR_LAST:
                    last_lap = None
                    render(elapsed, last_lap, best_lap)
                    continue
                if ch in CLEAR_BEST:
                    best_lap = None
                    render(elapsed, last_lap, best_lap)
                    continue

            # Gentle ~10 fps refresh
            if now - last_draw >= 0.1:
                render(elapsed, last_lap, best_lap)
                last_draw = now
finally:
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))
    disp.display(img)
