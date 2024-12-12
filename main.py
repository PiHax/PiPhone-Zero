from PIL import Image, ImageDraw, ImageFont
import spidev
import ST7789
import time
import RPi.GPIO as GPIO
import os
import subprocess

# GPIO setup
JOYSTICK_UP = 5
JOYSTICK_DOWN = 6
JOYSTICK_LEFT = 13
JOYSTICK_RIGHT = 19
KEY1 = 26
KEY2 = 21
KEY3 = 20

GPIO.setmode(GPIO.BCM)
GPIO.setup([JOYSTICK_UP, JOYSTICK_DOWN, JOYSTICK_LEFT, JOYSTICK_RIGHT, KEY1, KEY2, KEY3], GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize the display
spi = spidev.SpiDev(0, 0)
display = ST7789.ST7789(spi, 128, 128, reset=24, dc=25, backlight=18)
display.begin()

# Fonts
font = ImageFont.load_default()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (169, 169, 169)
LIGHT_GRAY = (211, 211, 211)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Screen size
WIDTH, HEIGHT = 128, 128

# State
current_screen = "home"
selected_app = 0  # Index of the selected app on the home screen

# Draw home screen with clean, minimal design
def draw_home_screen():
    image = Image.new("RGB", (WIDTH, HEIGHT), GRAY)
    draw = ImageDraw.Draw(image)

    # Background
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=LIGHT_GRAY)

    # Draw app icons with feedback (highlight selected app)
    apps = ["Browser", "Clock", "Terminal"]
    colors = [RED, GREEN, BLUE]
    positions = [(10, 10), (70, 10), (40, 70)]

    for i, (label, color, pos) in enumerate(zip(apps, colors, positions)):
        x, y = pos
        outline = WHITE if i == selected_app else LIGHT_GRAY
        fill = color if i != selected_app else (255, 255, 255)  # Highlight selected app
        draw.rectangle((x, y, x + 40, y + 40), fill=fill, outline=outline)
        draw.text((x + 5, y + 45), label, fill=BLACK if i != selected_app else WHITE, font=font)

    display.display(image)

# Draw Browser App with file navigation (clean interface)
def draw_browser_app(path="/home/pi"):
    image = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)

    # Display files in the current directory as a basic file browser
    try:
        files = os.listdir(path)
        files = [f for f in files if f[0] != '.']  # Skip hidden files
    except PermissionError:
        files = ["Permission Denied"]

    # Title and list of files
    draw.text((10, 10), "Browser", fill=BLACK, font=font)
    y_offset = 30
    for file in files[:5]:  # Limit to displaying first 5 files
        draw.text((10, y_offset), file, fill=BLACK, font=font)
        y_offset += 10

    draw.text((10, 100), "[Key3] Back", fill=RED, font=font)
    display.display(image)

# Draw Clock App with formatted time and date
def draw_clock_app():
    image = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)

    current_time = time.strftime("%H:%M:%S")
    current_date = time.strftime("%A, %b %d")
    draw.text((10, 10), "Clock", fill=BLACK, font=font)
    draw.text((10, 30), f"Time: {current_time}", fill=BLACK, font=font)
    draw.text((10, 50), f"Date: {current_date}", fill=BLACK, font=font)
    draw.text((10, 100), "[Key3] Back", fill=RED, font=font)
    display.display(image)

# Draw Terminal App with input functionality
def draw_terminal_app():
    image = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)

    draw.text((10, 10), "Terminal", fill=BLACK, font=font)

    # Display terminal output (limit length for display)
    terminal_output = subprocess.check_output(command_buffer.split(), stderr=subprocess.STDOUT, text=True) if command_buffer else "Enter command"
    
    # Display the output in the terminal window
    draw.text((10, 30), f"> {command_buffer}", fill=BLACK, font=font)
    draw.text((10, 50), terminal_output[:50], fill=BLACK, font=font)  # Limit to 50 chars
    draw.text((10, 100), "[Key3] Back", fill=RED, font=font)
    display.display(image)

# Event handling for joystick and buttons
def handle_joystick():
    global selected_app

    if not GPIO.input(JOYSTICK_UP):
        selected_app = (selected_app - 1) % 3  # Move up
    elif not GPIO.input(JOYSTICK_DOWN):
        selected_app = (selected_app + 1) % 3  # Move down

    draw_home_screen()

def handle_buttons():
    global current_screen, command_buffer

    if not GPIO.input(KEY1):  # Confirm selection
        if current_screen == "home":
            apps = ["browser", "clock", "terminal"]
            current_screen = apps[selected_app]
            draw_app_screen()
        elif current_screen == "terminal":
            # Execute terminal command
            command_buffer = command_buffer.strip()
            draw_terminal_app()
    elif not GPIO.input(KEY2):  # Enter input mode (for terminal)
        if current_screen == "terminal":
            # Start typing the command in the terminal app
            command_buffer += " "
            draw_terminal_app()
    elif not GPIO.input(KEY3):  # Back button
        if current_screen != "home":
            current_screen = "home"
            draw_home_screen()

def draw_app_screen():
    if current_screen == "browser":
        draw_browser_app()
    elif current_screen == "clock":
        draw_clock_app()
    elif current_screen == "terminal":
        draw_terminal_app()

# Main loop
def main():
    global current_screen

    draw_home_screen()

    while True:
        handle_joystick()
        handle_buttons()
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
