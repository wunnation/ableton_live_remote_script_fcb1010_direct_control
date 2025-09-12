# fcb1010_historical_looper.py
# MIDI Remote Script for Ableton Live
# Maps CC 96 to a function that mimics the Max for Live "bang" script
# Developed for Live 12.0

import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import MIDI_CC_TYPE
from Launchpad.ConfigurableButtonElement import ConfigurableButtonElement
from functools import partial
import os

SCRIPT_VERSION = "v0.1.0"

class fcb1010_historical_looper(ControlSurface):
    def __init__(self, c_instance):
        super().__init__(c_instance)
        self._send_midi = self._c_instance.send_midi

        with self.component_guard():
            global _map_modes
            _map_modes = Live.MidiMap.MapMode

            self.led_on = 127
            self.led_off = 0

            self.track_clip_trigger = []

            self.log_message(f"{os.path.basename(__file__)} {SCRIPT_VERSION} initialized.")

            # Create button for CC 96 on channel 13
            button = self.create_button(channel=13, cc=96)
            self.track_clip_trigger.append(button)

            # Assign the button to the historical looper function
            button.add_value_listener(
                partial(self.historical_looper_bang, button=button),
                identify_sender=False
            )

    def create_button(self, channel, cc):
        return ConfigurableButtonElement(
            is_momentary=True,
            msg_type=MIDI_CC_TYPE,
            channel=channel,
            identifier=cc
        )

    def historical_looper_bang(self, value, button):
        if value != 127:
            return

        song = self.song()
        view = song.view
        selected_track = view.selected_track
        track_index = list(song.tracks).index(selected_track)
        track_id = selected_track._live_ptr

        self.log_message(f"Track ID: {track_id}")
        self.log_message(f"Track Number: {track_index}")
        self.log_message(f"Track Name: {selected_track.name}")

        clip_slots = selected_track.clip_slots
        clip_slot_count = len(clip_slots)
        self.log_message(f"Total Clips: {clip_slot_count}")

        has_clip_count = 0
        last_clip_slot_index = -1

        for j, clip_slot in enumerate(clip_slots):
            if not clip_slot.has_clip:
                continue

            has_clip_count += 1
            clip = clip_slot.clip
            last_clip_slot_index = j

            is_recording = clip_slot.is_recording
            is_playing = clip_slot.is_playing

            song_time = song.current_song_time
            clip_start = clip.start_time
            clip_length = song_time - clip_start

            loop_end = ((clip_length + 3.999) // 4) * 4
            loop_start = max(loop_end - 16.0, 0)

            if is_recording or is_playing:
                self.log_message(f"{'Recording' if is_recording else 'Playing'} Clip Found at Slot: {j}")
                clip.loop_start = loop_start
                clip.loop_end = loop_end
                clip.looping = True

                self.log_message(f"Loop set from {loop_start} to {loop_end} for clip at slot {j}")

        self.log_message(f"Last Available Clip Slot Index: {last_clip_slot_index}")
        self.log_message(f"hasClipCount: {has_clip_count}")
