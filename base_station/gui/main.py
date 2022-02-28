""" This class manages the GUI framework for the base_station
user-interface using the built-in python Tkinter user-interface. """

# System imports
import sys
import os
import datetime

# Begin custom imports
import tkinter
from tkinter import Tk
from tkinter import Button
from tkinter import Frame
from tkinter import Label
from tkinter import Text
from tkinter import Entry
from tkinter import PhotoImage
from tkinter import Scrollbar
from tkinter import Toplevel
from tkinter import StringVar
from tkinter import BOTH, TOP, BOTTOM, LEFT, RIGHT, YES, NO, SUNKEN, X, Y, W, E, N, S, DISABLED, NORMAL, END
from tkinter import messagebox
from tkinter import constants
from tkinter.ttk import Combobox
from tkinter import font

from static import constants
from .map import Map
from screeninfo import get_monitors, Enumerator

# Begin Constants
WIDTH = 1400
HEIGHT = 800
# Refresh time
REFRESH_TIME = 500
# Development resolution constraints (used for proper screen scaling)
DEV_WIDTH = 1920.0
DEV_HEIGHT = 1200.0
# Frame heights
TOP_FRAME_HEIGHT = 550
BOT_FRAME_HEIGHT = 30
# Panel Constants
FUNC_FRAME_WIDTH = 250
STATUS_FRAME_WIDTH = 350
CALIBRATE_FRAME_WIDTH = 350
MISSION_FRAME_WIDTH = 300
LOG_FRAME_WIDTH = 650
# Font Constants
FONT = "Arial"
FONT_SIZE = 11
HEADING_SIZE = 20
BUTTON_SIZE = 12  # was 15 before
STATUS_SIZE = 17
# Main frame paddings
MAIN_PAD_X = 5
MAIN_PAD_Y = 5
# Calibration panel paddings
CALIBRATE_PAD_Y = 10
# Combobox panel paddings
COMBO_PAD_X = 10
COMBO_PAD_Y = 3
# Button panel paddings
BUTTON_PAD_X = 10
BUTTON_PAD_Y = 3
# Button width and heigth (in text units)
BUTTON_WIDTH = 8  # was 17
BUTTON_HEIGHT = 3
# Mission
MISSIONS = ["0: Sound Tracking", "1: Audio Collecting"]
# Icon Path
ICON_PATH = "gui/images/yonder_logo.png"


class Main():
    """ Main GUI object that handles all aspects of the User-Interface """

    def __init__(self, in_q=None, out_q=None):
        """ Constructor that handles the initialization of the GUI.
            in_q - An input queue that holds any tasks given to us
        from another thread.
            out_q - An output queue that it used to push tasks to
        the other thread. """

        # Begin initializing the main Tkinter (GUI) framework/root window
        self.root = Tk()
        self.root.resizable(False, False)
        try:
            self.root.iconphoto(True, PhotoImage(file=ICON_PATH))
        except:
            pass

        #### Code below is to fix high resolution screen scaling. ###
        os_enumerator = None
        # https://stackoverflow.com/questions/446209/possible-values-from-sys-platform
        if "linux" in sys.platform:  # Linux designated as "linux"
            os_enumerator = Enumerator.Xinerama
        elif "darwin" in sys.platform:  # Mac OS X designated as "darwin"
            os_enumerator = Enumerator.OSX
        # Windows OS different versions, "win32", "cygwin", "msys" TODO check if this is supported
        elif "win32" in sys.platform or "cygwin" in sys.platform or "msys" in sys.platform:
            os_enumerator = Enumerator.Windows
        if os_enumerator is None:
            print("[GUI] Error: Operating system " +
                  sys.platform + " is not supported.")
            exit()
            return
        screen_width = get_monitors(os_enumerator)[0].width
        screen_height = get_monitors(os_enumerator)[0].height
        self.multiplier_x = screen_width / DEV_WIDTH
        self.multiplier_y = screen_height / DEV_HEIGHT
        global HEADING_SIZE  # Mandate reference to global constant
        global BUTTON_SIZE
        global STATUS_SIZE
        HEADING_SIZE = int(HEADING_SIZE * self.multiplier_y)
        BUTTON_SIZE = int(BUTTON_SIZE * self.multiplier_y)
        STATUS_SIZE = int(STATUS_SIZE * self.multiplier_y)
        global WIDTH, HEIGHT, TOP_FRAME_HEIGHT, BOT_FRAME_HEIGHT, FUNC_FRAME_WIDTH, STATUS_FRAME_WIDTH, CALIBRATE_FRAME_WIDTH, MISSION_FRAME_WIDTH, LOG_FRAME_WIDTH, BUTTON_HEIGHT, BUTTON_WIDTH
        WIDTH = int(WIDTH * self.multiplier_x)
        HEIGHT = int(HEIGHT * self.multiplier_y)
        TOP_FRAME_HEIGHT = int(TOP_FRAME_HEIGHT * self.multiplier_y)
        BOT_FRAME_HEIGHT = int(BOT_FRAME_HEIGHT * self.multiplier_y)
        FUNC_FRAME_WIDTH = int(FUNC_FRAME_WIDTH * self.multiplier_x)
        STATUS_FRAME_WIDTH = int(STATUS_FRAME_WIDTH * self.multiplier_x)
        CALIBRATE_FRAME_WIDTH = int(CALIBRATE_FRAME_WIDTH * self.multiplier_x)
        MISSION_FRAME_WIDTH = int(MISSION_FRAME_WIDTH * self.multiplier_x)
        LOG_FRAME_WIDTH = int(LOG_FRAME_WIDTH * self.multiplier_x)
        self.heat_checker = 0
        ### End of high-resolution screen scaling code ###

        # Fix font scaling for all Combo-box elements
        self.root.option_add("*TCombobox*Listbox*Font", font.Font(family=FONT, size=BUTTON_SIZE))

        # Begin defining instance variables
        self.root.title("YonderDeep AUV Interaction Terminal")
        self.in_q = in_q  # Messages sent here from base_station.py thread
        self.out_q = out_q  # Messages sent to base_station.py thread

        self.top_frame = Frame(self.root, bd=1)
        self.top_frame.pack(fill=BOTH, side=TOP,
                            padx=MAIN_PAD_X, pady=MAIN_PAD_Y, expand=YES)

        self.bot_frame = Frame(self.root, bd=1)
        self.bot_frame.pack(fill=BOTH, side=BOTTOM,
                            padx=MAIN_PAD_X, pady=MAIN_PAD_Y, expand=YES)

        # self.init_function_frame()
        self.init_stack_frame()
        self.init_camera_frame()  # for left panel
        self.init_buttons_frame()  # for left panel
        self.init_motor_control_frame()  # for left panel
        self.init_map_frame()
        self.init_status_frame()
        self.init_calibrate_frame()
        self.init_log_frame()
        self.init_mission_frame()
        self.create_map(self.map_frame)

        # Save our last received BS coordinates
        self.bs_coordinates = None

        # Call function to properly end the program
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.update_idletasks()
        self.root.update()

        # Loop that checks our in-queue tasks given from the BaseStation thread object
        self.root.after(REFRESH_TIME, self.check_tasks)

        # Initializes heading variables
        self.localized_heading = 0.0
        self.current_heading = 0.0

        # Begin running GUI loop
        # self.root.mainloop()

    def check_tasks(self):
        """ Evaluates the commands/tasks given to us in the in-queue. These commands are
        passed as basic string objects. """
        while (self.in_q.empty() is False):
            try:
                eval("self." + self.in_q.get())
            except Exception as e:
                print("Task evaluation error: ", str(e))

        self.root.after(REFRESH_TIME, self.check_tasks)

    def get_time(self, now):
        """ Gets the current time in year-months-day hour:minute:second. """
        return now.strftime("%Y-%m-%d %I:%M %p: ")

    def init_function_frame(self):
        """ Creates the frame for all UI functions. """
        self.functions_frame = Frame(
            self.top_frame, height=TOP_FRAME_HEIGHT, width=FUNC_FRAME_WIDTH, bd=1, relief=SUNKEN)
        self.functions_frame.pack(
            padx=MAIN_PAD_X, pady=MAIN_PAD_Y, side=LEFT, fill=BOTH, expand=NO)
        self.functions_frame.pack_propagate(0)

        self.heading_button = Button(self.functions_frame, text="Calibrate Heading", takefocus=False, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                                     padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=self.calibrate_heading_on_map)
        self.origin_button = Button(self.functions_frame, text="Calibrate Origin", takefocus=False, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                                    padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=self.calibrate_origin_on_map)
        self.add_waypoint_button = Button(self.functions_frame, text="Add Waypoint", takefocus=False, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                                          padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=self.map.new_waypoint_prompt)
        self.nav_to_waypoint_button = Button(self.functions_frame, text="Nav. to Waypoint", takefocus=False, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                                             padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=self.map.nav_to_waypoint)
        # this does not actually have a button --- placed outside, test this
        self.download_data_button = Button(self.functions_frame, text="Download Data", takefocus=False, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                                           padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=lambda: self.out_q.put("download_data()"))
        self.clear_button = Button(self.functions_frame, text="Clear Map", takefocus=False, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                                   padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=self.map.clear)

        self.heading_button.pack(expand=YES)
        self.origin_button.pack(expand=YES)
        self.add_waypoint_button.pack(expand=YES)
        self.nav_to_waypoint_button.pack(expand=YES)
        self.download_data_button.pack(expand=YES)
        self.clear_button.pack(expand=YES)

    def init_stack_frame(self):
        self.stack_frame = Frame(
            self.top_frame, height=TOP_FRAME_HEIGHT, width=FUNC_FRAME_WIDTH, bd=1, relief=SUNKEN)
        self.stack_frame.pack(
            padx=MAIN_PAD_X, pady=MAIN_PAD_Y, side=LEFT, fill=BOTH, expand=NO)
        self.stack_frame.pack_propagate(0)

    def init_camera_frame(self):
        """ Creates the frame for camera window. """
        self.camera_frame = Frame(
            self.stack_frame, height=TOP_FRAME_HEIGHT*(3/7), width=FUNC_FRAME_WIDTH, bd=1, relief=SUNKEN)
        # self.camera_frame.pack(
        #    padx=MAIN_PAD_X, pady=MAIN_PAD_Y*(2/5), side=LEFT, fill=BOTH, expand=NO)
        self.camera_frame.grid(
            row=1, column=1, pady=CALIBRATE_PAD_Y)

    def init_buttons_frame(self):
        """ Creates the frame for buttons. """
        self.buttons_frame = Frame(
            self.stack_frame, height=TOP_FRAME_HEIGHT*(1/7), width=FUNC_FRAME_WIDTH, bd=1, relief=SUNKEN)

        # self.buttons_frame.pack(
        #    padx=MAIN_PAD_X, pady=MAIN_PAD_Y*(3/5), side=LEFT, fill=BOTH, expand=NO)
        self.buttons_frame.grid(
            row=2, column=1, pady=CALIBRATE_PAD_Y)

        # self.download_data_button = Button(self.buttons_frame, anchor=tkinter.W, text="Download\nData", takefocus=False, width=1, height=BUTTON_HEIGHT,
        #                                    padx=BUTTON_PAD_X+25, pady=BUTTON_PAD_Y, font=(4, BUTTON_SIZE), command=lambda: self.out_q.put("send_download_data()"))
        # Add calibrate depth button command to the below button
        # self.calibrate_depth_button = Button(self.buttons_frame, anchor=tkinter.W, text="Calibrate\nDepth", takefocus=False, width=1, height=BUTTON_HEIGHT,
        #                                      padx=BUTTON_PAD_X+35, pady=BUTTON_PAD_Y, font=(4, BUTTON_SIZE), command=lambda: self.out_q.put("send_calibrate_depth()"))

        # self.dive_command_button = Button(self.buttons_frame, anchor=tkinter.W, text="Dive\nCommand", takefocus=False, width=1, height=BUTTON_HEIGHT,
        #                                   padx=BUTTON_PAD_X+45, pady=BUTTON_PAD_Y, font=(4, BUTTON_SIZE), command=lambda: self.out_q.put("send_dive())"))

        self.download_data_button = Button(self.buttons_frame, anchor=tkinter.W, text="Download\nData", takefocus=False,
                                           padx=BUTTON_PAD_X+25, pady=BUTTON_PAD_Y, font=(FONT_SIZE, BUTTON_SIZE), command=lambda: self.out_q.put("send_download_data()"))

        self.calibrate_depth_button = Button(self.buttons_frame, anchor=tkinter.W, text="Calibrate\nDepth", takefocus=False,
                                             padx=BUTTON_PAD_X+35, pady=BUTTON_PAD_Y, font=(FONT_SIZE, BUTTON_SIZE), command=lambda: self.out_q.put("send_calibrate_depth()"))

        # self.dive_command_button = Button(self.buttons_frame, anchor=tkinter.W, text="Dive\nCommand", takefocus=False,
        #                                   padx=BUTTON_PAD_X+45, pady=BUTTON_PAD_Y, font=(4, BUTTON_SIZE), command=lambda: self.out_q.put("send_dive())"))

        self.download_data_button.pack(expand=YES, side=LEFT)
        self.download_data_button.place(relx=0, rely=0)

        self.calibrate_depth_button.pack(expand=YES, side=LEFT)
        self.calibrate_depth_button.place(relx=0.5, rely=0)

        # self.dive_command_button.pack(expand=YES, side=LEFT)
        # self.dive_command_button.place(relx=0.67, rely=0)

    def init_motor_control_frame(self):
        """ Creates the frame for motor control. """
        self.motor_control_frame = Frame(
            self.stack_frame, height=TOP_FRAME_HEIGHT*(3/7), width=FUNC_FRAME_WIDTH, bd=0.4, relief=SUNKEN)
        # self.motor_control_frame.pack(
        #    padx=MAIN_PAD_X, pady=MAIN_PAD_Y*(4/5), side=LEFT, fill=BOTH, expand=NO)
        self.motor_control_frame.grid(
            row=3, column=1, pady=CALIBRATE_PAD_Y)

        self.header_label = Label(self.motor_control_frame, text="Motor Control", font=(FONT, HEADING_SIZE))
        self.header_label.pack()
        self.header_label.place(relx=0.05, rely=0.3)

        self.distance_label = Label(self.motor_control_frame, text="Distance\n(0-100m)", font=(FONT, FONT_SIZE))
        self.distance_label.pack()
        self.distance_label.place(relx=0.05, rely=0.45)

        self.angle_label = Label(self.motor_control_frame, text="Angle\n(-180-180\N{DEGREE SIGN})", font=(FONT, FONT_SIZE))
        self.angle_label.pack()
        self.angle_label.place(relx=0.05, rely=0.65)

        prompt_input_distance = Entry(self.motor_control_frame, bd=5, font=(FONT, FONT_SIZE-3))
        prompt_input_distance.pack()
        prompt_input_distance.place(relx=0.4, rely=0.475)

        prompt_input_angle = Entry(self.motor_control_frame, bd=5, font=(FONT, FONT_SIZE-3))
        prompt_input_angle.pack()
        prompt_input_angle.place(relx=0.4, rely=0.675)

        # Add commands to halt and send buttons
        self.halt_button = Button(self.motor_control_frame, text="Halt", takefocus=False,
                                  width=BUTTON_WIDTH-15, height=BUTTON_HEIGHT - 10, padx=BUTTON_PAD_X,
                                  pady=BUTTON_PAD_Y, bg='dark red', activebackground="red", overrelief="sunken", font=(FONT, BUTTON_SIZE), command=lambda: self.send_halt())
        self.halt_button.pack(expand=YES)
        self.halt_button.place(relx=0.3, rely=0.85)

        self.send_button = Button(self.motor_control_frame, text="Send", takefocus=False, width=BUTTON_WIDTH-15, height=BUTTON_HEIGHT - 10,
                                  padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE))
        self.send_button.pack(expand=YES)
        self.send_button.place(relx=0.6, rely=0.85)

        self.dive_button = Button(self.motor_control_frame, text="Dive", takefocus=False,
                                  width=BUTTON_WIDTH-15, height=BUTTON_HEIGHT - 10, padx=BUTTON_PAD_X,
                                  pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=lambda: self.confirm_dive(int(prompt_input_dive.get())))

        self.dive_button.pack(expand=YES)
        self.dive_button.place(relx=0.05, rely=0.00)

        prompt_input_dive = Entry(self.motor_control_frame, bd=5, font=(FONT, FONT_SIZE-3))
        prompt_input_dive.pack()
        prompt_input_dive.place(relx=0.4, rely=0.000)

    def send_halt(self):
        self.out_q.put("send_halt()")

    def confirm_dive(self, depth):
        # TODO messages
        if depth < 1 or depth > 50:
            messagebox.showerror("ERROR", "Select a depth between 1 and 50 meters inclusive. ")
            return

        # Prompt mission start
        prompt = "Dive: " + str(depth) + " meters?"
        ans = messagebox.askquestion("Dive", prompt)
        if ans == 'yes':
            self.out_q.put("send_dive(" + str(depth) + ")")

    def init_map_frame(self):
        """ Create the frame for the x, y map """

        self.map_frame = Frame(self.top_frame, height=TOP_FRAME_HEIGHT,
                               width=TOP_FRAME_HEIGHT, bd=1, relief=SUNKEN)
        self.map_frame.pack(fill=X, padx=MAIN_PAD_X,  # fill=X at beginning
                            pady=MAIN_PAD_Y, side=LEFT, expand=YES)
        self.map_frame.pack_propagate(0)

    def init_status_frame(self):
        """ Initializes the status frame (top right frame). """
        self.status_frame = Frame(
            self.top_frame, height=TOP_FRAME_HEIGHT, width=STATUS_FRAME_WIDTH, bd=1, relief=SUNKEN)
        self.status_frame.pack(padx=MAIN_PAD_X,
                               pady=MAIN_PAD_Y, side=LEFT, expand=NO)
        self.status_frame.pack_propagate(0)
        self.status_label = Label(
            self.status_frame, text="AUV Data", font=(FONT, HEADING_SIZE))
        self.status_label.pack()
        self.status_label.place(relx=0.22, rely=0.075)

        self.position_label_string = StringVar()
        self.position_label = Label(self.status_frame, textvariable=self.position_label_string, font=(
            FONT, STATUS_SIZE), justify=LEFT)
        self.position_label.pack()
        self.position_label_string.set("Position \n \tX: N/A \t Y: N/A")
        self.position_label.place(relx=0.05, rely=0.25, anchor='sw')

        self.heading_label_string = StringVar()
        self.heading_label = Label(self.status_frame, textvariable=self.heading_label_string, font=(
            FONT, STATUS_SIZE), justify=LEFT)
        self.heading_label.pack()
        self.heading_label_string.set("Heading: N/A")
        self.heading_label.place(relx=0.05, rely=0.37, anchor='sw')

        self.battery_status_string = StringVar()
        self.battery_voltage = Label(
            self.status_frame, textvariable=self.battery_status_string, font=(FONT, STATUS_SIZE))
        self.battery_voltage.pack()
        self.battery_status_string.set("Battery Voltage: Not Implemented")
        self.battery_voltage.place(relx=0.05, rely=0.45, anchor='sw')

        self.temperature_string = StringVar()
        self.temperature = Label(
            self.status_frame, textvariable=self.temperature_string, font=(FONT, STATUS_SIZE))
        self.temperature.pack()
        self.temperature_string.set("Internal Temperature: N/A")
        self.temperature.place(relx=0.05, rely=0.52, anchor='sw')

        self.movement_status_string = StringVar()
        self.movement_status = Label(
            self.status_frame, textvariable=self.movement_status_string, font=(FONT, STATUS_SIZE))
        self.movement_status.pack()
        self.movement_status_string.set("Movement Status: TODO")
        self.movement_status.place(relx=0.05, rely=0.59, anchor='sw')

        self.mission_status_string = StringVar()
        self.mission_status = Label(
            self.status_frame, textvariable=self.mission_status_string, font=(FONT, STATUS_SIZE))
        self.mission_status.pack()
        self.mission_status_string.set("Mission Status: Waiting")
        self.mission_status.place(relx=0.05, rely=0.66, anchor='sw')

        self.flooded_string = StringVar()
        self.flooded = Label(
            self.status_frame, textvariable=self.flooded_string, font=(FONT, STATUS_SIZE))
        self.flooded.pack()
        self.flooded_string.set("Flooded: Not Implemented")
        self.flooded.place(relx=0.05, rely=0.73, anchor='sw')

        self.depth_string = StringVar()
        self.depth = Label(
            self.status_frame, textvariable=self.depth_string, font=(FONT, STATUS_SIZE))
        self.depth.pack()
        self.depth_string.set("Depth: 0meters")
        self.depth.place(relx=0.05, rely=0.80, anchor='sw')

        self.control_string = StringVar()
        self.control = Label(
            self.status_frame, textvariable=self.control_string, font=(FONT, STATUS_SIZE))
        self.control.pack()
        self.control_string.set("Control: (distance/angle or xbox) (calculated locally)")
        self.control.place(relx=0.05, rely=0.87, anchor='sw')

        self.comms_status_string = StringVar()
        self.comms_status = Label(
            self.status_frame, textvariable=self.comms_status_string, font=(FONT, STATUS_SIZE))
        self.comms_status.pack()
        self.comms_status_string.set("Comms: not connected")
        self.comms_status.place(relx=0.05, rely=0.93, anchor='sw')

        self.xbox_label_string = StringVar()
        self.xbox_label = Label(self.status_frame, textvariable=self.xbox_label_string, font=(
            FONT, STATUS_SIZE), justify=LEFT)
        self.xbox_label.pack()
        self.xbox_label_string.set("Xbox Controller: Inactive")
        self.xbox_label.place(relx=0.05, rely=0.98, anchor='sw')

        # self.calibrate_xbox_button           = Button(self.status_frame, text = "Calibrate Controller", takefocus = False, width = BUTTON_WIDTH + 10, height = BUTTON_HEIGHT,
        #                                      padx = BUTTON_PAD_X, pady = BUTTON_PAD_Y, font = (FONT, BUTTON_SIZE), command = self.base_station.calibrate_controller )
        # self.calibrate_xbox_button.pack()
        # self.calibrate_xbox_button.place(relx = 0.05, rely = 0.80);
        # self.establish_comm_button           = Button(self.status_frame, text = "Connect to AUV", takefocus = False, width = BUTTON_WIDTH, height = BUTTON_HEIGHT,
        #                                       padx = BUTTON_PAD_X, pady = BUTTON_PAD_Y, font = (FONT, BUTTON_SIZE), command = self.base_station.calibrate_communication )
        # self.establish_comm_button.pack()
        # self.establish_comm_button.place(relx = 0.05, rely = 0.90);

    def init_log_frame(self):
        """ Initializes the log/console frame in the bottom-middle part of the GUI. """
        self.log_frame = Frame(
            self.bot_frame, height=BOT_FRAME_HEIGHT, width=LOG_FRAME_WIDTH, bd=1, relief=SUNKEN)
        self.log_frame.pack(fill=BOTH, padx=MAIN_PAD_X,
                            pady=MAIN_PAD_Y, side=LEFT, expand=YES)
        self.log_frame.pack_propagate(0)
        self.console = Text(self.log_frame, font=(
            FONT, BUTTON_SIZE-2), state=DISABLED, width=LOG_FRAME_WIDTH)

        self.scrollbar = Scrollbar(self.log_frame)
        self.scrollbar.config(command=self.console.yview)
        self.console.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.console.pack()

    def log(self, string):
        """ Inserts/Logs the message into the console object. """
        time = self.get_time(datetime.datetime.now())
        self.console.config(state=NORMAL)
        self.console.insert(END, time + string + "\n")
        self.console.config(state=DISABLED)

    def add_auv_coordinates(self, northing, easting):
        """ Plots the AUV's current coordinates onto the map, given its UTM-relative northing and easting. """
        self.map.add_auv_data(northing, easting)

    def update_bs_coordinates(self, northing, easting):
        """ Saves base stations current coordinates, updates label on the data panel """
        self.bs_coordinates = (northing, easting)

    def set_connection(self, status):
        """ Sets the connection status text in the status frame. """
        if (status):
            self.comms_status_string.set("Comms Status: Connected.")
        else:
            self.comms_status_string.set("Comms Status: Not connected.")

    def set_movement(self, manual):
        """ Sets the movement status text in the status frame. """
        if (not manual):
            self.movement_status_string.set("Movement Status: Manual Control")
        else:
            self.movement_status_string.set(
                "Movement Status: Autonomous Control")

    def set_battery_voltage(self, voltage):
        self.battery_status_string.set("Battery Voltage: " + str(voltage))

    def set_heading(self, direction):
        """ Sets heading text """
        try:
            self.current_heading = float(direction)
            self.heading_label_string.set("Heading: " + str(self.current_heading - self.localized_heading))
        except Exception as e:
            print(str(e))
            print("failed to set heading of " + str(direction))

    def set_mission_status(self, mission):
        self.mission_status_string.set("Mission Status: " + str(mission))

    def set_flooded(self, flooded):
        self.flooded_string.set("Flooded: " + str(flooded))

    def set_control(self, control):
        self.control_string.set("Control: " + str(control))

    def set_temperature(self, temperature):
        """ Sets internal temperature text """
        self.temperature_string.set(
            "Internal Temperature: " + str(temperature) + "C")
        if temperature >= constants.HOT_TEMP:
            if self.heat_checker < 2:
                messagebox.showwarning("WARNING", "AUV has reached throttling rate! Recommend toggling kill all!")
                self.heat_checker = 2
        elif temperature >= constants.SAFE_TEMP:
            if self.heat_checker < 1:
                messagebox.showwarning("WARNING", "AUV temperature is reaching unsafe levels!")
                self.heat_checker = 1
        else:
            self.heat_checker = 0

    # def set_pressure(self, pressure):
    #     """ Sets depth text """
    #     self.pressure_string.set(
    #         "pressure: " + str(pressure) + "mBar")

    def set_depth(self, depth):
        """ Sets depth text """
        self.depth_string.set(
            "depth: " + str(depth) + "meter")

    def set_xbox_status(self, isActive, isVertical):
        """ Set xbox controller status text """
        if not isActive:
            self.xbox_label_string.set(
                "Xbox Controller: Inactive")
            return
        if isVertical == 1:
            self.xbox_label_string.set(
                "Xbox Controller: Sending Vertical")
        else:
            self.xbox_label_string.set(
                "Xbox Controller: Sending Horizontal")

    def set_dive(self, depth):
        """ Sets dive command """
        self.depth_string.set(
            "dive " + str(depth) + "meters")

    def set_position(self, xPos, yPos):
        self.position_label_string.set(
            "Position \n \tX: " + str(xPos) + "\t Y: " + str(yPos))

    def init_calibrate_frame(self):
        self.calibrate_frame = Frame(
            self.bot_frame, height=BOT_FRAME_HEIGHT, width=CALIBRATE_FRAME_WIDTH, bd=1, relief=SUNKEN)
        self.calibrate_frame.pack(
            fill=Y, padx=MAIN_PAD_X, pady=0, side=LEFT, expand=NO)
        self.calibrate_frame.pack_propagate(0)

        self.calibrate_label = Label(
            self.calibrate_frame, text="Motor Testing", takefocus=False, font=(FONT, HEADING_SIZE))
        self.calibrate_label.grid(row=0, columnspan=4, sticky=W+E)

        # test move forward
        self.forward_calibrate_button = Button(self.calibrate_frame, text="Forward", takefocus=False,  # width = 15, height = 3,
                                               padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(
                                                   FONT, BUTTON_SIZE),
                                               command=lambda: self.out_q.put("test_motor('Forward')"))
        # NAV X S Y
        self.forward_calibrate_button.grid(
            row=1, column=1, pady=CALIBRATE_PAD_Y)

        self.backward_calibrate_button = Button(self.calibrate_frame, text="Backward", takefocus=False,  # width = 15, height = 3,
                                                padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(
                                                    FONT, BUTTON_SIZE),
                                                command=lambda: self.out_q.put("test_motor('Backward')"))

        self.backward_calibrate_button.grid(row=2, column=1, pady=CALIBRATE_PAD_Y)

        # TODO ask about these tests
        # self.calibrate_all_button = Button(self.calibrate_frame, text="All", takefocus=False,  # width = 15, height = 3,
        #                                    padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(
        #                                        FONT, BUTTON_SIZE),
        #                                    command=lambda: self.out_q.put("test_motor('ALL')"))

        # self.calibrate_all_button.grid(row=5, column=1, pady=CALIBRATE_PAD_Y)

        self.vertical_down_calibrate_button = Button(self.calibrate_frame, text="Down", takefocus=False,  # width = 15, height = 3,
                                                     padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(
                                                         FONT, BUTTON_SIZE),
                                                     command=lambda: self.out_q.put("test_motor('Down')"))

        self.vertical_down_calibrate_button.grid(row=3, column=1, pady=CALIBRATE_PAD_Y)

        self.left_calibrate_button = Button(self.calibrate_frame, text="Left", takefocus=False,  # width = 15, height = 3,
                                            padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(
                                                FONT, BUTTON_SIZE),
                                            command=lambda: self.out_q.put("test_motor('Left')"))
        # X = 10, Y = 90
        self.left_calibrate_button.grid(row=4, column=1, pady=CALIBRATE_PAD_Y)

        self.right_calibrate_button = Button(self.calibrate_frame, text="Right", takefocus=False,  # width = 15, height = 3,
                                             padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(
                                                 FONT, BUTTON_SIZE),
                                             command=lambda: self.out_q.put("test_motor('Right')"))
        # X = 10, Y = 90
        self.right_calibrate_button.grid(row=5, column=1, pady=CALIBRATE_PAD_Y)

    def init_mission_frame(self):
        self.mission_frame = Frame(
            self.bot_frame, height=BOT_FRAME_HEIGHT, width=MISSION_FRAME_WIDTH, bd=1, relief=SUNKEN)

        self.mission_frame.pack(fill=Y, padx=COMBO_PAD_X,
                                pady=0, side=LEFT, expand=NO)
        self.mission_frame.pack_propagate(0)

        self.depth_label = Label(self.mission_frame, text="Depth(m):", font=(FONT, FONT_SIZE))
        self.depth_label.pack()
        self.depth_label.place(relx=0.06, rely=0.41)

        self.time_label = Label(self.mission_frame, text="Time(s):", font=(FONT, FONT_SIZE))
        self.time_label.pack()
        self.time_label.place(relx=0.06, rely=0.535)

        prompt_input_depth = Entry(self.mission_frame, bd=5, font=(FONT, FONT_SIZE))
        prompt_input_depth.pack()
        prompt_input_depth.place(relx=0.3, rely=0.4)

        prompt_input_time = Entry(self.mission_frame, bd=5, font=(FONT, FONT_SIZE))
        prompt_input_time.pack()
        prompt_input_time.place(relx=0.3, rely=0.525)

        self.mission_label = Label(
            self.mission_frame, text="Mission Control", takefocus=False, font=(FONT, HEADING_SIZE))
        self.mission_label.pack(expand=YES)
        self.mission_label.place(relx=0.24, rely=0.1)

        self.mission_list = Combobox(self.mission_frame, state="readonly", values=MISSIONS, font=(FONT, BUTTON_SIZE))
        self.mission_list.set("Select Mission...")
        self.mission_list.pack(expand=YES, fill=X, pady=COMBO_PAD_Y)
        self.mission_list.place(relx=0.15, rely=0.25)

        self.start_mission_button = Button(self.mission_frame, text="Start Mission", takefocus=False,
                                           width=BUTTON_WIDTH+2, height=BUTTON_HEIGHT - 10, padx=BUTTON_PAD_X,
                                           pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE+5), command=lambda: self.confirm_mission(int(prompt_input_depth.get()), int(prompt_input_time.get())))
        self.start_mission_button.pack(expand=YES)
        self.start_mission_button.place(relx=0.1, rely=0.65)

        self.abort_button = Button(self.mission_frame, text="ABORT MISSION", takefocus=False, width=BUTTON_WIDTH+4, height=BUTTON_HEIGHT - 10,
                                   padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, bg='dark red', activebackground="red", overrelief="sunken", font=(FONT, BUTTON_SIZE), command=self.abort_mission)
        self.abort_button.pack(expand=YES)
        self.abort_button.place(relx=0.18, rely=0.85)

    def confirm_mission(self, depth, time):
        # TODO messages
        mission = self.mission_list.get()

        if mission == "Select Mission...":
            # Prevent mission from starting if a mission was not properly selected
            self.log("Please select a mission before starting.")
        else:
            if (depth < 1 or depth > 50) or (time < 15 or time > 300):
                messagebox.showerror("ERROR", "Select a depth between 1 and 50 meters inclusive and select a time between 15 and 300 seconds. ")
                return

            # Prompt mission start
            prompt = "Start mission: " + mission + "?"
            ans = messagebox.askquestion("Mission Select", prompt)

            if ans == 'yes':  # Send index of mission (0, 1, 2, etc...)

                self.out_q.put(
                    "start_mission(" + str(self.mission_list.current()) + ")")

    def abort_mission(self):
        ans = messagebox.askquestion(
            "Abort Misssion", "Are you sure you want to abort the mission?")
        if ans == 'yes':
            self.out_q.put("abort_mission()")

    def calibrate_origin_on_map(self):
        """ Calibrates the origin on the map to the base stations coordinates """
        print("ran calibrate origin")
        if self.bs_coordinates is not None:
            # Update the origin on our map.
            self.map.zero_map(self.bs_coordinates[0], self.bs_coordinates[1])
            self.log("Updated the origin on the map to UTM coordinates (" + str(self.bs_coordinates[0]) + "," + str(self.bs_coordinates[1]) + ").")
        else:
            self.log("Cannot calibrate origin because the base station has not reported GPS data.")

    def calibrate_heading_on_map(self):
        """ Calibrates heading on the map to the AUV's heading """
        print("ran calibrate heading:")
        if self.heading_label_string is not None:
            # Update heading
            self.heading_label_string.set("Heading: 0.0")
            print("heading changed from", self.localized_heading)
            self.localized_heading = self.current_heading
            print("to", self.current_heading, self.localized_heading)
        else:
            self.log("Cannot calibrate heading because the base station has not reported heading data.")

    # def get_angle(self):

    def create_map(self, frame):
        self.map = Map(frame, self)

    def on_closing(self):
        #    self.map.on_close()
        self.out_q.put("close()")  # TODO
        self.root.destroy()
        sys.exit()
