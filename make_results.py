import matplotlib.pyplot as mplt
from matplotlib import cm
import pandas as pd
import numpy as np
from math import floor
import ctypes
import os
user32 = ctypes.windll.user32

df_keyboard = ''
df_mouse = ''
screen_size = ()
foldername = 'data'


filename_mouse = '00_dump_mouse.csv'
filename_keyboard = '00_dump_keyboard.csv'
filename_screensize = '00_screen.csv'

filename_img_clicks = '01_heatmap_clicks.png'
filename_img_movement = '02_heatmap_movement.png'
filename_mousepath = '03_mousepath.png'
filename_exact_data = '04_data.txt'

def load_data():
    global df_keyboard, df_mouse, screen_size, filename_mouse, filename_keyboard, filename_screensize
    df_keyboard = pd.read_csv(filename_keyboard, sep=';')
    df_mouse = pd.read_csv(filename_mouse, sep=';')
    df_screen = pd.read_csv(filename_screensize, sep=';')
    screen_size = (df_screen['width'][0], df_screen['height'][0])


def create_mouse_path(df_mouse_moves, df_mouse_clicks):
    screen_width, screen_height = screen_size

    fig, axes = mplt.subplots(figsize=(screen_width/200, screen_height/200))
    axes.set_xlabel('x')
    axes.set_xlim(0, screen_width)

    axes.set_ylabel('y')
    axes.set_ylim(0, screen_height)
    axes.invert_yaxis()

    axes.set_aspect('equal')

    # axes.set_title('title');

    x = df_mouse_moves['pos_x'].tolist()
    y = df_mouse_moves['pos_y'].tolist()
    line, = axes.plot(x, y, '-', lw=0.3, color='#222222', alpha=0.7)

    x = df_mouse_clicks['pos_x'].tolist()
    y = df_mouse_clicks['pos_y'].tolist()
    line, = axes.plot(x, y, 'o', color='#222222', alpha=0.3)

    fig.savefig(filename_mousepath, bbox_inches='tight', dpi=200)


def create_heatmap(df_coordinates, filename, data_type='clicks'):
    screen_width, screen_height = screen_size
    gridsize = 60
    bins = gridsize * 4
    coordinates_pos_x = df_coordinates['pos_x'].values
    coordinates_pos_y = df_coordinates['pos_y'].values
    x = np.append(coordinates_pos_x, [0, screen_width])  # make sure the x and y axes go from 0 to screen_width and create a square heatmap that is later cropped
    y = np.append(coordinates_pos_y, [0, screen_width])
    heatmap, xedges, yedges = np.histogram2d(x, y, bins=bins)
    heatmap = heatmap.T
    if data_type == 'clicks' or data_type == 'movement':
    	heatmap[0][0] = 0
    # print()
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

    x = y = np.linspace(0, xedges[-1], bins)
    X, Y = np.meshgrid(x, y)
    x = X.ravel()
    y = Y.ravel()
    z = heatmap.ravel()

    fig, axes = mplt.subplots(figsize=(screen_width/200, screen_height/200))
    axes.set_xlabel('x')
    axes.set_xlim(0, screen_width)

    axes.set_ylabel('y')
    axes.set_ylim(0, screen_height)
    axes.invert_yaxis()

    axes.set_aspect('equal')

    hb = axes.hexbin(x, y, C=z, gridsize=gridsize, cmap=cm.viridis, bins=None)
    cb = fig.colorbar(hb)
    cb.set_label('Anzahl Clicks')

    fig.savefig(filename, bbox_inches='tight', dpi=200)


def calculate_length_of_mouse_trail(df_mouse_moves):
    coordinates = df_mouse_moves[['pos_x', 'pos_y']].values
    # Length between corners
    lengths = np.sqrt(np.sum(np.diff(coordinates, axis=0)**2, axis=1))
    total_length = np.sum(lengths)
    return total_length


def calculate_total_time_ms(df_mouse):
    return int(df_mouse['time'][-1:].values - df_mouse['time'][0:1].values)


def create_heatmap_clicks():
	create_heatmap(df_mouse_clicks, filename_img_clicks, 'clicks')


def create_heatmap_movements():
	create_heatmap(df_mouse_moves, filename_img_movement, 'movement')


def create_exact_data():
	length_trail = calculate_length_of_mouse_trail(df_mouse_moves)
	output = "{:10.0f} px zurückgelegt\n".format(length_trail)

	time_total = calculate_total_time_ms(df_mouse) / 1000
	time_total_min = time_total / 60
	time_total_h = floor(time_total_min / 60)
	time_total_min = time_total_min - time_total_h * 60
	output += "{:10.0f} s gemessen ({:.0f} h und {:.0f} min)\n".format(time_total, time_total_h, time_total_min)

	output += "{:10.0f} Mausclicks links ({:.0f} clicks/min)\n".format(df_mouse_down_left.shape[0], df_mouse_down_left.shape[0] / time_total * 60)
	output += "{:10.0f} Mausclicks mitte ({:.0f} clicks/min)\n".format(df_mouse_down_middle.shape[0], df_mouse_down_middle.shape[0] / time_total * 60)
	output += "{:10.0f} Mausclicks rechts ({:.0f} clicks/min)\n".format(df_mouse_down_right.shape[0], df_mouse_down_right.shape[0] / time_total * 60)
	output += "{:10.0f} Mausraddrehungen ({:.0f} Drehungen/min)\n".format(df_mouse_wheel.shape[0], df_mouse_wheel.shape[0] / time_total * 60)
	num_key_down = df_keyboard.query('event_type == "key_down"').shape[0]
	output += "{:10.0f} Tastenanschlaege ({:.0f} Tastenanschläge/min)\n".format(num_key_down, num_key_down / time_total * 60)

	with open(filename_exact_data, 'w') as f:
		f.write(output)


def is_int(number):
    try:
        int(number)
        return True
    except ValueError:
        return False


def determine_data_set():
    global foldername, filename_mouse, filename_keyboard, filename_screensize, filename_img_clicks, filename_img_movement, filename_mousepath, filename_exact_data

    print("Which user should be loaded?")
    user_list = [uid for uid in os.listdir(foldername) if os.path.isdir(os.path.join(foldername, uid))]
    print()
    print("--ID--NAME-------")
    for pair in enumerate(user_list):
        print("{id:4.0f}  {name}".format(id=pair[0]+1, name=pair[1]))
    print()

    user_id_num = ''
    while not is_int(user_id_num):
        user_id_num = input("Please enter ID: ")
        if is_int(user_id_num) and int(user_id_num) >= 1 and int(user_id_num) <= len(user_list):
            user_id_num = int(user_id_num) - 1
            break
        user_id_num = ''
        print ("Please enter valid ID from 1 to {}".format(len(user_list)))

    user_id = user_list[user_id_num]
    foldername = os.path.join(foldername, user_id)
    print("User \"{}\" selected".format(user_id))

    print()

    print("Which datapoint should be loaded?")
    datapoint_list = [datapoint for datapoint in os.listdir(foldername) if os.path.isdir(os.path.join(foldername, datapoint))]
    print()
    print("--ID--DATAPOINT--")
    for pair in enumerate(datapoint_list):
        print("{id:4.0f}  {name}".format(id=pair[0]+1, name=pair[1]))
    print()

    datapoint_num = ''
    while not is_int(datapoint_num):
        datapoint_num = input("Please enter ID: ")
        if is_int(datapoint_num) and int(datapoint_num) >= 1 and int(datapoint_num) <= len(datapoint_list):
            datapoint_num = int(datapoint_num) - 1
            break
        datapoint_num = ''
        print ("Please enter valid ID from 1 to {}".format(len(datapoint_list)))

    datapoint = datapoint_list[datapoint_num]
    foldername = os.path.join(foldername, datapoint)
    print("Datapoint \"{}\" selected".format(datapoint))

    print()

    filename_mouse = os.path.join(foldername, filename_mouse)
    filename_keyboard = os.path.join(foldername, filename_keyboard)
    filename_screensize = os.path.join(foldername, filename_screensize)

    filename_img_clicks = os.path.join(foldername, filename_img_clicks)
    filename_img_movement = os.path.join(foldername, filename_img_movement)
    filename_mousepath = os.path.join(foldername, filename_mousepath)
    filename_exact_data = os.path.join(foldername, filename_exact_data)


determine_data_set()

load_data()


df_mouse = df_mouse#[0:2000]
df_mouse_down_left = df_mouse.query('event_type == "mouse_down_left"')
df_mouse_down_middle = df_mouse.query('event_type == "mouse_down_middle"')
df_mouse_down_right = df_mouse.query('event_type == "mouse_down_right"')
df_mouse_wheel = df_mouse.query('event_type == "mouse_wheel"')
df_mouse_clicks = df_mouse.query('event_type == "mouse_down_left" or event_type == "mouse_down_middle" or event_type == "mouse_down_right"')
df_mouse_moves = df_mouse.query('event_type == "mouse_move"')
create_mouse_path(df_mouse_moves, df_mouse_clicks)
print("Mauspfad berechnet.")
create_heatmap_clicks()
print("Heatmap Clicks erstellt.")
create_heatmap_movements()
print("Heatmap Mausbewegungen erstellt.")
create_exact_data()
print("Exakte Daten berechnet.")
