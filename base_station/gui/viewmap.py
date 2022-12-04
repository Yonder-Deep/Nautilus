import tkinter
import tkintermapview


class ViewMap:
    #    """ Map class creates a map of the position of the AUV """

    def __init__(self,  window, main, guimap):
        """ Initialize Class variables """
        # Define the window.
        self.window = window
        self.main = main
        self.guimap = guimap

        map_widget = tkintermapview.TkinterMapView(self.window, width=800, height=600, corner_radius=0)
        map_widget.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        # map_widget.pack()


#root = tkinter.Tk()
# root.geometry(f"{800}x{600}")
# root.title("viewmap.py")


# set current widget position and zoom
# map_widget.set_position(48.860381, 2.338594)  # Paris, France
# map_widget.set_zoom(15)

# set current widget position by address
#map_widget.set_address("colosseo, rome, italy")
