# React Frontend for Nautilus AUV
## Basic Map of Codebase:
* `src/` holds all the of the React and typescript source files and the associated css styles
* Within `src/`, entrypoint is `index.tsx`, main file is `App.tsx`, dashboard grid layout is `Grid.tsx`, `inputs/` is for user inputs, `outputs/` is for data outputs, `utils/` for miscellaneous other stuff
* `public/` holds assets like icons and fonts
* Building with `npm run build` will output into and clear existing files in `dist/`
* Entrypoint is obviously the `index.html`

## General Info:
* A local websocket to the FastAPI server is made and managed from the top level `App.tsx`, and any data put into it will go through the server and end up in the `queue_to_auv` FIFO queue in the `__init__.py` of the auv code. This is how most of the communication is done.
* There are also simple fetch requests to the FastAPI server to manage the grid layout and persist it to json.

## *Relatively* minimal npm packages:
* Built using Vite, which means you can get HMR if you run `npm run dev` from this directory. Also using `react-scan` so you can inspect React rendering when in dev mode.
* No component library, all custom CSS
* Obviously `react` and `react-dom`
* `three` and `@react-three/fiber` for the 3D model
* `leaflet` for the map
* `vite` for the build system
* `react-grid-layout` for the heavy lifting on the grid dashboard
* `typescript` and all the associated `@types/*` libraries for everything else
