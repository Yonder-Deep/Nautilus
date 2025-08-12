import { useRef, useState, useEffect } from "react";
import {
    Canvas,
    useFrame
} from "@react-three/fiber"
import * as THREE from "three"

THREE.Object3D.DEFAULT_UP.set(0, 0, 1);

const Mesh = ({euler}: {euler: number[]}) => {
    const eulerAngles = new THREE.Euler()
    let meshRef = useRef<THREE.Mesh>(null!);

    useEffect(() => {
        eulerAngles.set(euler[0], euler[1], euler[2], "ZYX");
        console.log("Euler Angles: " + JSON.stringify(euler));
    }, [euler])

    useFrame(() => {
        const [z, y, x] = eulerAngles.toArray();
        meshRef.current.rotation.set(x, y, z);
    })

    return (
        <mesh ref={meshRef}>
            <boxGeometry args={[2,2,4]}/>
            <meshStandardMaterial />
        </mesh>
    )
}

export const Simulation = ({euler}: {euler: number[]}) => {

    return (
        <>
            <h2>Visualization</h2>
            <Canvas frameloop="demand" camera={{rotation: [0, -0.25, Math.PI/2] ,position: [-2,0,6]}}>
                <Mesh euler={euler}></Mesh>
                <ambientLight intensity={0.1} />
                <directionalLight position={[0, 0, 5]} color="red" />
                <axesHelper position={[2, 0, 0]}/>
            </Canvas>
        </>
    )
}
