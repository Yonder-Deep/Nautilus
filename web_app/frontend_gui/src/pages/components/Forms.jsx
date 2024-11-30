import React, { useState } from 'react';

export const ParametersForm = ({ handlePostRequest }) => {
    const [axis, setAxis] = useState('');
    const [constantP, setConstantP] = useState('');
    const [constantI, setConstantI] = useState('');
    const [constantD, setConstantD] = useState('');
    const createPIDRequest = () => {
        const pidConstants = {
            p: '' + constantP.target.value,
            i: '' + constantI.target.value,
            d: '' + constantD.target.value
        };
        handlePostRequest(axis.target.value.toLowerCase() + '_pid_constants', pidConstants);
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
                <button onClick={() => createPIDRequest()}>Set Constants</button>
            </div>
        </div>
    )
}

export const MotorTestForm = ({ handlePostRequest }) => {
    const [motorType, setMotorType] = useState('');
    const [motorSpeed, setMotorSpeed] = useState('');
    const [motorDuration, setMotorDuration] = useState('');
    const createMotorTest = () => {
        const motorTest = {
            motor: '' + motorType.target.value,
            speed: '' + motorSpeed.target.value,
            duration: '' + motorDuration.target.value
        };
        handlePostRequest('motor_test', motorTest);
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
                <button onClick={() => createMotorTest()}>Begin Test</button>
            </div>
        </div>
    )
}

export const HeadingTestForm = ({ handlePostRequest }) => {
    const [targetHeading, setTargetHeading] = useState('');

    return (
        <div className="testing-form">
            <h2>Heading Test</h2>
            <div className="form-body">
                <input placeholder="Enter target heading" onChange={e => (setTargetHeading(e))} />
                <button onClick={() => handlePostRequest('heading_test', { heading: targetHeading.target.value })}>Begin Test</button>
            </div>
        </div>
    )
}
