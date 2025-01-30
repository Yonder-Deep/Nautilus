import React, { useState } from 'react';

export const ParametersForm = ({ websocket }) => {
    const [axis, setAxis] = useState('');
    const [constantP, setConstantP] = useState('');
    const [constantI, setConstantI] = useState('');
    const [constantD, setConstantD] = useState('');
    const makePidRequest = () => {
        if (!axis || !constantP || !constantI || !constantD) { return; }
        const pidConstants = {
            axis: '' + axis,
            p: '' + constantP.target.value,
            i: '' + constantI.target.value,
            d: '' + constantD.target.value
        };
        const request = {
            command: "pidConstants",
            content: pidConstants
        };
        websocket.send(JSON.stringify(request));
    }

    return (
        <div className="parameters-form">
            <h2>Set PID Constants</h2>
            <div className="form-body">
                <select defaultValue={"Default"} onChange={e => setAxis(e)}>
                    <option value="Default" disabled>Select Axis</option>
                    <option value="Pitch">Pitch</option>
                    <option value="Yaw">Yaw</option>
                    <option value="Roll">Roll</option>
                </select>
                <input placeholder="P" onChange={e => setConstantP(e)} />
                <input placeholder="I" onChange={e => setConstantI(e)} />
                <input placeholder="D" onChange={e => setConstantD(e)} />
                <button onClick={() => makePidRequest()}>Set Constants</button>
            </div>
        </div>
    )
}

export const MotorTestForm = ({ websocket }) => {
    const [motorType, setMotorType] = useState('');
    const [motorSpeed, setMotorSpeed] = useState('');
    const [motorDuration, setMotorDuration] = useState('');
    const makeMotorRequest = () => {
        console.log("Making motor request.")
        const motorTest = {
            motor: '' + motorType.target.value,
            speed: '' + motorSpeed.target.value,
            duration: '' + motorDuration.target.value
        };
        const request = {
            command: "motorTest",
            content: motorTest
        };
        websocket.send(JSON.stringify(request));
    }

    return (
        <div className="motor-form">
            <h2>Motor Testing</h2>
            <div className="form-body">
                <select defaultValue={"Default"} onChange={e => setMotorType(e)}>
                    <option value="Default" disabled>Select Motor</option>
                    <option value="Forward">Forward</option>
                    <option value="Backward">Backward</option>
                    <option value="Down">Down</option>
                    <option value="Left">Left</option>
                    <option value="Right">Right</option>
                </select>
                <input placeholder="Enter motor speed" onChange={e => setMotorSpeed(e)} />
                <input placeholder="Enter duration of run" onChange={e => setMotorDuration(e)} />
                <button onClick={() => makeMotorRequest()}>Begin Test</button>
            </div>
        </div>
    )
}

export const HeadingTestForm = ({ websocket }) => {
    const [targetHeading, setTargetHeading] = useState('');
    const headingRequest = () => {
        console.log("Making heading request.")
        const headingTest = {
            heading: targetHeading
        }
        const request = {
            command: "headingTest",
            content: headingTest
        };
        websocket.send(JSON.stringify(request));
    }

    return (
        <div className="testing-form">
            <h2>Heading Test</h2>
            <div className="form-body">
                <input placeholder="Enter target heading" onChange={e => (setTargetHeading(e))} />
                <button onClick={() => headingRequest()}>Begin Test</button>
            </div>
        </div>
    )
}
