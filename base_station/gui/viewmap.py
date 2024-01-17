import tkinter
import tkintermapview


class ViewMap:
    #    """ Map class creates a map of the position of the AUV """

    def __init__(self, window, main, guimap):
        """Initialize Class variables"""
        # Define the window.
        self.window = window
        self.main = main
        self.guimap = guimap
        self.zoom_factor = 15

        self.map_widget = tkintermapview.TkinterMapView(
            self.window, width=800, height=600, corner_radius=0
        )
        self.map_widget.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        self.map_widget.set_zoom(self.zoom_factor)
        self.map_widget.add_right_click_menu_command(
            label="Add Marker", command=self.add_marker_event, pass_coords=True
        )
        # self.path = self.map_widget.set_path()

    def zoom_out(self):
        print("[VIEWMAP] Zooming out.")
        if self.zoom_factor > 0:
            self.zoom_factor -= 1
        self.map_widget.set_zoom(self.zoom_factor)

    def zoom_in(self):
        print("[VIEwMAP] Zooming in.")
        if self.zoom_factor < 19:
            self.zoom_factor += 1
        self.map_widget.set_zoom(self.zoom_factor)

    def input_gps_coordinates(self, latitude, longitude, name):
        new_marker = self.map_widget.set_position(latitude, longitude, marker=True)
        new_marker.set_text(name)

    def set_base_station_position(self, latitude, longitude):
        self.base_station_marker = self.map_widget.set_position(
            latitude, longitude, marker=True
        )
        self.base_station_marker.set_text("Base Station")

    def add_marker_event(self, coords):
        print("Add marker:", coords)
        self.new_marker = self.map_widget.set_marker(
            coords[0], coords[1], text="new marker"
        )


# root = tkinter.Tk()
# root.geometry(f"{800}x{600}")
# root.title("viewmap.py")


# set current widget position and zoom
# map_widget.set_position(48.860381, 2.338594)  # Paris, France
# map_widget.set_zoom(15)

# set current widget position by address
# map_widget.set_address("colosseo, rome, italy")
