# Stopwatch on ST7735; lap/reset triggered by USB keyboard (SPACE/Enter). 'q' to quit.
import sys, time, termios, tty, select, signal
from PIL import Image, ImageDraw, ImageFont
import st7735

disp = st7735.ST7735(
    port=0, cs=0, dc=9, backlight=18, rotation=90,
    width=160, height=80, offset_left=26, offset_top=1, bgr=True,
    spi_speed_hz=4_000_000
)
disp.begin()
W, H = disp.width, disp.height

def load_font(size):
    try: return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
    except: return ImageFont.load_default()

FONT_BIG   = load_font(26)
FONT_SMALL = load_font(12)

def fmt_time(s):
    m, s = divmod(s, 60)
    return f"{int(m):02d}:{s:06.3f}"

def render(current_s, last_s):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((2,2), "STOPWATCH", font=FONT_SMALL, fill=(160,160,160))
    cur = fmt_time(current_s)
    tw, th = d.textbbox((0,0), cur, font=FONT_BIG)[2:]
    d.text(((W - tw)//2, (H - th)//2 - 6), cur, font=FONT_BIG, fill=(255,255,255))
    last_txt = "--" if last_s is None else fmt_time(last_s)
    d.text((2, H-14), f"Last: {last_txt}", font=FONT_SMALL, fill=(0,255,128))
    hint = "SPACE/Enter=Lap   q=Quit"
    hw, _ = d.textbbox((0,0), hint, font=FONT_SMALL)[2:]
    d.text((W - hw - 2, H - 14), hint, font=FONT_SMALL, fill=(120,120,120))
    disp.display(img)

TRIGGER_KEYS = {b' ', b'\n', b'\r'}  # SPACE or Enter
QUIT_KEYS    = {b'q', b'Q'}

class RawStdin:
    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        return self
    def __exit__(self, *args):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)

def read_key(timeout=0.0):
    if sys.stdin in select.select([sys.stdin], [], [], timeout)[0]:
        return sys.stdin.buffer.read(1)
    return None

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

            ch = read_key(0.01)
            if ch:
                if ch in QUIT_KEYS: break
                if ch in TRIGGER_KEYS:
                    last_lap = elapsed
                    start = time.monotonic()
                    render(0.0, last_lap)
                    continue

            if now - last_draw >= 0.1:  # ~10 fps
                render(elapsed, last_lap)
                last_draw = now
finally:
    disp.display(Image.new("RGB", (W, H), (0, 0, 0)))
