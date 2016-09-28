import sys
import time
from collections import namedtuple
import numpy as np
import os
# import pandas as pd  # slow
# from pandas import DataFrame
import pyhooker
import ctypes
import re
import datetime as dt
import csv

# # used for pyinstaller
# import six
# import packaging
# import packaging.version
# import packaging.specifiers
# import packaging.requirements
# # /pyinstaller

user32 = ctypes.windll.user32




def handler_mouse(event):
    global pos_x, pos_y, clicks, pts
    mouse_events.append(event)
    pos_x = event.pos_x
    pos_y = event.pos_y
    if event.event_type == 'mouse_move':
        pts.append((pos_x, pos_y))
    elif event.event_type[6:10] == 'down':
        clicks.append((pos_x, pos_y))
        num_clicks[event.event_type[11:]] += 1
        refresh_screen(True)
    elif event.event_type[6:] == 'wheel':
        num_clicks['wheel'] += 1
        # if event.event_type[11:] == 'left':
    refresh_screen()


def handler_keyboard(event):
    key_events.append(event)
    refresh_screen(True)


def calculate_length_of_mouse_trail():
    global pts
    # Length between corners
    lengths = np.sqrt(np.sum(np.diff(pts, axis=0)**2, axis=1))
    total_length = np.sum(lengths)
    return total_length


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def save_results():
    global pts, clicks

    cls()
    print("Saving data...")

    save_data_to_file()
    sys.exit()
    cls()
    print("Finished saving.")
    print("You may now close the window.")


def init_file_structure():
    global key_events, mouse_events

    user32.SetProcessDPIAware()
    screen_width = user32.GetSystemMetrics(78)  # use 0 for current monitor
    screen_height = user32.GetSystemMetrics(79)  # use 1 for current monitor

    screen_size = {"width": screen_width, "height": screen_height}
    with open(filename_screensize, 'w', newline='') as f:
        writer = csv.DictWriter(f, screen_size.keys(), delimiter=';')
        writer.writeheader()
        writer.writerow(screen_size)

    with open(filename_mouse, 'w', newline='') as f:
        writer = csv.DictWriter(f, pyhooker.MouseEvent._fields, delimiter=';')
        writer.writeheader()
        writer.writerows([evt._asdict() for evt in mouse_events])
        mouse_events = []

    with open(filename_keyboard, 'w', newline='') as f:
        writer = csv.DictWriter(f, pyhooker.KeyboardEvent._fields, delimiter=';')
        writer.writeheader()
        writer.writerows([evt._asdict() for evt in key_events])
        key_events = []


    # df_mouse = pd.DataFrame(data=list(mouse_events))
    # mouse_events = deque()
    # df_mouse.to_csv(filename_mouse, sep=';', index=False)
    # df_mouse = None

    # df_keyboard = pd.DataFrame(data=list(key_events))
    # # key_events = deque()
    # key_events = []
    # df_keyboard.to_csv(filename_keyboard, sep=';', index=False)
    # df_keyboard = None


def append_data_to_files():
    global key_events, mouse_events

    with open(filename_mouse, 'a', newline='') as f:
        writer = csv.DictWriter(f, pyhooker.MouseEvent._fields, delimiter=';')
        # writer.writeheader()
        writer.writerows([evt._asdict() for evt in mouse_events])
        mouse_events = []

    with open(filename_keyboard, 'a', newline='') as f:
        writer = csv.DictWriter(f, pyhooker.KeyboardEvent._fields, delimiter=';')
        # writer.writeheader()
        writer.writerows([evt._asdict() for evt in key_events])
        key_events = []

    # with open(filename_mouse, 'a') as f:
    #     df_mouse = pd.DataFrame(data=list(mouse_events))
    #     mouse_events = []
    #     # mouse_events = deque()
    #     df_mouse.to_csv(f, sep=';', index=False, header=False)
    #     df_mouse = None

    # with open(filename_keyboard, 'a') as f:
    #     df_keyboard = pd.DataFrame(data=list(key_events))
    #     key_events = []
    #     # key_events = deque()
    #     df_keyboard.to_csv(f, sep=';', index=False, header=False)
    #     df_keyboard = None


def save_data_to_file():
    global key_events, mouse_events

    if os.path.isfile(filename_mouse):
        append_data_to_files()
    else:
        init_file_structure()


i = 49
def refresh_screen(forced_refresh=False):
    global pos_x, pos_y, num_clicks, i, key_events
    i += 1
    if i >= 20 or forced_refresh is True:
        cls()
        sys.stdout.write("         X: {:8.0f}\n".format(pos_x))
        sys.stdout.write("         Y: {:8.0f}\n".format(pos_y))
        sys.stdout.write("      Left: {:8.0f}\n".format(num_clicks['left']))
        sys.stdout.write("    Middle: {:8.0f}\n".format(num_clicks['middle']))
        sys.stdout.write("     Right: {:8.0f}\n".format(num_clicks['right']))
        sys.stdout.write("     Wheel: {:8.0f}\n".format(num_clicks['wheel']))
        # sys.stdout.write("  Distance: {:8.0f}\n".format(calculate_length_of_mouse_trail()))
        if key_events:
            sys.stdout.write("  Last Key: {}\n".format(key_events[-1].key_code_readable.rjust(8, ' ')))
        i = 0

        if len(mouse_events) > 100:
            save_data_to_file()


def determine_user_id():
    userid_raw = input("Enter user ID: ")

    if re.match("^[A-Za-z0-9_-]*$", userid_raw):
        return userid_raw
    else:
        print("Only use the characters A-Za-z0-9_-")
        return determine_user_id()


def init():
    global foldername, filename_mouse, filename_keyboard, filename_screensize
    userid = determine_user_id()

    print(userid)
    date_now = dt.datetime.now()
    date_formatted = date_now.strftime('%Y%m%d-%H%M')
    foldername = foldername.format(userid=userid, date=date_formatted)

    if not os.path.exists(foldername):
        os.makedirs(foldername)

    filename_mouse = filename_mouse.format(foldername=foldername)
    filename_keyboard = filename_keyboard.format(foldername=foldername)
    filename_screensize = filename_screensize.format(foldername=foldername)

    if os.path.exists(filename_mouse):
        os.remove(filename_mouse)
    if os.path.exists(filename_keyboard):
        os.remove(filename_keyboard)

    pyHooker = pyhooker.PyHooker()
    pyHooker.set_handler_mouse(handler_mouse)
    pyHooker.set_handler_keyboard(handler_keyboard)
    pyHooker.set_handler_destruct(save_results)
    pyHooker.listen()



if __name__ == "__main__":
    pts = []


    pos_x = 0
    pos_y = 0
    pts = []
    clicks = []
    num_clicks = dict(left=0, middle=0, right=0, wheel=0)
    mouse_events = []
    key_events = []
    # mouse_events = deque()
    # key_events = deque()
    userid = ''

    foldername = 'data/{userid}/{date}'

    filename_mouse = '{foldername}/00_dump_mouse.csv'
    filename_keyboard = '{foldername}/00_dump_keyboard.csv'
    filename_screensize = '{foldername}/00_screen.csv'
    init()
