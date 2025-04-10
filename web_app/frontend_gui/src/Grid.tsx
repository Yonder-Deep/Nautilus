import React, { useState } from 'react';
import { Responsive, WidthProvider} from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css'; // Import resizable styles
import { ParametersForm } from './inputs/Forms';

const ResponsiveGridLayout = WidthProvider(Responsive);

export const Grid = ({
    children,
    enabled,
}:{
    children: any, // TODO: Figure out typing for react children of children
    enabled: boolean
    }) => {
    const [layout, setLayout] = useState<{}>();

    return (
        <ResponsiveGridLayout
            className="layout"
            layouts={layout}
            draggableHandle=".drag-handle"
            isDraggable={enabled}
            isResizable={enabled}
            // The breakpoints & cols chosen for 50px increments
            breakpoints={{ lg: 1200, md: 700, sm:500, xs:200, xxs:0 }}
            cols={{ lg: 20, md: 14, sm: 10, xs: 4, xxs: 2 }}
            rowHeight={50}
            resizeHandles={['s', 'w', 'e', 'n', 'sw', 'nw', 'se', 'ne']}
        >
            {React.Children.map(children, (child, index) => {
                if (child.props.coordinates) {
                    return (
                    <div key={index} data-grid={{ w:2, h:2, x:0, y:0, minW:2, minH:2 }}>
                        <div className="drag-handle map-handle"/>
                        {child}
                    </div>
                    )
                }
                return (
                    <div key={index} data-grid={{ w:2, h:2, x:0, y:0, minW:2, minH:2 }} className="drag-handle">
                        {child}
                    </div>
                )
            })}
            {children}
        </ResponsiveGridLayout>
    );
};

