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
    title.text_color = "#ffffff"  # White title text
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
            color=color, alpha=0.7, source=filtered_source, legend_label=category
        )

    # Apply dark theme styling
    p.background_fill_color = "#2e2e2e"  # Dark background
    p.border_fill_color = "#2e2e2e"
    p.outline_line_color = "#444444"  # Outline color

    # Customize grid lines
    p.xgrid.grid_line_color = "#444444"  # Dark gray grid lines
    p.ygrid.grid_line_color = "#444444"
    p.xgrid.grid_line_alpha = 0.6       # Slight transparency
    p.ygrid.grid_line_alpha = 0.6
    p.xgrid.grid_line_dash = [6, 4]     # Dashed grid lines
    p.ygrid.grid_line_dash = [6, 4]

    # Customize axes
    p.xaxis.axis_label = "Business Novelty"
    p.yaxis.axis_label = "Customer Novelty"
    p.xaxis.axis_label_text_color = "#ffffff"  # White axis labels
    p.yaxis.axis_label_text_color = "#ffffff"
    p.xaxis.major_label_text_color = "#cccccc"  # Light gray tick labels
    p.yaxis.major_label_text_color = "#cccccc"
    p.xaxis.axis_line_color = "#888888"  # Light gray axis lines
    p.yaxis.axis_line_color = "#888888"
    p.xaxis.major_tick_line_color = "#888888"  # Light gray ticks
    p.yaxis.major_tick_line_color = "#888888"
    p.axis.minor_tick_line_color = "#555555"  # Darker gray minor ticks

    # Customize legend
    p.legend.label_text_color = "#ffffff"  # White legend text
    p.legend.background_fill_color = "#444444"  # Dark gray legend background
    p.legend.border_line_color = "#888888"  # Light gray legend border
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"
    p.legend.visible = True

    script, div = components(p)
    return script, div
