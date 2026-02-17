import keyboard
import time


def read_rfid_card():

    badge = ""
    key_interval = 0.1
    initial_time = time.time()

    while True:
        event_read = keyboard.read_event()

        if event_read.event_type == keyboard.KEY_DOWN:
            current_time = time.time()

            if current_time - initial_time < key_interval:
                badge += event_read.name
            else:
                if badge:
                    badge_formated = badge.replace("enter", "").replace("enter", "")
                    return badge_formated
                badge = ""

            initial_time = current_time

            if event_read.name == 'enter' and badge:
                badge_formated = badge.replace("enter", "").replace("shift", "")
                return badge_formated



