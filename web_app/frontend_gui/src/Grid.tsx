import React from 'react';
import { Responsive, WidthProvider, Layout, Layouts } from 'react-grid-layout';

// Import resizable styles
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

export const Grid = ({
    children,
    enabled,
    layouts,
    setLayouts,
}:{
        children: any, // TODO: Figure out typing for react children of children
        enabled: boolean,
        layouts: Layouts | undefined,
        setLayouts: React.Dispatch<React.SetStateAction<Layouts | undefined>>
    }) => {

    return (
        <ResponsiveGridLayout
            className="layout"
            layouts={layouts}
            onLayoutChange={(_currentLayout: Layout[], allLayouts: Layouts) => {
                setLayouts(allLayouts);
            }}
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
                    /** The only one w/ coordinates as props is the map
                      * The map needs to have a defined separate handle to allow
                      * for movement dragging to conflict with map dragging
                      * The extra class "map-flex-fix" is for the map to expand correctly
                     **/
                    return (
                        <div key={index} className="map-holder">
                            {child}
                        </div>
                    )
                }
                return (
                    <div key={index} className="drag-handle">
                        {child}
                    </div>
                )
            })}
            {children}
        </ResponsiveGridLayout>
    );
};

