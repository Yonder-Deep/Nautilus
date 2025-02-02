import React, { useEffect, useState, useRef } from "react";
import { ParametersForm, MotorTestForm, HeadingTestForm } from "./components/Forms.jsx";

const Graph = () => {
    return (
        <div className="graph">
            <h3>Graph Placeholder</h3>
        </div>
    )
}

const StatusItem = ({ statusType, statusData }) => {
    const statusListItems = statusData.map(dataPart =>
        <li key={dataPart.id}>{dataPart.title}: {dataPart.value}</li>
    )

    return (
        <div className="status-item">
            <h2>{statusType}</h2>
            <ul>{statusListItems}</ul>
        </div>
    )
}

const StatusMessages = ({ statusMessages, setStatusMessages }) => {
    const messagesBottomRef = useRef(null);

    const scrollToMessagesBottom = () => {
        messagesBottomRef.current?.scrollIntoView({ behavior: "smooth" });
    };
	const clearMessages = () => {
		setStatusMessages([]);
	};

    useEffect(() => {
        scrollToMessagesBottom()
    }, [statusMessages]);

	return (
		<div className="status-messages-container">
			<h2>Status Messages</h2>
			<ul className="status-messages">
				{statusMessages.map((message, index) => (
				<li key={index}>{message}</li>
			    ))}
                <div ref={messagesBottomRef}></div>
			</ul>
			<div className="status-messages-bottom-bar">
				<button onClick={() => clearMessages()}>Clear Output</button>
			</div>
		</div>
	)
}

export default function Tests() {
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
    const [websocket, setWebsocket] = useState(null);
	const [statusMessages, setStatusMessages] = useState([]);

    const handleSocketData = (event) => {
        console.log("Socket data arrived: " + event.data)
        setStatusMessages(statusMessages => [...statusMessages, event.data]);
    }

    // Register socket handler for server-sent data
    const connection = useRef(null);
    useEffect(() => {
        const socket = new WebSocket("/api/websocket");

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
						<HeadingTestForm websocket={websocket}></HeadingTestForm>
					</div>
				</div>
			</div>
			<StatusMessages statusMessages={statusMessages} setStatusMessages={ setStatusMessages}></StatusMessages>
        </div>
    );
}
