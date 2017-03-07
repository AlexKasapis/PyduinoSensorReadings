import sys

import tkinter as tk
from tkinter import messagebox

import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import style
style.use('ggplot')

import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import matplotlib.animation as animation
import numpy as np
import os

from datetime import datetime


file_loc = '/LOCATION/TO/DIRECTORY/SensorReadings/'

SETTINGS = {
    # Application Info
    'WINDOW_WIDTH': -1, 'WINDOW_HEIGHT': -1, 'X_OFFSET': -1, 'Y_OFFSET': -1, 'FPS': -1, 'REFRESH_RATE': -1,
    # Sensors Info
    'ROOM_TS': -1, 'BOARD_TS': -1, 'TEMP_S': -1, 'HUMID_S': -1, 'PRESS_S': -1,
    # Precisions/Locations
    'TEMP_PRE': -1, 'TEMP_LOC': -1, 'HUMID_PRE': -1, 'HUMID_LOC': -1, 'PRESS_PRE': -1, 'PRESS_LOC': -1,
    # Live/Visible History
    'LIVE_H': -1, 'VISIBLE_H': -1, 'MAX_S': -1,
    # Danger Limits
    'TEMP_U': -1, 'TEMP_L': -1, 'HUMID_U': -1, 'HUMID_L': -1, 'PRESS_U': -1, 'PRESS_L': -1,
    # Fonts
    'AVG_F': ('Verdana', 55), 'NORM_F': ('Verdana', 10), 'ROOM_TEMP_F': ('Verdana', 20), 'THP_F': ('Verdana', 35)
}

# The modifiers for every reading. The a and b in { Y = a * X + b }
EQ_PARAMS = []

# A0 A1 A4
RT_DISPLAY = ['2', '3', '4']

# A2 A3
BT_DISPLAY = ['X', 'Y']

# PIN4
H_DISPLAY = ['1', '2']

# NO SENSORS YET
P_DISPLAY = ['1', '2', '3']

# LINE AND CHECKBOX COLORS
COLORS = [
    '#FF5005', '#0075DC', '#2BCE48', '#993F00', '#4C005C', '#808080',
    '#FFA405', '#FF0010', '#5EF1F2', '#740AFF', '#FFFF80', '#F0A3FF'
]

isPaused = False
currRoom = 'RoomMode'


def init_conf():
    with open('{}preferences.txt'.format(file_loc), 'r') as file:
        for line in file:
            line = line.rstrip('\r\n')
            line = line.rstrip('\n')
            if len(line) > 3 and line[0] is not '#':
                setting = line.split(' ')
                if setting[0] == 'WindowWidth':
                    SETTINGS['WINDOW_WIDTH'] = int(setting[1])
                elif setting[0] == 'WindowHeight':
                    SETTINGS['WINDOW_HEIGHT'] = int(setting[1])
                elif setting[0] == 'XOffset':
                    SETTINGS['X_OFFSET'] = float(setting[1])
                elif setting[0] == 'YOffset':
                    SETTINGS['Y_OFFSET'] = float(setting[1])
                elif setting[0] == 'FPS':
                    SETTINGS['FPS'] = float(setting[1])
                    SETTINGS['REFRESH_RATE'] = 1000/SETTINGS['FPS']

                elif setting[0] == 'RoomTemperatureSensors':
                    SETTINGS['ROOM_TS'] = int(setting[1])
                elif setting[0] == 'BoardTemperatureSensors':
                    SETTINGS['BOARD_TS'] = int(setting[1])
                elif setting[0] == 'TemperatureSensors':
                    SETTINGS['TEMP_S'] = int(setting[1])
                elif setting[0] == 'HumiditySensors':
                    SETTINGS['HUMID_S'] = int(setting[1])
                elif setting[0] == 'PressureSensors':
                    SETTINGS['PRESS_S'] = int(setting[1])

                elif setting[0] == 'TempPrecision':
                    SETTINGS['TEMP_PRE'] = float(setting[1])
                elif setting[0] == 'TempLocation':
                    SETTINGS['TEMP_LOC'] = float(setting[1])
                elif setting[0] == 'HumidPrecision':
                    SETTINGS['HUMID_PRE'] = float(setting[1])
                elif setting[0] == 'HumidLocation':
                    SETTINGS['HUMID_LOC'] = float(setting[1])
                elif setting[0] == 'PressPrecision':
                    SETTINGS['PRESS_PRE'] = float(setting[1])
                elif setting[0] == 'PressLocation':
                    SETTINGS['PRESS_LOC'] = float(setting[1])

                elif setting[0] == 'LiveHistory':
                    SETTINGS['LIVE_H'] = int(setting[1])
                elif setting[0] == 'VisibleHistory':
                    SETTINGS['VISIBLE_H'] = int(setting[1])
                elif setting[0] == 'MaxScroll':
                    SETTINGS['MAX_S'] = int(setting[1])

                elif setting[0] == 'TempUpperLimit':
                    SETTINGS['TEMP_U'] = float(setting[1])
                elif setting[0] == 'TempLowerLimit':
                    SETTINGS['TEMP_L'] = float(setting[1])
                elif setting[0] == 'HumidUpperLimit':
                    SETTINGS['HUMID_U'] = float(setting[1])
                elif setting[0] == 'HumidLowerLimit':
                    SETTINGS['HUMID_L'] = float(setting[1])
                elif setting[0] == 'PressUpperLimit':
                    SETTINGS['PRESS_U'] = float(setting[1])
                elif setting[0] == 'PressLowerLimit':
                    SETTINGS['PRESS_L'] = float(setting[1])

                elif setting[0] == 'NewParam':
                    EQ_PARAMS.append((setting[1], setting[2]))

        # Check if everything was configured correctly
        for key, value in SETTINGS.items():
            if value is -1:
                file.close()
                return False
        file.close()
        return True


def save_eq_params():
    print('Saving')


def grab_live_data():

    temp_l = []
    humid_l = []
    press_l = []

    while True:

        done = True

        try:
            # Get data
            temp_file = open('{}templive.bin'.format(file_loc), 'rb')
            raw_temps = np.fromfile(temp_file, dtype=np.float16)
            t1 = int(raw_temps[0])
            raw_temps2 = np.delete(raw_temps, 0)
            t2 = int(raw_temps2[0])
            temps1d = np.delete(raw_temps2, 0)
            temps2d = np.reshape(temps1d, (t1, t2))

            humid_file = open('{}humidlive.bin'.format(file_loc), 'rb')
            raw_humids = np.fromfile(humid_file, dtype=np.float16)
            h1 = int(raw_humids[0])
            raw_humids2 = np.delete(raw_humids, 0)
            h2 = int(raw_humids2[0])
            humids1d = np.delete(raw_humids2, 0)
            humids2d = np.reshape(humids1d, (h1, h2))

            press_file = open('{}presslive.bin'.format(file_loc), 'rb')
            raw_press = np.fromfile(press_file, dtype=np.float16)
            p1 = int(raw_press[0])
            raw_press2 = np.delete(raw_press, 0)
            p2 = int(raw_press2[0])
            press1d = np.delete(raw_press2, 0)
            press2d = np.reshape(press1d, (p1, p2))

            temp_l = temps2d.tolist()
            humid_l = humids2d.tolist()
            press_l = press2d.tolist()

            if not temp_l or not humid_l or not press_l:
                done = False

        except (IndexError, ValueError):
            done = False
            #print('WARNING: Could not read from the live data')

        if done:
            break

    #print(humid_l)
    return temp_l, humid_l, press_l


def get_period_num(number):
    splitted = number.split(',')
    try:
        return '{}.{}'.format(splitted[0], splitted[1])
    except IndexError:
        print('ERROR: Could not convert comma number to period number:', number)
        return ''


def popupmessage(mtype, title, text):
    if mtype is 'Error':
        messagebox.showerror(title, text)
    elif mtype is 'Info':
        messagebox.showinfo(title, text)


class SensorReadingsApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self, "Sensor Readings")

        # The container will hold everything the GUI packs
        container = tk.Frame(self)
        container.pack(side="top", fill=tk.BOTH, expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Create the menubar
        menubar = tk.Menu(container)

        # File Submenu
        filemenu = tk.Menu(menubar, tearoff=0)

        def open_log_folder():
            os.system('xdg-open {}'.format(file_loc + 'Logs/'))
        filemenu.add_command(label="Open Logs File", command=open_log_folder)
        filemenu.add_separator()

        def quit_app():
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                print('INFO: Shutting Down the Application')
                quit()
        filemenu.add_command(label="Exit", command=quit_app)
        menubar.add_cascade(label="File", menu=filemenu)

        # Options Submenu
        optionsmenu = tk.Menu(menubar, tearoff=0)

        def pause_resume():
            global isPaused
            if not isPaused:
                optionsmenu.entryconfigure(0, label='Resume')
            else:
                optionsmenu.entryconfigure(0, label='Pause')
            isPaused = not isPaused
        optionsmenu.add_command(label='Pause', command=pause_resume)

        def switch_page():
            global currRoom
            if currRoom == 'RoomMode':
                currRoom = 'BoardMode'
                optionsmenu.entryconfigure(1, label='Graph Mode')
                self.show_frame(BoardModePage)
            elif currRoom == 'BoardMode':
                currRoom = 'RoomMode'
                optionsmenu.entryconfigure(1, label='Digital Mode')
                self.show_frame(RoomModePage)
        optionsmenu.add_command(label='Board Mode', command=switch_page)

        menubar.add_cascade(label="Options", menu=optionsmenu)

        # Help Submenu
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help", command=lambda: popupmessage('Info', 'Info', 'Not supported just yet'))
        menubar.add_cascade(label="Help", menu=helpmenu)

        # Set the menubar as the menubar
        tk.Tk.config(self, menu=menubar)

        # The list containing the basic pages
        self.frames = {}

        # Create the basic pages and add them to the list
        for F in (RoomModePage, BoardModePage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.show_frame(RoomModePage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def get_room(self, room_class):
        return self.frames[room_class]


class RoomModePage(tk.Frame):
    def __init__(self, parent, controller):

        # Initialize the Frame
        tk.Frame.__init__(self, parent)

        # Top frame contains the checkbuttons, the Pause/Play button and the Board Mode button
        top_frame = tk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.BOTH)

        self.temp_cl = []
        self.humid_cl = []
        self.press_cl = []

        def customize_checkbuttons():

            # Create the temperature checkbuttons
            temp_layer = tk.Frame(top_frame)
            temp_layer.grid(row=0, column=0, sticky=tk.W)

            tk.Label(temp_layer, text="T: ", width=2).pack(side=tk.LEFT)
            for sensor in range(SETTINGS['ROOM_TS']):
                cb = tk.Checkbutton(temp_layer, text='{}'.format(RT_DISPLAY[sensor]))
                var = tk.IntVar()
                cb.config(variable=var, relief=tk.GROOVE, bg=COLORS[sensor])
                cb.select()
                cb.pack(side=tk.LEFT)
                self.temp_cl.append(var)
            for sensor in range(SETTINGS['BOARD_TS']):
                cb = tk.Checkbutton(temp_layer, text='{}'.format(BT_DISPLAY[sensor]), relief=tk.GROOVE)
                var = tk.IntVar()
                cb.config(variable=var, relief=tk.GROOVE, bg=COLORS[SETTINGS['ROOM_TS']+sensor])
                cb.select()
                cb.pack(side=tk.LEFT)
                self.temp_cl.append(var)

            # Create the humidity checkbuttons
            humid_layer = tk.Frame(top_frame)
            humid_layer.grid(row=1, column=0, sticky=tk.W)

            tk.Label(humid_layer, text="H: ", width=2).pack(side=tk.LEFT)
            for sensor in range(SETTINGS['HUMID_S']):
                cb = tk.Checkbutton(humid_layer, text='{}'.format(H_DISPLAY[sensor]), relief=tk.GROOVE)
                var = tk.IntVar()
                cb.config(variable=var, relief=tk.GROOVE, bg=COLORS[sensor])
                cb.select()
                cb.pack(side=tk.LEFT)
                self.humid_cl.append(var)

            # Create the pressure checkbuttons
            press_layer = tk.Frame(top_frame)
            press_layer.grid(row=2, column=0, sticky=tk.W)

            tk.Label(press_layer, text="P: ", width=2).pack(side=tk.LEFT)
            for sensor in range(SETTINGS['PRESS_S']):
                cb = tk.Checkbutton(press_layer, text='{}'.format(P_DISPLAY[sensor]), relief=tk.GROOVE)
                var = tk.IntVar()
                cb.config(variable=var, relief=tk.GROOVE, bg=COLORS[sensor])
                cb.select()
                cb.pack(side=tk.LEFT)
                self.press_cl.append(var)
        customize_checkbuttons()

        # Separator
        separator_f = tk.Frame(self, height=1, bg='black')
        separator_f.pack(side=tk.TOP, fill=tk.X)

        graph_frame = tk.Frame(self, bg='blue')
        graph_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        figure_frame = tk.Frame(graph_frame)
        figure_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        layers_frame = tk.Frame(figure_frame)
        layers_frame.pack(side=tk.TOP, fill=tk.X)

        sliders_frame = tk.Frame(figure_frame, bg='white')
        sliders_frame.config(width=50)
        sliders_frame.pack(side=tk.LEFT, fill=tk.BOTH)

        def make_update(x):
            self.update_xticks = True

        t_prec_label = tk.Label(sliders_frame, text="T Prec", bg='white')
        t_prec_label.grid(row=0, column=0)
        self.temp_p_scroll = tk.Scale(sliders_frame)
        self.temp_p_scroll.config(resolution=0.05, from_=2, to=0.05, length=205, bg='white', command=make_update)
        self.temp_p_scroll.set(SETTINGS['TEMP_PRE'])
        self.temp_p_scroll.grid(row=1, column=0)

        t_loc_label = tk.Label(sliders_frame, text="T Loc", bg='white')
        t_loc_label.grid(row=0, column=1)
        self.temp_l_scroll = tk.Scale(sliders_frame)
        self.temp_l_scroll.config(resolution=1, from_=40, to=10, length=205, bg='white', command=make_update)
        self.temp_l_scroll.set(SETTINGS['TEMP_LOC'])
        self.temp_l_scroll.grid(row=1, column=1)

        h_prec_label = tk.Label(sliders_frame, text="H Prec", bg='white')
        h_prec_label.grid(row=2, column=0)
        self.humid_p_scroll = tk.Scale(sliders_frame)
        self.humid_p_scroll.config(resolution=0.05, from_=2, to=0.05, length=205, bg='white', command=make_update)
        self.humid_p_scroll.set(SETTINGS['HUMID_PRE'])
        self.humid_p_scroll.grid(row=3, column=0)

        h_loc_label = tk.Label(sliders_frame, text="H Loc", bg='white')
        h_loc_label.grid(row=2, column=1)
        self.humid_l_scroll = tk.Scale(sliders_frame)
        self.humid_l_scroll.config(resolution=1, from_=60, to=10, length=205, bg='white', command=make_update)
        self.humid_l_scroll.set(SETTINGS['HUMID_LOC'])
        self.humid_l_scroll.grid(row=3, column=1)

        p_prec_label = tk.Label(sliders_frame, text="P Prec", bg='white')
        p_prec_label.grid(row=5, column=0)
        self.press_p_scroll = tk.Scale(sliders_frame)
        self.press_p_scroll.config(resolution=0.01, from_=0.1, to=0.01, length=205, bg='white', command=make_update)
        self.press_p_scroll.set(SETTINGS['PRESS_PRE'])
        self.press_p_scroll.grid(row=6, column=0)

        p_loc_label = tk.Label(sliders_frame, text="P Loc", bg='white')
        p_loc_label.grid(row=5, column=1)
        self.press_l_scroll = tk.Scale(sliders_frame)
        self.press_l_scroll.config(resolution=0.01, from_=1.5, to=0.5, length=205, bg='white', command=make_update)
        self.press_l_scroll.set(SETTINGS['PRESS_LOC'])
        self.press_l_scroll.grid(row=6, column=1)

        canvas_frame = tk.Frame(figure_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.figure, self.graphs = plt.subplots(nrows=3)
        plt.subplots_adjust(left=0.11, bottom=0.05, right=0.94, top=0.97, wspace=0, hspace=0.2)

        self.canvas = FigureCanvasTkAgg(self.figure, canvas_frame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        def customize_graphs():
            self.graphs[0].set_ylabel(r"Temperature (C)", size=14)
            self.graphs[1].set_ylabel(r"Humidity (%)", size=14)
            self.graphs[2].set_ylabel(r"Pressure (bar)", size=14)
            self.graphs[0].axis([0, SETTINGS['VISIBLE_H'] - 1, SETTINGS['TEMP_LOC'] - 5 * SETTINGS['TEMP_PRE'],
                                 SETTINGS['TEMP_LOC'] + 5 * SETTINGS['TEMP_PRE']])
            self.graphs[1].axis([0, SETTINGS['VISIBLE_H'] - 1, SETTINGS['HUMID_LOC'] - 5 * SETTINGS['HUMID_PRE'],
                                 SETTINGS['HUMID_LOC'] + 5 * SETTINGS['HUMID_PRE']])
            self.graphs[2].axis([0, SETTINGS['VISIBLE_H'] - 1, SETTINGS['PRESS_LOC'] - 5 * SETTINGS['PRESS_PRE'],
                                 SETTINGS['PRESS_LOC'] + 5 * SETTINGS['PRESS_PRE']])
            for graph in self.graphs:
                # Disable the top ticks of every Axes instance
                graph.tick_params(axis="x", which="both", top="off")
                # Enable the right tick labels, as is defaulted to False
                graph.tick_params(labelright=True)
                graph.xaxis.set_major_locator(plticker.MultipleLocator(base=1))
                graph.yaxis.set_major_locator(plticker.MultipleLocator(base=1))
                graph.grid(which="major", axis="both", linestyle="-")
                graph.get_yaxis().set_label_coords(-0.08, 0.5)
            self.graphs[2].yaxis.set_major_locator(plticker.MultipleLocator(base=0.05))
        customize_graphs()

        self.pos = SETTINGS['MAX_S']

        self.update_xticks = False

        self.time_scroll_frame = tk.Scale(canvas_frame)
        self.time_scroll_frame.config(orient=tk.HORIZONTAL, resolution=1, from_=0, to=SETTINGS['MAX_S'], bg='white',
                                      command=make_update)
        self.time_scroll_frame.set(SETTINGS['MAX_S'])
        self.time_scroll_frame.pack(side=tk.TOP, fill=tk.X)
        time_label = tk.Label(canvas_frame, text='Time', bg='white')
        time_label.pack(side=tk.TOP, fill=tk.X)

        # This list will contain the labels for the time axis
        # +1 cause it seems that the first element in the list is being ignored
        self.times = ['' for _ in range(SETTINGS['LIVE_H'] + 1)]
        # Every time the counter loops back to 0, a new time tick will be inserted into the list.
        # Else, an empty string will be inserted in the list.
        self.t_ctr = 0
        self.t_ctr_max = 5

        def plot(graph, i):
            return graph.plot(0, 0, animated=True, color=COLORS[i])[0]

        self.temp_lines = [plot(self.graphs[0], i) for i in range(SETTINGS['TEMP_S'])]
        self.humid_lines = [plot(self.graphs[1], i) for i in range(SETTINGS['HUMID_S'])]
        self.press_lines = [plot(self.graphs[2], i) for i in range(SETTINGS['PRESS_S'])]

        # Separator
        self.separator_f2 = tk.Frame(graph_frame, width=2, bg='black')
        self.separator_f2.pack(side=tk.LEFT, fill=tk.Y)

        '''AVERAGES'''
        self.avg_frame = tk.Frame(graph_frame, padx=5, bg="white")
        self.avg_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        self.avg_labels_list = []
        for i in range(3):
            avg_frame = tk.Frame(self.avg_frame, bg="white", padx=20)
            avg_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
            avg_label = tk.Label(avg_frame)
            avg_label.config(padx=5, relief=tk.RAISED, fg="#1F5B97", bg="white", font=SETTINGS['AVG_F'])
            avg_label.pack()
            self.avg_labels_list.append(avg_label)

        self.temp_data = []
        self.humid_data = []
        self.press_data = []

    def animate(self, i):

        self.pos = self.time_scroll_frame.get()
        t_precision = self.temp_p_scroll.get()
        t_location = self.temp_l_scroll.get()
        h_precision = self.humid_p_scroll.get()
        h_location = self.humid_l_scroll.get()
        p_precision = self.press_p_scroll.get()
        p_location = self.press_l_scroll.get()
        self.graphs[0].set_ylim([t_location-5*t_precision, t_location+5*t_precision])
        self.graphs[1].set_ylim([h_location-5*h_precision, h_location+5*h_precision])
        self.graphs[2].set_ylim([p_location-5*p_precision, p_location+5*p_precision])

        prev_data = self.temp_data[-2:]
        self.temp_data, self.humid_data, self.press_data = grab_live_data()
        curr_data = self.temp_data[-2:]
        # If we get a new set of data
        if self.update_xticks:
            for graph in self.graphs:
                graph.set_xticklabels(self.times[self.pos:self.pos+SETTINGS['VISIBLE_H']])
        if prev_data != curr_data:
            self.update_xticks = True
            # Bring the labels one position left
            for i in range(len(self.times)-1):
                self.times[i] = self.times[i+1]
            if self.t_ctr == 0:
                # Add the current time in the last position of the list
                hour = datetime.now().strftime('%H:%M:%S.%f')[0:2]
                min = datetime.now().strftime('%H:%M:%S.%f')[3:5]
                sec = datetime.now().strftime('%H:%M:%S.%f')[6:8]
                string = hour+':'+min+':'+sec
            else:
                string = ''
            self.t_ctr += 1
            if self.t_ctr >= self.t_ctr_max:
                self.t_ctr = 0
            self.times[-1] = string

        # Update the graph only if the state is not paused
        global isPaused
        if not isPaused:
            # Update the time tick labels
            for graph in self.graphs:
                graph.set_xticklabels(self.times[self.pos + 1:self.pos + SETTINGS['VISIBLE_H'] + 2])

            ''' ANIMATE THE GRAPH '''
            def get_y_data(raw_values, mult):
                filler = [-1 for _ in range(SETTINGS['LIVE_H'] - len(raw_values))]
                values = []
                for j in range(len(raw_values)):
                    values.append(raw_values[j][0])
                values = filler + values
                values = values[self.pos:self.pos + SETTINGS['VISIBLE_H']]
                y_data = []
                for value in values:
                    if value != -1:
                        y_data.append(value * mult)
                x_data = [SETTINGS['VISIBLE_H'] - 1 - i for i in range(len(y_data))]
                return list(reversed(y_data)), x_data

            for i in range(len(self.temp_lines)):
                if len(self.temp_lines) is 1:
                    temp_values = self.temp_data
                else:
                    temp_values = [[self.temp_data[temp_i][i]] for temp_i in range(len(self.temp_data))]
                y_data, x_data = get_y_data(temp_values, self.temp_cl[i].get())
                self.temp_lines[i].set_ydata(y_data)
                self.temp_lines[i].set_xdata(x_data)

            for i in range(len(self.humid_lines)):
                if len(self.humid_lines) is 1:
                    humid_values = self.humid_data
                else:
                    humid_values = [[self.humid_data[humid_i][i]] for humid_i in range(len(self.humid_data))]
                y_data, x_data = get_y_data(humid_values, self.humid_cl[i].get())
                self.humid_lines[i].set_ydata(y_data)
                self.humid_lines[i].set_xdata(x_data)

            for i in range(len(self.press_lines)):
                if len(self.press_lines) is 1:
                    press_values = self.press_data
                else:
                    press_values = [[self.press_data[press_i][i]] for press_i in range(len(self.press_data))]
                y_data, x_data = get_y_data(press_values, self.press_cl[i].get())
                self.press_lines[i].set_ydata(y_data)
                self.press_lines[i].set_xdata(x_data)

            ''' ANIMATE THE AVERAGE LABELS '''
            try:
                if self.temp_data[-1]:
                    temp_tuple = []
                    for i in range(len(self.temp_data[-1])):
                        if self.temp_cl[i].get() > 0:
                            temp_tuple.append(self.temp_data[-1][i])
                else:
                    temp_tuple = 0

                if self.humid_data[-1]:
                    humid_tuple = []
                    for i in range(len(self.humid_data[-1])):
                        if self.humid_cl[i].get() > 0:
                            humid_tuple.append(self.humid_data[-1][i])
                else:
                    humid_tuple = 0

                if self.press_data[-1]:
                    press_tuple = []
                    for i in range(len(self.press_data[-1])):
                        if self.press_cl[i].get() > 0:
                            press_tuple.append(self.press_data[-1][i])
                else:
                    press_tuple = 0

                if temp_tuple != 0 and len(temp_tuple) != 0:
                    average_temp = sum(temp_tuple) / len(temp_tuple)
                else:
                    average_temp = -1

                if humid_tuple != 0 and len(humid_tuple) != 0:
                    average_humid = sum(humid_tuple) / len(humid_tuple)
                else:
                    average_humid = -1

                if press_tuple != 0 and len(press_tuple) != 0:
                    average_press = sum(press_tuple) / len(press_tuple)
                else:
                    average_press = -1

                if average_temp == -1:
                    self.avg_labels_list[0].config(bg="white")
                elif average_temp > SETTINGS['TEMP_U'] or average_temp < SETTINGS['TEMP_L']:
                    self.avg_labels_list[0].config(bg="red")
                else:
                    self.avg_labels_list[0].config(bg="white")
                if average_temp != -1:
                    self.avg_labels_list[0].config(text="{:.1f} °C".format(average_temp))
                else:
                    self.avg_labels_list[0].config(text="- °C")

                if average_humid == -1:
                    self.avg_labels_list[1].config(bg="white")
                elif average_humid > SETTINGS['HUMID_U'] or average_humid < SETTINGS['HUMID_L']:
                    self.avg_labels_list[1].config(bg="red")
                else:
                    self.avg_labels_list[1].config(bg="white")
                if average_humid != -1:
                    self.avg_labels_list[1].config(text="{:.1f} %".format(average_humid))
                else:
                    self.avg_labels_list[1].config(text="- %")

                if average_press == -1:
                    self.avg_labels_list[2].config(bg="white")
                elif average_press > SETTINGS['PRESS_U'] or average_press < SETTINGS['PRESS_L']:
                    self.avg_labels_list[2].config(bg="red")
                else:
                    self.avg_labels_list[2].config(bg="white")
                if average_press != -1:
                    self.avg_labels_list[2].config(text="{:.2f} bar".format(average_press))
                else:
                    self.avg_labels_list[2].config(text="- bar")

            except (TypeError, IndexError):
                print('WARNING: Could not calculate average labels', self.press_data)

                self.avg_labels_list[0].config(bg="red")
                self.avg_labels_list[0].config(text="??.? °C")

                self.avg_labels_list[1].config(bg="red")
                self.avg_labels_list[1].config(text="??.? %")

                self.avg_labels_list[2].config(bg="red")
                self.avg_labels_list[2].config(text="?.?? bar")

        if self.update_xticks:
            self.canvas.draw()
            #self.canvas.draw()
            # for i in range(len(self.graphs)):
            #     self.figure.canvas.restore_region(self.graph_bgs[i])
            #     self.graphs[i].draw_artist(self.graphs[i])
            #     self.figure.canvas.blit(self.graphs[i].bbox)
            self.update_xticks = False

        return self.temp_lines + self.humid_lines + self.press_lines


class BoardModePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        # The room temp indicators
        room_temps_frame = tk.Frame(self, pady=20)
        room_temps_frame.pack(side=tk.TOP, fill=tk.X)

        rtop_frame = tk.Frame(room_temps_frame, pady=5)
        rtop_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
        rbot_frame = tk.Frame(room_temps_frame, pady=5)
        rbot_frame.pack(side=tk.TOP, fill=tk.X, expand=True)

        self.room_temp_labels_list = []
        for i in range(SETTINGS['ROOM_TS']):
            if i < SETTINGS['ROOM_TS'] / 2:
                room_temp_frame = tk.Frame(rtop_frame)
            else:
                room_temp_frame = tk.Frame(rbot_frame)
            room_temp_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            room_temp_label = tk.Label(room_temp_frame)
            room_temp_label.config(padx=5, height=2, relief=tk.RAISED, fg="#1F5B97", bg="white",
                                   font=SETTINGS['ROOM_TEMP_F'])
            room_temp_label.pack()

            self.room_temp_labels_list.append(room_temp_label)

        # Separator
        self.separator_f_1 = tk.Frame(self, height=2, bg='black')
        self.separator_f_1.pack(side=tk.TOP, fill=tk.X)

        # Humid and pressures indicators
        self.h_p_frame = tk.Frame(self, pady=20)
        self.h_p_frame.pack(side=tk.TOP, fill=tk.X)

        self.humid_labels_list = []
        for i in range(SETTINGS['HUMID_S']):
            humid_frame = tk.Frame(self.h_p_frame)
            humid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            humid_label = tk.Label(humid_frame)
            humid_label.config(padx=10, height=2, relief=tk.RAISED, fg="#1F5B97", bg="white", font=SETTINGS['THP_F'])
            humid_label.pack()

            self.humid_labels_list.append(humid_label)

        self.press_labels_list = []
        for i in range(SETTINGS['PRESS_S']):
            press_frame = tk.Frame(self.h_p_frame)
            press_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            press_label = tk.Label(press_frame)
            press_label.config(padx=10, height=2, relief=tk.RAISED, fg="#1F5B97", bg="white", font=SETTINGS['THP_F'])
            press_label.pack()

            self.press_labels_list.append(press_label)

        # Separator 2
        self.separator_f_2 = tk.Frame(self, height=2, bg='black')
        self.separator_f_2.pack(side=tk.TOP, fill=tk.X)

        # The board sensors indicators
        self.board_frame = tk.Frame(self)
        self.board_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.btop_frame = tk.Frame(self.board_frame)
        self.btop_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.bbot_frame = tk.Frame(self.board_frame)
        self.bbot_frame.pack(side=tk.TOP, fill=tk.X, expand=True)

        self.board_temp_labels_list = []
        for i in range(SETTINGS['BOARD_TS']):
            if i < SETTINGS['BOARD_TS']/2:
                board_frame = tk.Frame(self.btop_frame)
            else:
                board_frame = tk.Frame(self.bbot_frame)
            board_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            board_label = tk.Label(board_frame)
            board_label.config(padx=10, height=2, relief=tk.RAISED, fg="#1F5B97", bg="white", font=SETTINGS['THP_F'])
            board_label.pack()

            self.board_temp_labels_list.append(board_label)

        self.update_labels()

    def update_labels(self):
        try:
            temp_data_l, humid_data_l, press_data_l = grab_live_data()
            #if temp_data_l:
            temp_data = temp_data_l[-1]
            #else:
            #    temp_data = []

            #if humid_data_l:
            humid_data = humid_data_l[-1]
            #else:
            #    humid_data = []

            #if press_data_l:
            press_data = press_data_l[-1]
            #else:
            #    press_data = []

            # Update the Room Temp Sensors Indicators
            for i in range(len(self.room_temp_labels_list)):
                temp = temp_data[i]
                self.room_temp_labels_list[i].config(text='{}: {:.2f}°C'.format(RT_DISPLAY[i], temp))
                if float(temp) > SETTINGS['TEMP_U'] or float(temp) < SETTINGS['TEMP_L']:
                    self.room_temp_labels_list[i].config(bg="red")
                else:
                    self.room_temp_labels_list[i].config(bg="white")

            # Update the Humidity Sensors Indicators
            for i in range(len(self.humid_labels_list)):
                humid = humid_data[i]
                self.humid_labels_list[i].config(text='Humidity {}: {:.2f}%'.format(H_DISPLAY[i], humid))
                if float(humid) > SETTINGS['HUMID_U'] or float(humid) < SETTINGS['HUMID_L']:
                    self.humid_labels_list[i].config(bg="red")
                else:
                    self.humid_labels_list[i].config(bg="white")

            # Update the Pressure Sensors Indicators
            for i in range(len(self.press_labels_list)):
                press = press_data[i]
                self.press_labels_list[i].config(text='Pressure {}: {:.2f}bar'.format(P_DISPLAY[i], press))
                if float(press) > SETTINGS['PRESS_U'] or float(press) < SETTINGS['PRESS_L']:
                    self.press_labels_list[i].config(bg="red")
                else:
                    self.press_labels_list[i].config(bg="white")

            # Update the Board Temp Sensors Indicators
            for i in range(len(self.board_temp_labels_list)):
                temp = temp_data[SETTINGS['BOARD_TS'] + i]
                self.board_temp_labels_list[i].config(text='{}: {:.2f}°C'.format(BT_DISPLAY[i], temp))
                if float(temp) > SETTINGS['TEMP_U'] or float(temp) < SETTINGS['TEMP_L']:
                    self.board_temp_labels_list[i].config(bg="red")
                else:
                    self.board_temp_labels_list[i].config(bg="white")

        except IndexError:
            print('IndexError')

        # Loop the function to run every 'REFRESH_RATE' ms
        self.after(int(SETTINGS['REFRESH_RATE']), self.update_labels)


# Start a new thread for the data pull background process
if __name__ == "__main__":

    print('INFO: Loading settings')
    if not init_conf():
        print('ERROR: Could not run the configuration. Exiting.')
        sys.exit()

    # Create the main window
    app = SensorReadingsApp()

    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            print('INFO: Shutting Down the Application')
            app.quit()
    app.protocol('WM_DELETE_WINDOW', on_closing)

    app.geometry('%dx%d+%d+%d' % (SETTINGS['WINDOW_WIDTH'], SETTINGS['WINDOW_HEIGHT'],
                                  SETTINGS['X_OFFSET'], SETTINGS['Y_OFFSET']))

    app.resizable(False, False)

    ani = animation.FuncAnimation(app.get_room(RoomModePage).figure, app.get_room(RoomModePage).animate, range(1, 200),
                                  interval=SETTINGS['REFRESH_RATE'], blit=True)

    print('INFO: Starting Application Mainloop')
    app.mainloop()
