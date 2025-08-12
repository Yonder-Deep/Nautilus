export interface Command {
    command: string
    content: any
    ack?: boolean
}

export const isCommand = (obj: any): obj is Command => {
    return (
        typeof obj === 'object' &&
        obj !== null &&
        typeof obj.command === 'string' &&
        typeof obj.content === 'number'
    )
}

export interface State {
    position: number[]
    velocity: number[]
    attitude: number[]
    angular_velocity: number[]
}

const isNumberArray = (value: any): value is number[] => {
    return Array.isArray(value) && value.every((item) => typeof item === "number");
}

export const isState = (obj: any): obj is State => {
    return (
        typeof obj === 'object' &&
        obj !== null &&
        isNumberArray(obj.position) &&
        isNumberArray(obj.velocity) &&
        isNumberArray(obj.attitude) &&
        isNumberArray(obj.angular_velocity) //&&
    )
}

export type Status = "unknown" | "active" | "inactive";

export interface Tasks {
    "Localization": Status,
    "Perception": Status,
    "Control": Status,
    "Navigation": Status,
}

export interface Data {
    source: string
    type: string
    content: Tasks | State | string
} 

export const isData = (obj: any): obj is Data => {
    return (
        typeof obj === 'object' &&
        obj !== null &&
        typeof obj.source === 'string' &&
        typeof obj.type === 'string' &&
        (typeof obj.content === 'object' || typeof obj.content === 'string')
    )
}
