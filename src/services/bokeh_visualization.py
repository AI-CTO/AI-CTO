from bokeh.palettes import Set2
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, Range1d, Title, Label

def create_scatter_plot(data):
    projects = data["projects"]
    x_values = data["business_novelty"]  
    y_values = data["customer_novelty"]
    impact = [i * 5 for i in data["impact"]]  # scales impact values to make the bubbles larger and easier to see  
    categories = data.get("categories", ["Existing"] * len(projects))  

    source = ColumnDataSource(data={
        'projects': projects,
        'x_value': x_values,
        'y_value': y_values,
        'impact': impact,
        'categories': categories,
    })

    p = figure(
        height=500, width=1500,
        title="Project Portfolio Visualization",
        toolbar_location=None,
        match_aspect=False,
        tools="hover",
        tooltips="@projects: (X: @x_value, Y: @y_value, Impact: @impact)",
        x_range=Range1d(0, 100),  # Set x-axis range
        y_range=Range1d(0, 100),  # Set y-axis range
        sizing_mode="stretch_width"
    )

    # Customize the title
    title = Title(text="Project Portfolio Visualization", align="left")
    title.text_font_size = '20pt' 
    title.text_font = "helvetica"
    title.text_color = "#333333"  # Dark text for title to stand out on white background
    p.title = title

    # Define colors for categories
    colors = {"Existing": Set2[3][0], "Idea": Set2[3][1]}  

    for category, color in colors.items():
        filtered_source = ColumnDataSource({
            k: [v[i] for i in range(len(projects)) if categories[i] == category] 
            for k, v in source.data.items()
        })
        p.scatter(
            x="x_value", y="y_value", size="impact",  
            color=color, alpha=0.8, source=filtered_source, legend_label=category
        )

    # Apply lighter, modern theme styling
    p.background_fill_color = "#f9f9f9"  # White background to complement page
    p.border_fill_color = "#f9f9f9"  # Light gray border for a clean look
    p.outline_line_color = "#e0e0e0"  # Very light gray outline to keep it soft

    # Customize grid lines for visibility on white background
    p.xgrid.grid_line_color = "#dddddd"  # Very light gray grid lines for contrast
    p.ygrid.grid_line_color = "#dddddd"
    p.xgrid.grid_line_alpha = 0.5  # Light transparency
    p.ygrid.grid_line_alpha = 0.5
    p.xgrid.grid_line_dash = [6, 4]  # Dashed grid lines
    p.ygrid.grid_line_dash = [6, 4]

    # Customize axes for a modern, clean look
    p.xaxis.axis_label = "Business Novelty"
    p.yaxis.axis_label = "Customer Novelty"
    p.xaxis.axis_label_text_color = "#555555"  # Dark gray axis labels for contrast
    p.yaxis.axis_label_text_color = "#555555"
    p.xaxis.major_label_text_color = "#666666"  # Subtle gray tick labels
    p.yaxis.major_label_text_color = "#666666"
    p.xaxis.axis_line_color = "#cccccc"  # Light gray axis lines
    p.yaxis.axis_line_color = "#cccccc"
    p.xaxis.major_tick_line_color = "#cccccc"  # Light gray ticks
    p.yaxis.major_tick_line_color = "#cccccc"
    p.axis.minor_tick_line_color = "#bbbbbb"  # Even lighter minor ticks

    # Customize legend for a refined look
    p.legend.label_text_color = "#333333"  # Dark legend text for clarity
    p.legend.background_fill_color = "#f9f9f9"  # Very light background for legend
    p.legend.border_line_color = "#e0e0e0"  # Soft light border for the legend
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"
    p.legend.visible = True

    script, div = components(p)
    return script, div
