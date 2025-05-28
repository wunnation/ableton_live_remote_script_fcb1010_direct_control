# Import Ableton Live Python API
import Live

# Import the base class for control surfaces
from _Framework.ControlSurface import ControlSurface

# Import constant for MIDI Continuous Controller messages
from _Framework.InputControlElement import MIDI_CC_TYPE

# Import a configurable button class (used for each footswitch on the FCB1010)
from Launchpad.ConfigurableButtonElement import ConfigurableButtonElement
from _Framework.SessionComponent import SessionComponent
from _Framework.ButtonElement import ButtonElement

# Used to bind parameters to functions (for listener callbacks)
from functools import partial
import os

SCRIPT_VERSION = "v0.1.0"
# Developed with Ableton Live 12.0

START_BANK = 1 # Valid: 0-9, a value 1 is skipping bank 0 # TODO: This is not linked into create button objects
NUM_SCENES = 8 # Valid: 1-10, a value of 8 is only using 8 of the maximum 10 scenes (leaving two banks open)
START_SCENE = 0 # 0 is what is labeled as 'Scene 1' in the Ableton Live UI
START_TRACK = 0 # this supports 4 tracks. 0 is 'Track 1' in Ableton Live UI
NUM_TRACKS = 4
# 
SINGLE_BANK_LAUNCH_SCENE_IDS = [0]
SINGLE_BANK_LAUNCH_CLIP_IDS = [1, 2, 3, 4] # Track A, B, C, D in current scene
SINGLE_BANK_STOP_CLIP_IDS = [6, 7, 8, 9] # Track A, B, C, D
SINGLE_BANK_STOP_ALL_TRACK_CLIPS = [5]




# Define the main class for the FCB1010 script
class fcb1010_by_scene(ControlSurface):
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
        self.all_buttons = []

        # Log a message to Ableton's internal console
        # self.log_message(f"{os.path.basename(__file__)} initialized.")
        self.log_message(f"{os.path.basename(__file__)} {SCRIPT_VERSION} initialized.")
        # self.log_message("simple_fcb1010 initialized.")

        # Create button objects for CC messages 13–92 on channel 13 (80 buttons total)
        for cc in range(13, 93): # 
            button = self.create_button(channel=13, cc=cc)
            self.all_buttons.append(button)

        # Link each button to a specific clip slot or function
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
        
        # loop through 8 Scenes
        for scene_index in range(NUM_SCENES):
            # Each Bank has 10 buttons, we are dedicating 1 bank to 1 scene.
            start_index = scene_index * 10
            # - get all button objects for this scene.
            scene_buttons = self.all_buttons[start_index:start_index + 10]
            
            # Ableton tracks are zero-indexed; we start at track 1 (second track)
            scene_num = scene_index + START_SCENE

            for i, button in enumerate(scene_buttons):
                # determine what type of button this is...
                # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (labeled 1-10 on fcb1010)
                if i in SINGLE_BANK_LAUNCH_SCENE_IDS:
                    # sub_index = SINGLE_BANK_LAUNCH_SCENE_IDS.index(i) (not used in scene launch)
                    if scene_num < len(song.scenes):
                        scene = song.scenes[scene_index]
                        button.add_value_listener(
                            partial(self.launch_scene_if_full_press_pass_ids, scene_num=scene_num),
                            # partial(self.launch_scene_if_full_press, scene=scene),
                            identify_sender=False
                        )
                elif i in SINGLE_BANK_STOP_CLIP_IDS:
                    # Get Track Number
                    track_num = SINGLE_BANK_STOP_CLIP_IDS.index(i)
                    if track_num < len(song.tracks):
                        # Assign Button Function to track object
                        track = song.tracks[track_num]
                        button.add_value_listener(
                            partial(self.stop_clips_if_full_press_pass_ids, track_num=track_num),
                            # partial(self.stop_clips_if_full_press, track=track),
                            identify_sender=False
                        )
                elif i in SINGLE_BANK_STOP_ALL_TRACK_CLIPS:
                    # Get Track Number
                    # track_num = SINGLE_BANK_STOP_ALL_TRACK_CLIPS.index(i) (not used in stop clips for all tracks)
                    tracks = []
                    track_nums = []
                    for track_num in range(START_TRACK, START_TRACK+NUM_TRACKS):
                        if track_num >= len(song.tracks):
                            break
                        else:
                            track = song.tracks[track_num]
                            tracks.append(track)
                            track_nums.append(track_num)
                    if track_nums:
                        # Assign Button Function to track object
                        button.add_value_listener(
                            # partial(self.stop_clips_for_all_tracks, tracks=tracks),
                            partial(self.stop_clips_for_all_tracks_pass_ids, track_nums=track_nums),
                            identify_sender=False
                        )
                elif i in SINGLE_BANK_LAUNCH_CLIP_IDS:
                    track_num = SINGLE_BANK_LAUNCH_CLIP_IDS.index(i)
                    if track_num < len(song.tracks):
                        track = song.tracks[track_num]
                        if scene_num < len(track.clip_slots):
                            clip_slot = track.clip_slots[scene_num]
                            button.add_value_listener(
                                # 
                                # partial(self.fire_clip_if_full_press, clip=clip_slot),
                                partial(self.fire_clip_if_full_press_pass_ids, scene_num=scene_num, track_num=track_num),
                                identify_sender=False
                            )


        # # Loop through 9 tracks (tracks 2–10; track 0 = Master, track 1 = usually not used here)
        # for track_index in range(9):
        #     # Each track gets 10 buttons (total 9*10 = 90, but we use 80, so last one may be unused)
        #     start_index = track_index * 10
        #     track_buttons = self.all_buttons[start_index:start_index + 10]

        #     # Ableton tracks are zero-indexed; we start at track 1 (second track)
        #     track_num = track_index + 1

        #     # Check if track exists before trying to assign buttons
        #     if track_num < len(song.tracks):
        #         track = song.tracks[track_num]

        #         # Assign each button to the appropriate function
        #         for i, button in enumerate(track_buttons):
        #             if i < 8 and i < len(track.clip_slots):
        #                 # Assign to clip slots 0–7
        #                 clip_slot = track.clip_slots[i]
        #                 button.add_value_listener(
        #                     partial(self.fire_clip_if_full_press, clip=clip_slot),
        #                     identify_sender=False
        #                 )
        #             elif i == 8:
        #                 # Button 9: Toggle record arm for the track
        #                 button.add_value_listener(
        #                     partial(self.toggle_arm_if_full_press, track=track),
        #                     identify_sender=False
        #                 )
        #             elif i == 9:
        #                 # Button 10: Stop all clips on the track
        #                 button.add_value_listener(
        #                     partial(self.stop_clips_if_full_press, track=track),
        #                     identify_sender=False
        #                 )
        #     else:
        #         # Log a warning if trying to map to a non-existent track
        #         self.log_message(f"Track index {track_num} out of bounds.")


    # Callback: Trigger clip if value equals 127 (i.e., full press from foot controller)
    # def fire_clip_if_full_press(self, value, clip):
    #     if value == 127:
    #         clip.fire()

    # Pass ids instead of objects, so that position stays same even if user moves tracks and scenes around
    def fire_clip_if_full_press_pass_ids(self, value, scene_num, track_num):
        if value != 127:
            return
        song = self.song()
        if track_num < len(song.tracks):
            track = song.tracks[track_num]
            if scene_num < len(track.clip_slots):
                clip = track.clip_slots[scene_num]
                clip.fire()

    # Callback: Toggle arm if value equals 127
    def toggle_arm_if_full_press(self, value, track):
        if value == 127 and track.can_be_armed:
            track.arm = not track.arm

    def toggle_arm_if_full_press_pass_ids(self, value, track_num):
        if value != 127:
            return
        song = self.song()
        if track_num < len(song.tracks):
            track = song.tracks[track_num]       
            if track.can_be_armed:
                track.arm = not track.arm


    # Callback: Stop all clips (single track) if value equals 127
    def stop_clips_if_full_press(self, value, track):
        if value == 127:
            track.stop_all_clips()

    def stop_clips_if_full_press_pass_ids(self, value, track_num):
        if value != 127:
            return
        song = self.song()
        if track_num < len(song.tracks):
            track = song.tracks[track_num]
            track.stop_all_clips()

    # Callback: Stop all clips (all looped tracks) if value equals 127
    def stop_clips_for_all_tracks(self, value, tracks):
        if value != 127:
            return
        for track in tracks:
            track.stop_all_clips()
        
    def stop_clips_for_all_tracks_pass_ids(self, value, track_nums):
        if value != 127:
            return
        song = self.song()
        for track_num in track_nums:
            if track_num < len(song.tracks):
                track = song.tracks[track_num]
                track.stop_all_clips()

    def launch_scene_if_full_press(self, value, scene):
        if value == 127:
            scene.fire()

    def launch_scene_if_full_press_pass_ids(self, value, scene_num):
        if value != 127:
            return
        song = self.song()
        if scene_num < len(song.scenes):
            scene = song.scenes[scene_num]
            scene.fire()
