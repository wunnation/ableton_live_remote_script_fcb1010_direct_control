from .simple_fcb1010 import simple_fcb1010

def create_instance(c_instance):
    return simple_fcb1010(c_instance)

# from _Framework.Dependency import inject
# from .simple_fcb1010 import simple_fcb1010

# def create_instance(c_instance):
#     def factory():
#         return simple_fcb1010(c_instance)

#     def send_midi_wrapped(*args, **kwargs):
#         return c_instance.send_midi(*args, **kwargs)

#     with inject(send_midi=send_midi_wrapped).everywhere():
#         return factory()