""" Tkinter map object used in the Main gui file """
# Begin imports for MatplotLib
from tkinter import *
from matplotlib.pyplot import scatter
from matplotlib.pyplot import plot
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter.ttk import Combobox
import matplotlib
import matplotlib.axes
matplotlib.use('TkAgg')

# Begin imports for tkinter

# Object & Map Constants
DEFAULT_FIGURE_SIZE = 30  # Window Size
DEFAULT_GRID_SIZE = 550  # Grid Size in Meters

# String Constants
KILOMETERS = "Kilometers (km)"
METERS = "Meters (m)"
MILES = "Miles (mi)"

# Color Constants
BACKGROUND_COLOR = 'darkturquoise'
AUV_PATH_COLOR = 'red'
WAYPOINT_COLOR = 'red'
MINOR_TICK_COLOR = 'black'

# Conversion Multiplier Constants
M_TO_M = 1000.000000000
MI_TO_M = 1609.340000000
KM_TO_MI = 0000.621371000
M_TO_MI = 0000.000621371
MI_TO_KM = 0001.609340000
M_TO_KM = 0000.001000000

# Other Debug Constants
ZOOM_SCALAR = 1.15
CLOSE_ENOUGH = 0.25

# Popup Window Contstants
PROMPT_WINDOW_WIDTH = 620
PROMPT_WINDOW_HEIGHT = 400

# Font Constants
FONT = "Arial"
FONT_SIZE = 11


class Map:
    """ Map class creates a map of the position of the AUV """

    def __init__(self,  window, main):
        """ Initialize Class variables """
        # Define the window.
        self.window = window
        self.main = main

        # Initialize object data/information
        self.waypoints = list()
        self.units = METERS
        self.size = DEFAULT_GRID_SIZE
        self.zero_offset_x = 0
        self.zero_offset_y = 0
        # Used to move the map whenever the boat moves.
        self.old_position = 0
        self.press_position = [0, 0]
        self.mouse_pressing = False
        self.legend_obj = None
        self.auv_path_obj = None
        self.auv_data = [list(), list()]

        # Inialize the Tk-compatible Figure, the map, and the canvas
        self.fig = self.init_fig()
        self.map = self.init_map()
        self.canvas = self.init_canvas()
        # Start listening for mouse-clicks
        #self.fig.canvas.mpl_connect('button_press_event',   self.on_press)
        #self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        #self.fig.canvas.mpl_connect('motion_notify_event',  self.on_move)

        # Assign default values.
        self.set_range()  # Set to default range

        # Re-draw the canvas.
        self.draw_canvas()

        # Adjust prompt window width + height for Screen scaling
        global PROMPT_WINDOW_HEIGHT, PROMPT_WINDOW_WIDTH, FONT_SIZE
        PROMPT_WINDOW_WIDTH = int(PROMPT_WINDOW_WIDTH * self.main.multiplier_x)
        PROMPT_WINDOW_HEIGHT = int(PROMPT_WINDOW_HEIGHT * self.main.multiplier_y)
        FONT_SIZE = int(FONT_SIZE * self.main.multiplier_x)

        self.draw_canvas()
        self.add_waypoint(0, 0)

    def clear(self):
        """ Clears the map data """
        self.clear_waypoints()
        self.clear_auv_path()
        self.draw_canvas()
        print("[MAP] Map cleared.")

        self.main.log("Map has been successfully cleared.")

    def clear_auv_path(self):
        """ Clears the AUV path """
        if self.auv_path_obj is not None and self.auv_path_obj.pop(0) is not None:
            self.auv_path_obj.pop(0).remove()

        self.auv_data[0].clear()  # clear all x values
        self.auv_data[1].clear()  # clear all y values

    # def undraw_waypoints(self):
    #     """ Clears waypoints from the map """
    #     for waypoint in self.waypoints:
    #         # Remove waypoint from map.
    #         if waypoint[3] != None and type(waypoint[3]) != tuple:
    #             waypoint[3].pop(0).remove()
    #             waypoint[3] = None

    #         if waypoint[4] != None:
    #             waypoint[4].remove()
    #             waypoint[4] = None

    #     self.draw_canvas()

    # def clear_waypoints(self):
    #     """ Clears and removes waypoints """
    #     self.undraw_waypoints()
    #     del self.waypoints[:]

    def zero_map(self, x=0, y=0):
        """ Sets the origin of our coordinate system to (x,y) in UTM northing/eastings values"""

        # Move all old elements (waypoint, auv path) to their new position.
        delta_x = self.zero_offset_x - x  # oldX - newX = adjustment
        delta_y = self.zero_offset_y - y  # oldY - newY = adjustment

        for waypoint in self.waypoints:  # Move waypoints based on our new Origin
            waypoint[0] += delta_x
            waypoint[1] += delta_y

        for i in range(0, len(self.auv_data[0])):  # Move all auv_data based on our new Origin
            self.auv_data[0][i] += delta_x
            self.auv_data[1][i] += delta_y

        # Actually update our new origin.
        self.zero_offset_x = x
        self.zero_offset_y = y

        # Redraw waypoints based on new origin.
        if len(self.waypoints) > 0:
            self.redraw_waypoints()

        # Redraw auv-path based on new origin
        if len(self.auv_data[0]) > 0 and len(self.auv_data[1]) > 0:
            self.draw_auv_path()

        print("[MAP] Updated origin to UTM coordinates (" + str(x) + ", " + str(y) + ").")

    def on_move(self, mouse):
        """ Moves the map on drag """
        if self.mouse_pressing == True and mouse.xdata != None and mouse.ydata != None:
            x_delta = (self.press_position[0] - mouse.xdata) / 6
            y_delta = (self.press_position[1] - mouse.ydata) / 6
            lim = [self.map.get_xlim(), self.map.get_ylim()]

            self.map.set_xlim(lim[0][0] + x_delta, lim[0][1] + x_delta)
            self.map.set_ylim(lim[1][0] + y_delta, lim[1][1] + y_delta)

            self.draw_canvas()

    # def redraw_waypoints(self):
    #     """ Undraws waypoint and redraws a waypoint """
    #     self.undraw_waypoints()
    #     for waypoint in self.waypoints:
    #         # Draw waypoint again.
    #         waypoint[3] = self.map.plot(
    #             waypoint[0], waypoint[1], marker='o', markersize=5, color="red"),
    #         waypoint[4] = self.map.annotate(xy=(waypoint[0], waypoint[1]), s=waypoint[2] + ", UTM: (" +
    #                                         str(round(waypoint[0]+self.zero_offset_x, 5))+","+str(round(waypoint[1]+self.zero_offset_y, 5))+")")

        # Redraw canvas.
        self.draw_canvas()
        print("[MAP] Waypoints Redrawn!")

    def on_press(self, mouse):
        """ Gets the (x,y) position of map on click """
        self.press_position = [mouse.xdata, mouse.ydata]
        self.mouse_pressing = True

    def on_release(self, mouse):
        """ gets map data if mouse was not dragged """
        self.mouse_pressing = False
        # Ensuring we didnt drag mouse in x.
        if mouse.xdata != None and mouse.xdata - self.press_position[0] == 0:
            # Ensuring we didnt drag mouse in y.
            if mouse.ydata != None and mouse.ydata - self.press_position[1] == 0:
                self.on_map_click(mouse)

    def on_map_click(self, mouse):
        if mouse.button == 1:  # 1 => Left mouse click
            self.new_waypoint_prompt(mouse.xdata, mouse.ydata)
        if mouse.button == 3:  # 3 => Right mouse click
            self.try_remove_waypoint(mouse.xdata, mouse.ydata)

    def update_boat_position(self, x=0, y=0):
        return

    def try_remove_waypoint(self, x=0, y=0):
        close = CLOSE_ENOUGH * (self.size / DEFAULT_GRID_SIZE)

        if self.units == METERS:
            close += 100

        for waypoint in self.waypoints:
            # Close enough on x-axis.
            if x - close < waypoint[0] and x + close > waypoint[0]:
                # Close enough on y-axis.
                if y - close < waypoint[1] and y + close > waypoint[1]:
                    self.remove_waypoint_prompt(waypoint)
                    return

    def remove_waypoint_prompt(self, waypoint):
        print("[MAP] Opening remove-waypoint prompt.")
        prompt_window = Toplevel(self.window)
        center_x = ((self.main.root.winfo_x() +
                     self.main.root.winfo_width()) / 2.5)
        center_y = ((self.main.root.winfo_y() +
                     self.main.root.winfo_height()) / 2.5)
        prompt_window.geometry("+%d+%d" % (center_x, center_y))
        prompt_window.resizable(False, False)
        prompt_window.title("Remove Waypoint \"" + str(waypoint[2]) + "\"?")
        prompt_window.wm_attributes('-topmost')
        prompt_submit = Button(prompt_window, text="Yes, I want to remove waypoint \""+str(waypoint[2])+"\"", font=(FONT, FONT_SIZE),
                               command=lambda:
                               [
            self.confirm_remove_waypoint(waypoint),
            prompt_window.destroy()
        ])

        prompt_submit.pack(padx=5, pady=5)
        prompt_window.mainloop()

    def confirm_remove_waypoint(self, waypoint):
        self.waypoints.remove(waypoint)
        waypoint[3].pop(0).remove()
        waypoint[4].remove()
        self.draw_canvas()
        self.main.log("Waypoint \"" + waypoint[2] + "\" removed!")
        return

    def new_waypoint_prompt(self, x=0, y=0):
        print("[MAP] Opening new-waypoint prompt.")
        prompt_window = Toplevel(self.window)
        # Change position of waypoint prompt to cursor position.
        center_x = ((self.main.root.winfo_x() +
                     self.main.root.winfo_width()) / 2.5)
        center_y = ((self.main.root.winfo_y() +
                     self.main.root.winfo_height()) / 2.5)
        prompt_window.geometry("+%d+%d" % (center_x, center_y))

        prompt_window.resizable(False, False)
        prompt_window.title("New Waypoint")
        prompt_window.wm_attributes('-topmost')
        Label(prompt_window, text="Name", font=(FONT, FONT_SIZE)).grid(row=0)
        Label(prompt_window, text="X", font=(FONT, FONT_SIZE)).grid(row=1)
        Label(prompt_window, text="Y", font=(FONT, FONT_SIZE)).grid(row=2)
        prompt_input_name = Entry(prompt_window, bd=5, font=(FONT, FONT_SIZE))
        prompt_input_name.grid(row=0, column=1)
        prompt_input_x = Entry(prompt_window, bd=5, font=(FONT, FONT_SIZE))
        prompt_input_x.grid(row=1, column=1)
        prompt_input_y = Entry(prompt_window, bd=5, font=(FONT, FONT_SIZE))
        prompt_input_y.grid(row=2, column=1)

        prompt_input_name.insert(0, "My waypoint")  # Placeholder for input
        prompt_input_x.insert(0, x)
        prompt_input_y.insert(0, y)
        prompt_submit = Button(prompt_window, text="Save", font=(FONT, FONT_SIZE),
                               command=lambda:  # Runs multiple functions.
                               [
                                   self.add_waypoint(float(prompt_input_x.get()),
                                                     float(
                                                         prompt_input_y.get()),
                                                     str(prompt_input_name.get())),
                                   prompt_window.destroy()
        ])

        prompt_submit.grid(row=3, column=0, padx=5, pady=5)
 #       prompt_window.mainloop();
        print("[MAP] returning from waypoint mainloop")

    def add_auv_data(self, x=0, y=0):
        self.main.log("Adding AUV data at: ("+str(x)+", "+str(y)+").")
        self.auv_data[0].append(x)
        self.auv_data[1].append(y)
        self.draw_auv_path()

    def blinking_dot(self, i=0):
        colors = (AUV_PATH_COLOR, "red")
        self.canvas.itemconfigure(self.auv_path_obj, fill=colors[i])
        self.canvas.after(250, self.auv_path_obj, 1-i)

    def draw_auv_path(self):
        print("[MAP] Drawing (really re-drawing) AUV path.")

        # Completely delete the previous line, if it exists.
        if self.auv_path_obj != None:
            self.auv_path_obj.pop(0).remove()

        # Re-draw the entire line using the newly updated x-values (auv_data[0]) and y-values (auv_data[1])
        self.auv_path_obj = self.map.plot(
            self.auv_data[0]+self.zero_offset_x, self.auv_data[1]+self.zero_offset_y, label="AUV Path", color=AUV_PATH_COLOR)

        # Re-draw the canvas.
        self.draw_canvas()

    # need to see where to put this and what its parameters are
    # def blinking_dot(i=0):
    #     colors = (AUV_PATH_COLOR, "red")
    #     self.canvas.itemconfigure(self.auv_path_obj, fill=colors[i])
    #     self.canvas.after(250, self.auv_path_obj, 1-i)

    def draw_canvas(self):
        return self.canvas.draw()

    def init_canvas(self):
        print("[MAP] Initializing the canvas.")

        # Remove excess borders around figure.
        self.fig.subplots_adjust(
            left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

        # Create a tkinter-usable component.
        canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        canvas.get_tk_widget().pack()
        return canvas

    def init_fig(self):
        print("[MAP] Initializing figure...")
        fig = Figure(figsize=(DEFAULT_FIGURE_SIZE, DEFAULT_FIGURE_SIZE))
        return fig

    def init_map(self):
        print("[MAP] Initializing map...")
        graph = self.fig.add_subplot(111, xmargin=-0.49, ymargin=-0.49)
        graph.grid(b=True, which='major', axis='both')

        graph.spines['left'].set_position(('data', 0))

        # turn off the right spine/ticks
        graph.spines['right'].set_color('none')
        graph.yaxis.tick_left()

        # set the y-spine
        graph.spines['bottom'].set_position(('data', 0))

        # turn off the top spine/ticks
        graph.spines['top'].set_color('none')
        graph.xaxis.tick_bottom()

        graph.set_facecolor(BACKGROUND_COLOR)

        # Setup the Legend
        legend_elements = [Line2D([0], [0], color=AUV_PATH_COLOR, lw=2, label='AUV Path'),
                           scatter([0], [0], marker='o', color=WAYPOINT_COLOR, label='Waypoint')]

        graph.legend(handles=legend_elements,
                     loc='lower right', title="Legend")

        # Change color of minor axis.
        graph.tick_params(axis='x', colors=MINOR_TICK_COLOR)
        graph.tick_params(axis='y', colors=MINOR_TICK_COLOR)

        return graph

    def nav_to_waypoint(self):
        print("[MAP] Opening nav-to-waypoint prompt.")
        prompt_window = Toplevel(self.window)
        # Change position of waypoint prompt to cursor position.
        center_x = ((self.main.root.winfo_x() +
                     self.main.root.winfo_width()) / 2.5)
        center_y = ((self.main.root.winfo_y() +
                     self.main.root.winfo_height()) / 2.5)
        prompt_window.geometry("+%d+%d" % (center_x, center_y))

        prompt_window.resizable(False, False)
        prompt_window.title("Select Waypoint")
        prompt_window.wm_attributes('-topmost')
        Label(prompt_window, text="Waypoint", font=(FONT, FONT_SIZE)).grid(row=1)

        buttonList = list()

        # creates combo box of waypoints
        self.waypoint_list = Combobox(prompt_window, state="readonly", values=self.waypoints, font=(FONT, 20))
        self.waypoint_list.set("Select Waypoint...")

        self.waypoint_list.grid(row=2, column=0, padx=5, pady=5)

        # saves the selected waypoint when save is pressed

        def set_waypoint():
            self.nav_x = self.waypoints[self.waypoint_list.current()][0]
            self.nav_y = self.waypoints[self.waypoint_list.current()][1]
            self.main.log("Selected waypoint: " + str(self.nav_x) + " " + str(self.nav_y))

        # save button that calls set_waypoint()
        prompt_submit = Button(prompt_window, text="Save", font=(FONT, FONT_SIZE),
                               command=lambda:  # Runs multiple functions.
                               [
                                   set_waypoint(),
                                   prompt_window.destroy()
        ])

        prompt_submit.grid(row=3, column=0, padx=5, pady=5)

    def add_waypoint(self, x=0, y=0, label="My Waypoint"):
        # The code below should never fail (that would be a big problem).
        try:
            self.waypoints.append([
                x, y,
                label,
                self.map.plot(x, y, marker='o', markersize=5,
                              color=WAYPOINT_COLOR, label=label),
                self.map.annotate(xy=(x, y), text="AUV")
            ])
        except:
            self.waypoints.append([
                x, y,
                label,
                self.map.plot(x, y, marker='o', markersize=5,
                              color=WAYPOINT_COLOR, label=label),
                self.map.annotate(xy=(x, y), s="AUV")
            ])

        self.draw_canvas()
        return [x, y]

    def zoom_out(self):
        print("[MAP] Zooming out.")
        xlim = self.map.get_xlim()
        ylim = self.map.get_ylim()
        self.size *= ZOOM_SCALAR
        self.set_range(x=[xlim[0]*ZOOM_SCALAR, xlim[1]*ZOOM_SCALAR],
                       y=[ylim[0]*ZOOM_SCALAR, ylim[1]*ZOOM_SCALAR])

    def zoom_in(self):
        print("[MAP] Zooming in.")
        xlim = self.map.get_xlim()
        ylim = self.map.get_ylim()
        self.size /= ZOOM_SCALAR
        self.set_range(x=[xlim[0]/ZOOM_SCALAR, xlim[1]/ZOOM_SCALAR],
                       y=[ylim[0]/ZOOM_SCALAR, ylim[1]/ZOOM_SCALAR])

    def set_range(self, x=[-DEFAULT_GRID_SIZE, DEFAULT_GRID_SIZE], y=[-DEFAULT_GRID_SIZE, DEFAULT_GRID_SIZE]):
        print("[MAP] Changing grid size to x="+str(x)+", and y="+str(y)+".")
        self.map.set_xlim(x)
        self.map.set_ylim(y)
        self.draw_canvas()

    def set_units(self, unit=METERS):
        print("[MAP] Changing units from " + self.units + " to " + unit)
        multiplier = 1

        # Convert KM -> M
        if unit == METERS and self.units == KILOMETERS:
            multiplier = KM_TO_M

        # Convert MI -> M
        if unit == METERS and self.units == MILES:
            multiplier = MI_TO_M

        # Convert KM -> MI
        if unit == MILES and self.units == KILOMETERS:
            multiplier = KM_TO_MI

        # Convert M -> MI
        if unit == MILES and self.units == METERS:
            multiplier = M_TO_MI

        # Convert MI -> KM
        if unit == KILOMETERS and self.units == MILES:
            multiplier = MI_TO_KM

        # Convert M -> KM
        if unit == KILOMETERS and self.units == METERS:
            multiplier = M_TO_KM

        # Apply conversion
        for waypoint in self.waypoints:
            waypoint[0] *= multiplier
            waypoint[1] *= multiplier

        self.size *= multiplier
        self.units = unit
        self.set_range(x=self.size, y=self.size)
        self.draw_canvas()

    def on_close(self):
        self.map.cla()
        self.fig.clf()
        self.window.destroy()
