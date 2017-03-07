#!/usr/bin/env/python3
"""
Handles input data from the Arduino board, creates Logs and saves the live data in binary files.

The Arduino board is constantly outputting the readings. After establishing a stable connection with the board, this
program reads the data through the serial port, splits it and categorizes into Temperatures, Humidities and Pressures,
and finally appends these new readings in the Log file and in the live data binary files.
"""
import os
import time
from datetime import datetime
import numpy as np
import serial
import glob
import random

__author__ = "Alex Apostolos Kasapis"
__license__ = "GPLv2"
__maintainer__ = "Alex Apostolos Kasapis"
__email__ = "apkasapis@gmail.com"
__status__ = "Production"

# Directory pointing to the location of the folder where the Log folder and the live binary files will be created.
file_loc = '/media/alex/Storage/Projects/CERNuino/SensorReadings/'

SETTINGS = {
    # Sensor Quantity
    'TEMP_S': -1, 'HUMID_S': -1, 'PRESS_S': -1,
    # Readings danger limits
    'TEMP_UPPER': -1, 'TEMP_LOWER': -1, 'HUMID_UPPER': -1, 'HUMID_LOWER': -1, 'PRESS_UPPER': -1, 'PRESS_LOWER': -1,
    # Info regarding the graph
    'LIVE_H': -1
}

# Every input can be modified using two parameters, which are the A and B in "Y = A * X + B"
EQ_PARAMS = []

# The temp list will be storing the live data. Every new set of data will be appended to the end of each list, with the
# oldest elements deleted. These lists will be written to binary files in order for the GUI to read them.
temp_list = []
humid_list = []
press_list = []


def init_conf():
    """
    Open the text file containing the preferences and apply any settings.
    Every line is a possible new setting.
    Lines starting with # are being ignored. Lines with zero length are being ignored.
    Changes the values of the SETTINGS dictionary entries.
    """
    with open(file_loc + 'preferences.txt', 'r') as file:
        for line in file:
            line = line.rstrip('\r\n')
            line = line.rstrip('\n')
            if len(line) > 0 and line[0] is not '#':
                setting = line.split(' ')
                if setting[0] == 'TemperatureSensors':
                    SETTINGS['TEMP_S'] = int(setting[1])
                elif setting[0] == 'HumiditySensors':
                    SETTINGS['HUMID_S'] = int(setting[1])
                elif setting[0] == 'PressureSensors':
                    SETTINGS['PRESS_S'] = int(setting[1])
                elif setting[0] == 'TempUpperLimit':
                    SETTINGS['TEMP_UPPER'] = float(setting[1])
                elif setting[0] == 'TempLowerLimit':
                    SETTINGS['TEMP_LOWER'] = float(setting[1])
                elif setting[0] == 'HumidUpperLimit':
                    SETTINGS['HUMID_UPPER'] = float(setting[1])
                elif setting[0] == 'HumidLowerLimit':
                    SETTINGS['HUMID_LOWER'] = float(setting[1])
                elif setting[0] == 'PressUpperLimit':
                    SETTINGS['PRESS_UPPER'] = float(setting[1])
                elif setting[0] == 'PressLowerLimit':
                    SETTINGS['PRESS_LOWER'] = float(setting[1])
                elif setting[0] == 'LiveHistory':
                    SETTINGS['LIVE_H'] = float(setting[1])
                elif setting[0] == 'NewParam':
                    EQ_PARAMS.append((setting[1], setting[2]))


def modify_output(value, index):
    """
    Calculate the modified value of an input number based on the two parameters of the EQ_PARAMS list.
    :param value: The input value to be modified.
    :param index: The index pointing to the parameters in the EQ_PARAMS to be used for the modification.
    :return: The modified value of the input number.
    """
    number = float(value)
    a = int(EQ_PARAMS[index][0])
    b = int(EQ_PARAMS[index][1])
    number = a * number + b
    return str(number)


def get_comma_num(number):
    """
    Due to localization, some times the log files need to be filled with floats where the, point is a comma. So
    this function converts a float number to a string representing this number, where the floating point is a comma.
    :param number: The float number.
    :return: The string representing the input number, seperated by a comma instead of a period.
    """
    string_num = str(float(number))
    splitted = string_num.split('.')
    try:
        return '{},{}'.format(splitted[0], splitted[1])
    except IndexError:
        print('ERROR: Float number not valid {}'.format(number))
        return ''


def get_period_num(number):
    """
    Convert a number where the floating point is a comma, to a one where it is a period. (See above function)
    :param number: The string number.
    :return: The converted number where the floating point is a period.
    """
    splitted = number.split(',')
    try:
        return '{}.{}'.format(splitted[0], splitted[1])
    except IndexError:
        print('ERROR: Float string number not valid {}'.format(number))
        return ''


# Write the data string to the logs
def update_logs(data_str, danger):
    # Get the date
    date = datetime.now()

    # Create the folder where the log file will be saved
    if not os.path.isdir(file_loc + 'Logs'):
        os.makedirs(file_loc + 'Logs')

    if not os.path.isdir(file_loc + 'Logs/Errors'):
        os.makedirs(file_loc + 'Logs/Errors')

    # Create the path string to the file
    file_path = file_loc + 'Logs/{}-{}-{}.doc'.format(date.day, date.month, date.year)
    error_file_path = file_loc + 'Logs/Errors/ErrorLogs.doc'

    # Output to the file
    output_string = '{}-{}-{}-{}\t{}\n'.format(date.day, date.month, date.year, date.time(), data_str)
    text_file = open(file_path, 'a')
    text_file.write(output_string)
    text_file.close()

    # If the danger parameter is True, output to another file
    if danger:
        error_file = open(error_file_path, 'a')
        error_file.write(output_string)
        error_file.close()


# Update the binary live data files
def update_live_data():

    tl = np.array(temp_list, np.float16)
    tl = np.insert(tl, 0, [len(temp_list), len(temp_list[0])])

    hl = np.array(humid_list, np.float16)
    hl = np.insert(hl, 0, [len(humid_list), len(humid_list[0])])

    pl = np.array(press_list, np.float16)
    pl = np.insert(pl, 0, [len(press_list), len(press_list[0])])

    tl.astype('float16').tofile(file_loc + 'templive.bin')
    hl.astype('float16').tofile(file_loc + 'humidlive.bin')
    pl.astype('float16').tofile(file_loc + 'presslive.bin')


def mainloop(port):
    while True:
        # Read the raw data from the serial port
        raw_data = str(port.readline())
        raw_data = raw_data[2:-5]
        # print(raw_data)

        # Parse the raw string get the readings
        raw_list = raw_data.split()

        temps_string = ''
        humid_string = ''
        press_string = ''
        for i in range(len(raw_list)):
            if i < SETTINGS['TEMP_S']:
                num = modify_output(raw_list[i], i)
                temps_string += '{} '.format(str(num))
            elif i < SETTINGS['TEMP_S'] + SETTINGS['HUMID_S']:
                num = modify_output(raw_list[i], i)
                humid_string += '{} '.format(str(num))
            elif i < SETTINGS['TEMP_S'] + SETTINGS['HUMID_S'] + SETTINGS['PRESS_S']:
                num = modify_output(raw_list[i], i)
                press_string += '{} '.format(str(num))

        # Split the strings into lists
        t_list_str = [get_comma_num(temp) for temp in temps_string.split()]
        h_list_str = [get_comma_num(humid) for humid in humid_string.split()]
        p_list_str = [get_comma_num(press) for press in press_string.split()]
        #print(t_list_str, '+', h_list_str, '+', p_list_str)

        error = False
        for value in t_list_str:
            num_value = float(get_period_num(value))
            if num_value > SETTINGS['TEMP_UPPER'] or num_value < SETTINGS['TEMP_LOWER']:
                error = True
        for value in h_list_str:
            num_value = float(get_period_num(value))
            if num_value > SETTINGS['HUMID_UPPER'] or num_value < SETTINGS['HUMID_LOWER']:
                error = True
        for value in p_list_str:
            num_value = float(get_period_num(value))
            if num_value > SETTINGS['PRESS_UPPER'] or num_value < SETTINGS['PRESS_LOWER']:
                error = True

        # Update the logs
        update_logs('\t'.join(t_list_str + h_list_str + p_list_str), error)

        # Update the list
        if len(temp_list) >= SETTINGS['LIVE_H']:
            del temp_list[0]
            del humid_list[0]
            del press_list[0]
        temp_list.append(temps_string.split())

        #print(t_list_str)
        #print(temp_list[-1])
        
        humid_list.append(humid_string.split())
        press_list.append(press_string.split())

        update_live_data()

        time.sleep(2)


# Handle the initialization of the program
# Load the settings
# Search and connect to the Arduino
# Wait until the connection is stable
# Start the mainloop
def init_process():

    # Init the settings based on a txt file.
    print('INFO: Loading settings')
    init_conf()

    # Get the port connected to the pi
    # Get the first element of the array returned (multiple arduinos connected via usb?)
    print('INFO: Searching for connected Arduinos')
    port = glob.glob('/dev/ttyACM*')[0]
    print('INFO: Arduino board found in port {}'.format(port))

    # Connect to the serial port
    ard_serial = serial.Serial(port, 9600)
    print('INFO: Connected to port {}'.format(port))

    # Wait until the port is stable
    # When connecting to the port, the first batch of data read might be corrupted
    # Loop until the input data is as expected
    print('INFO: Waiting for port to output stable data')
    while True:
        data_string = str(ard_serial.readline())
        print('INFO: Input string {}'.format(data_string))
         
        if len(data_string) == 7+(SETTINGS['TEMP_S']+SETTINGS['HUMID_S']+SETTINGS['PRESS_S'])*6:
            print('INFO: String is valid')
            break
        else:
            print('WARNING: Expected string has length {}, input string has length {}'
                  .format(7 + (SETTINGS['TEMP_S'] + SETTINGS['HUMID_S'] + SETTINGS['PRESS_S']) * 6, len(data_string)))
    print('INFO: Port {} is stable'.format(port))

    # Clear any binary files left from the previous execution
    print('INFO: Clearing live data files')
    temp_file = open(file_loc + 'templive.bin', 'wb')
    temp_file.close()
    humid_file = open(file_loc + 'humidlive.bin', 'wb')
    humid_file.close()
    press_file = open(file_loc + 'presslive.bin', 'wb')
    press_file.close()

    # Start the mainloop
    print('INFO: Starting background mainloop')
    mainloop(ard_serial)


def fake_nums(f, t, n):
    return ''.join('{:.2f} '.format(random.uniform(f, t)) for _ in range(n))[:-1]


def fake_mainloop():
    while True:
        # Get the strings like the Arduino would output
        temps_string = fake_nums(f=16.0, t=18.0, n=SETTINGS['TEMP_S'])
        humid_string = fake_nums(f=22.0, t=24.0, n=SETTINGS['HUMID_S'])
        press_string = fake_nums(f=0.90, t=1.10, n=SETTINGS['PRESS_S'])

        # Modify the output
        tmp = temps_string.split()
        for i in range(len(tmp)):
            tmp[i] = modify_output(tmp[i], i)
        temps_string = (' '.join(tmp))

        tmp = humid_string.split()
        for i in range(len(tmp)):
            tmp[i] = modify_output(tmp[i], SETTINGS['TEMP_S'] + i)
        humid_string = (' '.join(tmp))

        tmp = press_string.split()
        for i in range(len(tmp)):
            tmp[i] = modify_output(tmp[i], SETTINGS['TEMP_S'] + SETTINGS['HUMID_S'] + i)
        press_string = (' '.join(tmp))

        # Split the strings into lists
        t_list_str = [get_comma_num(temp) for temp in temps_string.split()]
        h_list_str = [get_comma_num(humid) for humid in humid_string.split()]
        p_list_str = [get_comma_num(press) for press in press_string.split()]

        error = False
        for value in t_list_str:
            num_value = float(get_period_num(value))
            if num_value > SETTINGS['TEMP_UPPER'] or num_value < SETTINGS['TEMP_LOWER']:
                error = True
        for value in h_list_str:
            num_value = float(get_period_num(value))
            if num_value > SETTINGS['HUMID_UPPER'] or num_value < SETTINGS['HUMID_LOWER']:
                error = True
        for value in p_list_str:
            num_value = float(get_period_num(value))
            if num_value > SETTINGS['PRESS_UPPER'] or num_value < SETTINGS['PRESS_LOWER']:
                error = True

        # Update the logs
        update_logs('\t'.join(t_list_str + h_list_str + p_list_str), error)

        # Update the list
        if len(temp_list) >= SETTINGS['LIVE_H']:
            del temp_list[0]
            del humid_list[0]
            del press_list[0]
        temp_list.append(temps_string.split())
        humid_list.append(humid_string.split())
        press_list.append(press_string.split())

        update_live_data()

        time.sleep(2)


def init_fake():
    print('INFO: Loading settings')
    init_conf()

    print('INFO: Clearing live data files')
    temp_file = open(file_loc + 'templive.bin', 'wb')
    temp_file.close()
    humid_file = open(file_loc + 'humidlive.bin', 'wb')
    humid_file.close()
    press_file = open(file_loc + 'presslive.bin', 'wb')
    press_file.close()

    print('INFO: Starting background mainloop')
    fake_mainloop()


if __name__ == '__main__':
    #init_process()
    init_fake()
