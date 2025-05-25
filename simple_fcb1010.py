import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.Dependency import inject, depends
from _Framework.InputControlElement import MIDI_CC_TYPE
# from Launchpad.ConfigurableButtonElement import ConfigurableButtonElement
#
from _Framework.Layer import Layer
from _Framework.DeviceComponent import DeviceComponent
from _Framework.MixerComponent import MixerComponent
from _Framework.SliderElement import SliderElement
from _Framework.TransportComponent import TransportComponent
from _Framework.InputControlElement import *
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.SessionComponent import SessionComponent
from _Framework.EncoderElement import *
from Launchpad.ConfigurableButtonElement import ConfigurableButtonElement
#
from functools import partial

# @depends(send_midi=None)
def make_button(channel, cc, send_midi=None):
    return ConfigurableButtonElement(
        is_momentary=True,
        msg_type=MIDI_CC_TYPE,
        channel=channel,
        identifier=cc,
        # send_midi=send_midi
    )

class simple_fcb1010(ControlSurface):
    def __init__(self, c_instance):
        super().__init__(c_instance)
        self._send_midi = self._c_instance.send_midi  # <- get it manually
        # with inject(send_midi=c_instance.send_midi).everywhere():
        global _map_modes
        with self.component_guard():
            _map_modes = Live.MidiMap.MapMode
            self._setup_controls()

    def _setup_controls(self):
        self.led_on = 127
        self.led_off = 0
        self.track_clips_direct = []
        self.log_message("simple_fcb1010 initialized.")

        for cc in range(13, 93):
            button = self.create_button(channel=13, cc=cc)
            self.track_clips_direct.append(button)

        self.assign_buttons_to_clips()

    def create_button(self, channel, cc):
        # with inject(send_midi=self._c_instance.send_midi).everywhere():
        return make_button(channel, cc)

    # def create_button(self, channel, cc):
    # # def create_button(self, channel, cc):
    #     return make_button(channel, cc, self._send_midi)
    #     # send_midi = find_dependency('send_midi')
    #     # return ConfigurableButtonElement(
    #     #     is_momentary=True,
    #     #     msg_type=MIDI_CC_TYPE,
    #     #     channel=channel,
    #     #     identifier=cc,
    #     #     send_midi=send_midi
    #     # )

    def assign_buttons_to_clips(self):
        song = self.song()
        if not song:
            self.log_message("Unable to get song object.")
            return

        for track_index in range(9):  # Tracks 2–10
            start_index = track_index * 10
            track_buttons = self.track_clips_direct[start_index:start_index + 10]

            track_num = track_index + 1
            if track_num < len(song.tracks):
                track = song.tracks[track_num]
                for i, button in enumerate(track_buttons):
                    if i < len(track.clip_slots):
                        clip_slot = track.clip_slots[i]
                        button.add_value_listener(
                            partial(self.fire_clip_if_full_press, clip=clip_slot),
                            identify_sender=False
                        )
                        self.log_message(f"Mapped CC {13 + start_index + i} to Track {track_num}, Slot {i}")
            else:
                self.log_message(f"Track index {track_num} out of bounds.")

    def fire_clip_if_full_press(self, value, clip):
        if value == 127:
            clip.fire()
