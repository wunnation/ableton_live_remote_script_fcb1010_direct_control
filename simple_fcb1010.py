# Import Ableton Live Python API
import Live

# Import the base class for control surfaces
from _Framework.ControlSurface import ControlSurface

# Import constant for MIDI Continuous Controller messages
from _Framework.InputControlElement import MIDI_CC_TYPE

# Import a configurable button class (used for each footswitch on the FCB1010)
from Launchpad.ConfigurableButtonElement import ConfigurableButtonElement

# Used to bind parameters to functions (for listener callbacks)
from functools import partial

# Define the main class for the FCB1010 script
class simple_fcb1010(ControlSurface):
    def __init__(self, c_instance):
        # Call the superclass constructor with the Ableton instance
        super().__init__(c_instance)

        # Manually assign the _send_midi function (used to send raw MIDI messages if needed)
        self._send_midi = self._c_instance.send_midi

        # Use the component_guard context manager to ensure safe setup (avoids race conditions during load)
        with self.component_guard():
            # Assign Live's MapMode object to a global so it can be used elsewhere if needed
            global _map_modes
            _map_modes = Live.MidiMap.MapMode

            # Set up all the MIDI button controls
            self._setup_controls()

    # Set up MIDI controls from the FCB1010 (buttons/footswitches)
    def _setup_controls(self):
        # Define LED on/off values (if sending feedback later)
        self.led_on = 127
        self.led_off = 0

        # This will store the 80 buttons (CC 13–92) in a flat list
        self.track_clips_direct = []

        # Log a message to Ableton's internal console
        self.log_message("simple_fcb1010 initialized.")

        # Create button objects for CC messages 13–92 on channel 13 (80 buttons total)
        for cc in range(13, 93):
            button = self.create_button(channel=13, cc=cc)
            self.track_clips_direct.append(button)

        # Link each button to a specific clip slot
        self.assign_buttons_to_clips()

    # Create a single button element for a given MIDI channel and CC number
    def create_button(self, channel, cc):
        return ConfigurableButtonElement(
            is_momentary=True,       # FCB1010 buttons act like momentary switches
            msg_type=MIDI_CC_TYPE,   # Use MIDI CC messages
            channel=channel,         # MIDI channel the FCB1010 is sending on
            identifier=cc            # CC number (13–92)
        )

    # Assign buttons to clip slots on tracks in the Live set
    def assign_buttons_to_clips(self):
        # Get the current Live "song" (a.k.a. the Live Set)
        song = self.song()
        if not song:
            self.log_message("Unable to get song object.")
            return

        # Loop through 9 tracks (tracks 2–10; track 0 = Master, track 1 = usually not used here)
        for track_index in range(9):
            # Each track gets 10 buttons (total 9*10 = 90, but we use 80, so last one may be unused)
            start_index = track_index * 10
            track_buttons = self.track_clips_direct[start_index:start_index + 10]

            # Ableton tracks are zero-indexed; we start at track 1 (second track)
            track_num = track_index + 1

            # Check if track exists before trying to assign buttons
            if track_num < len(song.tracks):
                track = song.tracks[track_num]

                # Assign each button to the corresponding clip slot (if it exists)
                for i, button in enumerate(track_buttons):
                    if i < len(track.clip_slots):
                        clip_slot = track.clip_slots[i]

                        # Add a listener that fires the clip when the button is fully pressed (value 127)
                        button.add_value_listener(
                            partial(self.fire_clip_if_full_press, clip=clip_slot),
                            identify_sender=False
                        )
            else:
                # Log a warning if trying to map to a non-existent track
                self.log_message(f"Track index {track_num} out of bounds.")

    # Callback: Trigger clip if value equals 127 (i.e., full press from foot controller)
    def fire_clip_if_full_press(self, value, clip):
        if value == 127:
            clip.fire()
