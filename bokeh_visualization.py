from bokeh.palettes import Set2
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource

def create_scatter_plot(data):
    projects = data["projects"]
    x_values = data["x_value"]  
    y_values = data["y_value"]  
    categories = data.get("categories", ["Existing"] * len(projects))  

    source = ColumnDataSource(data={
        'projects': projects,
        'x_value': x_values,
        'y_value': y_values,
        'categories': categories,
    })

    p = figure(
        height=420, width=420,
        title="Project Portfolio Visualization",
        toolbar_location=None,
        match_aspect=True,
        tools="hover",
        tooltips="@projects: (X: @x_value, Y: @y_value)"
    )

    colors = {"Existing": Set2[3][0], "Idea": Set2[3][1]}  

    for category, color in colors.items():
        filtered_source = ColumnDataSource({
            k: [v[i] for i in range(len(projects)) if categories[i] == category] 
            for k, v in source.data.items()
        })
        p.scatter(
            x="x_value", y="y_value", size=10,  
            color=color, alpha=0.7, source=filtered_source, legend_label=category
        )

    p.background_fill_color = None
    p.border_fill_color = None
    p.outline_line_color = None
    p.grid.visible = False
    p.xaxis.axis_label = "Business Novelty"
    p.yaxis.axis_label = "Customer Novelty"
    p.axis.minor_tick_line_color = None
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"

    p.legend.visible = False
    
    script, div = components(p)
    return script, div
