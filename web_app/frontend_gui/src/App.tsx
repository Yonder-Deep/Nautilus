import React, { useEffect, useState, useRef } from "react";
import { ParametersForm, MotorTestForm, HeadingTestForm, StartMission } from "./inputs/Forms.js";
import { StatusItem, StatusMessages } from "./outputs/status.js";

const Graph = () => {
    return (
        <div className="graph">
            <h3>Graph Placeholder</h3>
        </div>
    )
}

interface socketEvent extends Event {
    data: string
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

    const handleSocketData = (event: MessageEvent<string>) => {
        console.log("Socket data arrived: " + event.data);
        setStatusMessages((prev: any)  => [...prev, event.data]);
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
					<div>
						<Graph></Graph>
					</div>
					<div>
						<Graph></Graph>
					</div>
					<div>
						<Graph></Graph>
					</div>
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
