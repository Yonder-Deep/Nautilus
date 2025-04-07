import React, { useEffect, useState, useRef } from "react";
import { ParametersForm, MotorTestForm, HeadingTestForm, StartMission } from "./inputs/Forms";
import { StatusItem, StatusMessages } from "./outputs/status";
import { Simulation } from "./outputs/sim";
import { Map } from "./outputs/map"
import {
    Command,
    isCommand,
    State,
    isState,
    Data,
    isData
} from "./types"

import "../public/leaflet.css"

const Graph = () => {
    return (
        <div className="graph">
            <h3>Graph Placeholder</h3>
        </div>
    )
}

const tryJson = (raw: string): any => {
    try {
        return JSON.parse(raw)
    }
    catch {
        return undefined
    }
}

export default function App() {
    // These are the only state variables that need full scope
    const [imuData, setImuData] = useState([
        { title: 'Magnetometer', value: '', id: 1 },
        { title: 'Accelerometer', value: '', id: 2 },
        { title: 'Gyroscope', value: '', id: 3 }
    ]);
    const [insData, setInsData] = useState([
        { title: 'Heading', value: '', id: 1 },
        { title: 'Roll', value: '', id: 2 },
        { title: 'Pitch', value: '', id: 3 }
    ]);
    const [websocket, setWebsocket]: any = useState(undefined);
	const [statusMessages, setStatusMessages]: any = useState([]);
    const [attitude, setAttitude] = useState<number[]>([0,0,0,0]);

    const handleSocketData = (event: MessageEvent<string>) => {
        //console.log("Socket data arrived: " + event.data);
        const data: Command | Data = tryJson(event.data)
        if (isData(data)) {
            const state = data.content;
            if(isState(state)) {
                setAttitude(state.attitude)
            }
        } else {
            setStatusMessages((prev: any)  => [...prev, event.data]);
        }
    }

    // Register socket handler for server-sent data
    const connection: any = useRef(null);
    useEffect(() => {
        const socket: WebSocket = new WebSocket("/api/websocket");

        socket.addEventListener("open", () => setWebsocket(socket));
        socket.addEventListener("message", handleSocketData);

        connection.current = socket;

        return () => connection.current.close();
    }, [useState]);

    return (
        <div className = "parent-container">
			<div className="main-section">
				<h1>Testing and Calibration</h1>
				<div className="upper-section">
                    <Simulation quat={attitude}></Simulation>
                    <Map coordinates={[]}></Map>
				</div>
				<div className="lower-section">
					<div className="status-section">							
						<StatusItem statusType="IMU Status" statusData={imuData}></StatusItem>
						<StatusItem statusType="INS Status" statusData={insData}></StatusItem>
					</div>
					<div className="testing-section">
						<ParametersForm websocket={websocket}></ParametersForm>
						<MotorTestForm websocket={websocket}></MotorTestForm>
                        <div>
                            <HeadingTestForm websocket={websocket}></HeadingTestForm>
                            <StartMission websocket={websocket}></StartMission>
                        </div>
					</div>
				</div>
			</div>
			<StatusMessages statusMessages={statusMessages} setStatusMessages={ setStatusMessages}></StatusMessages>
        </div>
    );
}
