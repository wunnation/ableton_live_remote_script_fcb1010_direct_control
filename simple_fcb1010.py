
#
import Live
from _Framework.ControlSurface import ControlSurface

#
from functools import partial

class simple_fcb1010(ControlSurface):
    def __init__(self, c_instance):
        super().__init__(c_instance)
        self.c_instance = c_instance

        if self.song() is None:
            self.log_message("Error: Unable to Access Ableton's Song Object.")

        self.led_on = 127  # Example LED values
        self.led_off = 0

        self.track_clips_direct = []  # Stores all MIDI buttons

        # Initialize MIDI buttons dynamically
        for i in range(13, 93):  # CC values spanning 9 tracks (10 per track)
            setattr(self, f'midi_cc_ch_13_val_{i}', ConfigurableButtonElement(True, MIDI_CC_TYPE, 13, i))
            button = getattr(self, f'midi_cc_ch_13_val_{i}')
            button.set_on_off_values(self.led_on, self.led_off)
            button.add_value_listener(self.placehold_listener, identify_sender=False)
            button.pre_val = 0
            button.cur_val = 0
            self.track_clips_direct.append(button)

        # Assign each button to the corresponding clip launcher
        for track_index in range(9):  # Tracks 2–10 (zero-based index)
            start_index = track_index * 10 + 13
            end_index = start_index + 10
            track_buttons = self.track_clips_direct[start_index - 13:end_index - 13]  # Slice the correct buttons

            if track_index + 1 < len(self.song().tracks):  # Ensure valid track index
                for i, button in enumerate(track_buttons):
                    clip_slot = self.song().tracks[track_index + 1].clip_slots[i]  # Tracks 2–10
                    # button.add_value_listener(partial(lambda value, clip: clip.fire() if value == 127 else None, clip=clip_slot))
                    button.add_value_listener(partial(lambda value, clip: clip.fire(), clip=clip_slot))

    def placehold_listener(self, value):
        """Placeholder listener function for MIDI buttons."""
        self.c_instance.show_message(f"clip {value} triggered!")
        print(f"placeholder listener: {value}")
        pass

    # def song(self):
    #     """Mock function to represent Ableton Live API access."""
    #     # return self.c_instance.song()
    #     return self.c_instance.song() if hasattr(self, 'c_instance') else None
    #     # return Live.Application.get_application().get_document()

    def song(self):
        if hasattr(self, 'c_instance'):
            if self.c_instance is not None:
                return self.c_instance.song()
            else:
                print("Error: self.c_instance is None. Unable to access song.")
                return None
        else:
            print("Error: No attribute self.c_instance")
