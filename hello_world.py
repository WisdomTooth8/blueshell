import time
from PIL import Image, ImageDraw, ImageFont
import st7735

disp = st7735.ST7735(
    port=0,
    cs=0,          # CE0 -> physical pin 24; use 1 if you wired CE1/pin26
    dc=9,          # BCM9 -> physical pin 21
    backlight=18,  # BCM18 -> physical pin 12 (omit if not wired)
    rotation=90,
    width=160, height=80,     # this 0.96" panel
    offset_left=26, offset_top=1,  # common offsets; adjust if needed
    bgr=True,                 # correct colour order on most batches
    spi_speed_hz=4_000_000
)
disp.begin()

W, H = disp.width, disp.height
img = Image.new("RGB", (W, H), (0, 0, 0))
d = ImageDraw.Draw(img)
font = ImageFont.load_default()
txt = "Hello!"
bbox = d.textbbox((0,0), txt, font=font)
tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
d.rectangle((0,0,W-1,H-1), outline=(0,255,0))
d.text(((W-tw)//2, (H-th)//2), txt, font=font, fill=(255,255,255))
disp.display(img)
time.sleep(5)
