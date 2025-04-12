import { useEffect, useRef } from "react"
import * as L from "leaflet"
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet"
import "../../public/leaflet.css"

export const Map = ({ coordinates } : { coordinates: number[][]}) => {
    const center = L.latLng(32.865249, -117.243515);
    const zoom = 13

    return (
        <>
            <h2 className="drag-handle" style={{height: "2rem"}}>Map</h2>
            <MapContainer   className="map"
                            center={center}
                            zoom={zoom}>
                <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <Marker position={center}>
                    <Popup>Origin</Popup>
                </Marker>
            </MapContainer>
        </>
    )
}
