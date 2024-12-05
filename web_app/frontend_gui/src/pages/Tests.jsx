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

const StatusMessages = ({ statusMessages }) => {
    const messagesBottomRef = useRef(null);

    const scrollToMessagesBottom = () => {
        messagesBottomRef.current?.scrollIntoView({ behavior: "smooth" });
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
	const [statusMessages, setStatusMessages] = useState([]);

    // Handle all POST requests to set PID or run tests
    const handlePostRequest = async (url, data) => {
        console.log("Attempting post of data: " + JSON.stringify(data));
        try {
            const response = await fetch("http://localhost:6543/api/" + url, {
                method: 'POST',
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
            console.log("Response: " + response.data);
        } catch (error) {
            console.error('Error posting data:', error);
        }
    };

    const handleSocketData = (event) => {
        console.log("Socket data arrived: " + event.data)
        setStatusMessages(statusMessages => [...statusMessages, event.data]);
    }

    // Register socket handlers for server-sent data
    const connection = useRef(null);
    useEffect(() => {
        const socket = new WebSocket("/api/websocket");

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
						<ParametersForm handlePostRequest={handlePostRequest}></ParametersForm>
						<MotorTestForm handlePostRequest={handlePostRequest}></MotorTestForm>
						<HeadingTestForm handlePostRequest={handlePostRequest}></HeadingTestForm>
					</div>
				</div>
			</div>
			<StatusMessages statusMessages={statusMessages}></StatusMessages>
        </div>
    );
}
