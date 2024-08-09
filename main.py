# CSPico Minimal MicroPython Driver Program
# Copyright (C) Colin O'Flynn, 2021
# CC-SA 3.0 License

from machine import Pin, PWM, Signal
import neopixel
import time
import utime
import array
import struct
import math
import _thread
import random
from wavplayer import WavPlayer

state = "Startup"
substate = "None"
state_changed = True
animation_changed = True
running = True
loop_counter = 0
sound_on = True
low_power_brightness = 0.05



# ======= I2S CONFIGURATION =======
SCK_PIN = Pin(20)
WS_PIN = Pin(21)
SD_PIN = Pin(19)
I2S_ID = 0
BUFFER_LENGTH_IN_BYTES = 2000

wp = WavPlayer(
    id=I2S_ID,
    sck_pin=Pin(SCK_PIN),
    ws_pin=Pin(WS_PIN),
    sd_pin=Pin(SD_PIN),
    ibuf=BUFFER_LENGTH_IN_BYTES,
)

firing_song = ["pew-small.wav", "tesla.wav", "blaster.wav"]
firing_song_index = 0

low_power_song = ["nomana.wav", "nomana2.wav", "nomana3.wav"]
low_power_song_index = 0

# ======== BUTTON TRIGGERS ========

# Setup GPIO15 as input with pull-up resistor
low_power_pin = machine.Pin(9, machine.Pin.IN, machine.Pin.PULL_UP)
wakeup_pin = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)

# Define the callback function for button press
def low_power_callback(pin):
    global state
    global substate
    global state_changed
    global sound_on
    global animation_changed

    if state == "Sound On" or state == "Sound Off":
        # we are in the middle of a triggered sound change, ignore this button push
        return

    # Short delay to debounce and check both buttons
    utime.sleep_ms(50)

    if low_power_pin.value() and wakeup_pin.value():
        print("Both buttons pressed!")

        # invert the value of the sound_on variable
        sound_on = not sound_on
        substate = state
        state = "Sound On" if sound_on else "Sound Off"
        return
        

    print("Low Power Button pressed!")
    # Implement the logic to handle the button press
    state = "Low Power"

    if substate == "None":
        substate = "Chase"
    elif substate == "Chase":
        substate = "Rainbow"
    elif substate == "Rainbow":
        substate = "Twinkle"
    elif substate == "Twinkle":
        substate = "Wave"
    elif substate == "Wave":
        substate = "Chase"
    
    
    state_changed = True
    animation_changed = True

def wakeup_callback(pin):
    global state
    global substate
    global state_changed
    global sound_on
    global animation_changed

    if state == "Sound On" or state == "Sound Off":
        # we are in the middle of a triggered sound change, ignore this button push
        return
    
    # Short delay to debounce and check both buttons
    utime.sleep_ms(50)

    if low_power_pin.value() and wakeup_pin.value():
        print("Both buttons pressed!")
        
        # invert the value of the sound_on variable
        sound_on = not sound_on
        substate = state
        state = "Sound On" if sound_on else "Sound Off"
        return

    print("Wakeup Button pressed!")
    # Implement the logic to handle the button press
    if buttonArm.value():
        if state != "Armed":
            state_changed = True
            animation_changed = True
        state = "Armed"
    else:
        if state != "Disarmed":
            state_changed = True
            animation_changed = True
        state = "Disarmed"
        
    substate = "None"
    
# Attach the interrupt to GPIO15
low_power_pin.irq(trigger=machine.Pin.IRQ_RISING, handler=low_power_callback)
# Attach the interrupt to GPIO15
wakeup_pin.irq(trigger=machine.Pin.IRQ_RISING, handler=wakeup_callback)


# ======== LED CONFIGURATION ========
# Create NeoPixel object with appropriate configuration.
np = neopixel.NeoPixel(Pin(29), 76)
n = np.n

brightness = 0

led_groups = [
    [28, 67, 29, 66], [27, 65], [26, 64], [25, 61, 30, 68], 
    [24, 62, 31, 69], [23, 63, 32, 70], [22, 60], [21, 59, 33, 71], 
    [20, 58, 34, 72], [19, 57, 35, 73], [18, 56], [17, 53, 36, 74], 
    [16, 54, 37, 75], [15, 55, 38, 76], [14, 52], [13, 51], 
    [12, 50], [11, 49], [10, 48], [9, 47], [8, 46], [7, 45], 
    [6, 44], [5, 43], [4, 42], [3, 41], [2, 40], [1, 39]
]

def scale_color(color, factor):
    return tuple(int(c * factor) for c in color)

def interpolate_color(start_color, end_color, factor):
    return tuple(int(start_color[i] + factor * (end_color[i] - start_color[i])) for i in range(3))

def wheel(pos):
    # Generate rainbow colors across 0-255 positions.
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)

# Define start and end colors
start_color = (0, 0, 255)  # Blue
end_color = (255, 0, 0)    # Red

def set_all_leds(color):
    for group in led_groups:
        for led in group:
            np[led-1] = color
    np.write()

def flash_all_red():
    for i in range(n):
        np[i] = (10, 0, 0)
    np.write()
    time.sleep_ms(500)
    for i in range(n):
        np[i] = (0, 0, 0)
    np.write()
    time.sleep_ms(500)

def startup_animation():
    for i in range(len(led_groups)):
        # Calculate the current color based on the interpolation
        factor = i / (len(led_groups) - 1)
        current_color = interpolate_color(start_color, end_color, factor)
        
        # Turn on the LEDs in the current group
        for led in led_groups[i]:
            np[led-1] = current_color
        
        # Update the colors of all previous LEDs to the current color
        for j in range(i + 1):
            for led in led_groups[j]:
                np[led-1] = current_color
        
        np.write()
        time.sleep(0.07)

def wipe_animation(colour, sleep_time=0.03):
    for i in range(len(led_groups)):

        # Turn on the LEDs in the current group
        for led in led_groups[i]:
            np[led-1] = colour
        
        np.write()
        time.sleep(sleep_time)

def firing_animation():

    #set a colour gradiant from red to green
    for i in range(len(led_groups)):
        factor = i / (len(led_groups) - 1)
        current_color = interpolate_color((255, 0, 0), (0, 255, 0), factor/2)
        for led in led_groups[i]:
            np[led-1] = current_color
    np.write()     

    # a reverse wipe animation turning all the leds off (then all back on)
    for i in range(len(led_groups)-1, -1, -1):
        for led in led_groups[i]:
            np[led-1] = (0, 0, 0)
        np.write()
        time.sleep(0.01)

    #turn them all back on
    for i in range(len(led_groups)):
        for led in led_groups[i]:
            np[led-1] = (10, 0, 0)
    np.write()    

def breathing_effect(colour, max_brightness=50):
    global loop_counter

    loop_counter %= max_brightness
   
    # Calculate the brightness factor using a sine wave
    brightness_factor = (math.sin(brightness / max_brightness * 2 * math.pi) + 1) / 2
    
    # Adjust the brightness of all LEDs
    adjusted_color = tuple(int(c * brightness_factor) for c in colour)
    set_all_leds(adjusted_color)
    time.sleep(0.04)
    loop_counter += 1

def rainbow_cycle(wait=0.01):
    global loop_counter

    loop_counter %= 256

    for i in range(len(led_groups)):
        pixel_index = (i * 256 // len(led_groups)) + loop_counter
        color = wheel(pixel_index & 255)
        scaled_color = scale_color(color, low_power_brightness)
        for led in led_groups[i]:
            np[led - 1] = scaled_color
    np.write()
    time.sleep(wait)
    loop_counter += 1

def chase_animation():
    global loop_counter

    loop_counter %= len(led_groups)

    # Turn off all LEDs
    set_all_leds((0, 0, 0))
    
    # Turn on the current group and the next few groups for the chase effect
    for j in range(5):  # Number of groups in the chase
        group_index = (loop_counter + j) % len(led_groups)
        color = wheel((group_index * 256 // len(led_groups)) & 255)
        scaled_color = scale_color(color, low_power_brightness)
        for led in led_groups[group_index]:
            np[led - 1] = scaled_color
    
    np.write()
    time.sleep(0.1)
    loop_counter += 1

def twinkle_effect():
    twinkle_color = scale_color((255, 255, 255),0.1)  # White

    # Turn off all LEDs
    set_all_leds((0, 0, 0))
    
    # Randomly turn on a few groups
    for _ in range(10):  # Number of twinkles
        group_index = random.randint(0, len(led_groups) - 1)
        color = wheel((group_index * 256 // len(led_groups)) & 255)
        scaled_color = scale_color(color, low_power_brightness)
        for led in led_groups[group_index]:
            np[led - 1] = scaled_color
    
    np.write()
    time.sleep(0.5)

def wave_pattern():
    global loop_counter

    loop_counter %= 255

    for i in range(len(led_groups)):
        wave_value = (math.sin(i / 10.0 + loop_counter / 10.0) + 1) / 2 * 255
        color = (int(wave_value), 0, 255 - int(wave_value))
        scaled_color = scale_color(color, low_power_brightness)
        for led in led_groups[i]:
            np[led - 1] = scaled_color
    np.write()
    time.sleep(0.05)
    loop_counter += 1

def animation_thread():
    global state
    global animation_changed   
    global running
    global loop_counter

    try:
        while running:
            if state_changed:
                loop_counter = 0

            if state == "Startup":
                if (animation_changed):
                    animation_changed = False
                    startup_animation()
            elif state == "Disarmed":
                if (animation_changed):
                    animation_changed = False
                    wipe_animation((0, 10, 0), 0.05) 
                breathing_effect((0, 10, 0))
            elif state == "Armed":
                if (animation_changed):
                    animation_changed = False
                    wipe_animation((10, 0, 0)) 
                breathing_effect((10, 0, 0), 20)
            elif state == "Low Power":
                if substate == "Chase":
                    chase_animation()
                elif substate == "Rainbow":
                    rainbow_cycle()
                elif substate == "Wave":
                    wave_pattern()
                elif substate == "Twinkle":
                    twinkle_effect()
            elif state == "Error" or state == "Sound On" or state == "Sound Off":
                flash_all_red()
            elif state == "Firing":
                if (animation_changed):
                    animation_changed = False
                    firing_animation()
    except KeyboardInterrupt:
        running = False
        print("Keyboard Interrupt")
        return

# ============= EMP CONFIGURATION =============
def pwm_off():
    """Turn HV Transformer Off"""
    hvpwm = Pin(12, Pin.OUT)
    hvpwm.low()

def pwm_on():
    """Turn HV Transformer On"""
    hvpwm = PWM(Pin(12))
    # The duty cycle & frequency have been emperically tuned
    # here to maximize the HV charge. This results in around
    # 250V on the HV capacitor. Setting duty cycle higher generally
    # just causes more current flow/waste in the HV transformer.
    hvpwm.freq(2500)
    hvpwm.duty_u16(800) #range 0 to 65535, 800 = 1.22% duty cycle

#hvpwm pin drives the HV transformer
pwm_off()

# Status LEDs:
ledHv = Signal(Pin(17, Pin.OUT)) #HV 'on' LED (based on feedback)
ledArm = Signal(Pin(18, Pin.OUT)) #Arm 'on' LED
ledStatus = Signal(Pin(16, Pin.OUT)) #Simple status LED
ledStatus.on()


# Due to original PCB being single-layer milled board, these buttons
# used different "active" status to simplify the board routing. This
# was left the same for final PCB.
buttonArm = Signal(Pin(4,  Pin.IN, pull=Pin.PULL_DOWN))
buttonPulse = Signal(Pin(3, Pin.IN, pull=Pin.PULL_DOWN))

# The 'charged' input routes to two pins, one of them is an ADC pin.
# Technically could just use the ADC pin as digital input, but again
# for 'technical debt' reasons left as two pins.
charged = Signal(Pin(26,  Pin.IN), invert=True)

# The 'pulseOut' pin drives the gate of the switch via transformer.
pulse_out_pin = 10
pulseOut = Pin(pulse_out_pin, Pin.OUT)

# Originally 'pulseOut' directly drove the transformer so we increased
# slew rate & drive. This wasn't enough so MOSFET was added to design,
# but the high slew & drive is left set. Potentially we could modulate
# the drive signal slightly by adjusting drive strength?
machine.mem32[0x4 + 0x04*pulse_out_pin + 0x4001c000] = 0b1110011
pulseOut.low()

enabled = False
oldButtonArm = False

timeout_start = utime.ticks_ms()


def update(buttonArm, buttonPulse, charged):
    global state

    if state == "Startup":
        handle_startup()
    if state == "Disarmed":
        handle_disarmed(buttonArm)
    elif state == "Armed":
        handle_armed(buttonArm, buttonPulse, charged)
    elif state == "Low Power":
        handle_low_power()
    elif state == "Sound On":
        handle_sound_on()
    elif state == "Sound Off":
        handle_sound_off()


def handle_startup():
    global state
    global state_changed
    global animation_changed

    # Implement startup logic
    wp.play("startup.wav", loop=False)
    while wp.isplaying() == True:
        pass
    
    if buttonArm.value():
        state = "Armed"
    else:
        state = "Disarmed"
    state_changed = True
    animation_changed = True

def handle_disarmed(buttonArm):
    global state
    global state_changed
    global animation_changed

    if state_changed:
        ledArm.off()
        pwm_off()
        ledHv.off()
        if sound_on:
            wp.play("disarm.wav", loop=False)
            while wp.isplaying() == True:
                time.sleep(0.1) 

    if buttonArm.value():
        print("Arming")
        state = "Armed"
        state_changed = True
        animation_changed = True
        return
    
    if buttonPulse.value():
        print("Pulse Button Pressed while disarmed")
        if (sound_on):
            wp.play("boom.wav", loop=False)
            while wp.isplaying() == True:
                state = "Error"
            state = "Disarmed"
    
    state_changed = False

def handle_armed(buttonArm, buttonPulse, charged):
    global state
    global timeout_start
    global state_changed
    global firing_song_index
    global animation_changed

    fired = False

    if state_changed:
        ledArm.on()
        pwm_on()
        # Used to sleep HV
        timeout_start = utime.ticks_ms()
        
        if sound_on:
            wp.play("arm.wav", loop=False)
            while wp.isplaying() == True:
                time.sleep(0.1)


    if not buttonArm.value():
        print("Disarming")
        state = "Disarmed"
        state_changed = True
        animation_changed = True
        return
    
    if not charged.value():
        # Handle not charged logic
        ledHv.off()
        return
    else:
        ledHv.on()

    
    while buttonPulse.value():
        fired = True 
        state = "Firing"
        state_changed = True
        animation_changed = True
        if sound_on:
            wp.play(firing_song[firing_song_index], loop=False)   
        # Handle pulse logic
        pulseOut.high()
        utime.sleep_us(5)
        pulseOut.low()

        # Used to sleep HV
        timeout_start = utime.ticks_ms()

        # Force delay between pulses, allowing you to
        # hold down button. If you want one-shot operation
        # add code to check previous value like with 'arm'
        # button. Note HV circuit takes ~2-3 seconds to
        # recover so 2nd and later pulses not as strong.
        utime.sleep_ms(250)
        state = "Armed"
        while wp.isplaying() == True:
            time.sleep(0.1)
    
    if fired:
        firing_song_index += 1
        firing_song_index %= len(firing_song)
    
    # Check for timeout to switch to low power or disable
    if utime.ticks_diff(utime.ticks_ms(), timeout_start) > 60000:
        state = "Low Power"
        state_changed = True
        return
    
    state_changed = False

def handle_low_power():
    global state
    global substate
    global low_power_song
    global low_power_song_index
    global state_changed

    if state_changed:
        low_power_song_index = 0
        ledArm.off()
        pwm_off()
        ledHv.off()


    # Implement low power logic
    if substate == "None":
        #start with the chase animation
        substate = "Chase"

    if buttonPulse.value():
        print("Pulse Button Pressed while in low power mode")
        if (sound_on):
            wp.play(low_power_song[low_power_song_index], loop=False)
            while wp.isplaying() == True:
                time.sleep(0.1)

            low_power_song_index += 1
            low_power_song_index %= len(low_power_song)

    state_changed = False


def handle_sound_on():
    global state
    global substate
    global state_changed
    global animation_changed

    wp.play("soundon.wav", loop=False)
    while wp.isplaying() == True:
        time.sleep(0.1)

    state = substate
    substate = "None"
    state_changed = False
    animation_changed = True

def handle_sound_off():
    global state
    global substate
    global state_changed

    wp.play("nosound.wav", loop=False)
    while wp.isplaying() == True:
        time.sleep(0.1)

    state = substate
    substate = "None"
    state_changed = True


# Start the animation thread
_thread.start_new_thread(animation_thread, ())

# Start the main loop
try:

    while running:
        update(buttonArm, buttonPulse, charged)
        time.sleep(0.1)

except KeyboardInterrupt:
    running = False
    print("Keyboard Interrupt")


_thread.exit()

