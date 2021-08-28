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
from tkinter import PhotoImage
from tkinter import Scrollbar
from tkinter import Toplevel
from tkinter import StringVar
from tkinter import BOTH, TOP, BOTTOM, LEFT, RIGHT, YES, NO, SUNKEN, X, Y, W, E, N, S, DISABLED, NORMAL, END
from tkinter import messagebox
from tkinter.ttk import Combobox
from tkinter import font
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
HEADING_SIZE = 20
BUTTON_SIZE = 15
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
BUTTON_WIDTH = 17
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

        self.init_function_frame()
        self.init_map_frame()
        self.init_status_frame()
        self.init_calibrate_frame()
        self.init_log_frame()
        self.init_mission_frame()
        self.create_map(self.map_frame)
        self.create_function_buttons()

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
        self.root.mainloop()

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

    def init_map_frame(self):
        """ Create the frame for the x, y map """

        self.map_frame = Frame(self.top_frame, height=TOP_FRAME_HEIGHT,
                               width=TOP_FRAME_HEIGHT, bd=1, relief=SUNKEN)
        self.map_frame.pack(fill=X, padx=MAIN_PAD_X,  # fill=X at beginning
                            pady=MAIN_PAD_Y, side=LEFT, expand=YES)
        self.map_frame.pack_propagate(0)

    def init_status_frame(self):
        """ Initializes the status frame (rop right frame). """
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
        self.position_label.place(relx=0.05, rely=0.30, anchor='sw')

        self.heading_label_string = StringVar()
        self.heading_label = Label(self.status_frame, textvariable=self.heading_label_string, font=(
            FONT, STATUS_SIZE), justify=LEFT)
        self.heading_label.pack()
        self.heading_label_string.set("Heading: N/A")
        self.heading_label.place(relx=0.05, rely=0.40, anchor='sw')

        self.battery_status_string = StringVar()
        self.battery_voltage = Label(
            self.status_frame, textvariable=self.battery_status_string, font=(FONT, STATUS_SIZE))
        self.battery_voltage.pack()
        self.battery_status_string.set("Battery Voltage: N/A")
        self.battery_voltage.place(relx=0.05, rely=0.50, anchor='sw')

        self.temperature_string = StringVar()
        self.temperature = Label(
            self.status_frame, textvariable=self.temperature_string, font=(FONT, STATUS_SIZE))
        self.temperature.pack()
        self.temperature_string.set("Internal Temperature: N/A")
        self.temperature.place(relx=0.05, rely=0.60, anchor='sw')

        self.vehicle_status_string = StringVar()
        self.vehicle_status = Label(
            self.status_frame, textvariable=self.vehicle_status_string, font=(FONT, STATUS_SIZE))
        self.vehicle_status.pack()
        self.vehicle_status_string.set("Vehicle Status: Manual Control")
        self.vehicle_status.place(relx=0.05, rely=0.70, anchor='sw')

        self.comms_status_string = StringVar()
        self.comms_status = Label(
            self.status_frame, textvariable=self.comms_status_string, font=(FONT, STATUS_SIZE))
        self.comms_status.pack()
        self.comms_status_string.set("Comms Status: Not connected")
        self.comms_status.place(relx=0.05, rely=0.80, anchor='sw')

        self.pressure_string = StringVar()
        self.pressure = Label(
            self.status_frame, textvariable=self.pressure_string, font=(FONT, STATUS_SIZE))
        self.pressure.pack()
        self.pressure_string.set("depth: 0mBar")
        self.pressure.place(relx=0.05, rely=0.90, anchor='sw')

        self.depth_string = StringVar()
        self.depth = Label(
            self.status_frame, textvariable=self.depth_string, font=(FONT, STATUS_SIZE))
        self.depth.pack()
        self.depth_string.set("depth: 0meters")
        self.depth.place(relx=0.05, rely=1.0, anchor='sw')
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

    def set_vehicle(self, manual):
        """ Sets the vehicle status text in the status frame. """
        if (manual):
            self.vehicle_status_string.set("Vehicle Status: Manual Control")
        else:
            self.vehicle_status_string.set(
                "Vehicle Status: Autonomous Control")

    def set_battery_voltage(self, voltage):
        self.battery_status_string.set("Battery Voltage: " + voltage)

    def set_heading(self, direction):
        """ Sets heading text """
        try:
            self.current_heading = float(direction)
            self.heading_label_string.set("Heading: " + str(self.current_heading - self.localized_heading))
        except Exception as e:
            print(str(e))
            print("failed to set heading of " + str(direction))

    def set_temperature(self, temperature):
        """ Sets internal temperature text """
        self.temperature_string.set(
            "Internal Temperature: " + str(temperature) + "C")

    def set_pressure(self, pressure):
        """ Sets depth text """
        self.pressure_string.set(
            "pressure: " + str(pressure) + "mBar")

    def set_depth(self, depth):
        """ Sets depth text """
        self.depth_string.set(
            "depth: " + str(depth) + "meter")

    def set_position(self, xPos, yPos):
        self.position_label_string.set(
            "Position \n \tX: " + xPos + "\t Y: " + yPos)

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
            row=4, column=1, pady=CALIBRATE_PAD_Y)

        self.turn_calibrate_button = Button(self.calibrate_frame, text="Right", takefocus=False,  # width = 15, height = 3,
                                            padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(
                                                FONT, BUTTON_SIZE),
                                            command=lambda: self.out_q.put("test_motor('Right')"))
        # X = 10, Y = 90
        self.turn_calibrate_button.grid(row=1, column=1, pady=CALIBRATE_PAD_Y)

        self.front_calibrate_button = Button(self.calibrate_frame, text="Left", takefocus=False,  # width = 15, height = 3,
                                             padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(
                                                 FONT, BUTTON_SIZE),
                                             command=lambda: self.out_q.put("test_motor('Left')"))

        self.front_calibrate_button.grid(row=2, column=1, pady=CALIBRATE_PAD_Y)

        # TODO ask about these tests
        self.calibrate_all_button = Button(self.calibrate_frame, text="All", takefocus=False,  # width = 15, height = 3,
                                           padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(
                                               FONT, BUTTON_SIZE),
                                           command=lambda: self.out_q.put("test_motor('ALL')"))

        self.calibrate_all_button.grid(row=5, column=1, pady=CALIBRATE_PAD_Y)

        self.back_calibrate_button = Button(self.calibrate_frame, text="Back", takefocus=False,  # width = 15, height = 3,
                                            padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(
                                                FONT, BUTTON_SIZE),
                                            command=lambda: self.out_q.put("test_motor('BACK')"))

        self.back_calibrate_button.grid(row=3, column=1, pady=CALIBRATE_PAD_Y)

    def init_mission_frame(self):
        self.mission_frame = Frame(
            self.bot_frame, height=BOT_FRAME_HEIGHT, width=MISSION_FRAME_WIDTH, bd=1, relief=SUNKEN)

        self.mission_frame.pack(fill=Y, padx=COMBO_PAD_X,
                                pady=0, side=LEFT, expand=NO)
        self.mission_frame.pack_propagate(0)

        self.mission_label = Label(
            self.mission_frame, text="Mission Control", takefocus=False, font=(FONT, HEADING_SIZE))

        self.mission_label.pack(expand=YES)
        self.mission_list = Combobox(self.mission_frame, state="readonly", values=MISSIONS, font=(FONT, BUTTON_SIZE))
        self.mission_list.set("Select Mission...")
        self.mission_list.pack(expand=YES, fill=X, pady=COMBO_PAD_Y)
        # self.mission_list.bind("<<ComboboxSelected>>", lambda _ : out_q.put(missions.index(self_mission_list.get())))

        self.start_mission_button = Button(self.mission_frame, text="Start Mission", takefocus=False,
                                           width=BUTTON_WIDTH, height=BUTTON_HEIGHT, padx=BUTTON_PAD_X,
                                           pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE+5), command=self.confirm_mission)
        self.start_mission_button.pack(expand=YES)  # TODO

        self.abort_button = Button(self.mission_frame, text="ABORT MISSION", takefocus=False, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                                   padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, bg='dark red', activebackground="red", overrelief="sunken", font=(FONT, BUTTON_SIZE), command=self.abort_mission)
        self.abort_button.pack(expand=YES)

    def confirm_mission(self):
        # TODO messages
        mission = self.mission_list.get()

        if mission == "Select Mission...":
            # Prevent mission from starting if a mission was not properly selected
            messagebox.showerror(
                "Mission Select", "Please select a mission before starting.")
        else:
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

    def create_function_buttons(self):
        self.heading_button = Button(self.functions_frame, text="Calibrate Heading", takefocus=False, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                                     padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=self.calibrate_heading_on_map)
        self.origin_button = Button(self.functions_frame, text="Calibrate Origin", takefocus=False, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                                    padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=self.calibrate_origin_on_map)
        self.add_waypoint_button = Button(self.functions_frame, text="Add Waypoint", takefocus=False, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                                          padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=self.map.new_waypoint_prompt)
        self.nav_to_waypoint_button = Button(self.functions_frame, text="Nav. to Waypoint", takefocus=False, width=BUTTON_WIDTH, height=BUTTON_HEIGHT,
                                             padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=self.map.nav_to_waypoint)
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

    def create_map(self, frame):
        self.map = Map(frame, self)
        self.zoom_in_button = Button(self.map_frame, text="+", takefocus=False, width=1, height=1,
                                     padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=self.map.zoom_in)
        self.zoom_in_button.place(relx=1, rely=0.0, anchor=N+E)

        self.zoom_out_button = Button(self.map_frame, text="-", takefocus=False, width=1, height=1,
                                      padx=BUTTON_PAD_X, pady=BUTTON_PAD_Y, font=(FONT, BUTTON_SIZE), command=self.map.zoom_out)
        self.zoom_out_button.place(relx=1, rely=0.06, anchor=N+E)

    def on_closing(self):
        #    self.map.on_close()
        self.out_q.put("close()")  # TODO
        self.root.destroy()
        sys.exit()
