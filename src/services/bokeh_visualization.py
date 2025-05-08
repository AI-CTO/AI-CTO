"""
Module for the bokeh visualization methods.
"""

#from bokeh.palettes import Set2
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, Range1d, Title, TapTool, OpenURL

#pylint: disable=too-many-locals
def create_scatter_plot(data):
    """Creates a scatter plot based on inputted data.

    Args:
        data (dict): dictionary with the needed data.

    Returns:
        tuple[str, str]: (script, div) tuple for embedding the plot in HTML.
    """
    projects = data["projects"]
    x_values = data["business_novelty"]
    y_values = data["customer_novelty"]
    impact = [i * 5 for i in data["impact"]]  # Scale impact values for bubble size
    project_types = data["project_types"]  # Get project_type from data
    project_ids = data["project_ids"]  # Unique project IDs

    # Include 'project_type' in the ColumnDataSource
    source = ColumnDataSource(data={
        'projects': projects,
        'x_value': x_values,
        'y_value': y_values,
        'impact': impact,
        'project_type': project_types,  # Include project_type
        'project_id': project_ids  # Add project_id to source
    })

    # Define styles for project types
    colors = {"Existing": "#69b8a0"}  # Emerald green for "Existing"
    line_dash_styles = {"Idea": "dashed"}  # Dashed outline for "Idea"

    # Create the figure
    p = figure(
        height=500, width=1500,
        title="Project Portfolio Visualization",
        toolbar_location=None,
        tools="hover,tap",  # Enable hover and tap tools
        tooltips="@projects: (X: @x_value, Y: @y_value, Impact: @impact, Type: @project_type)",
        x_range=Range1d(0, 100),
        y_range=Range1d(0, 100),
        sizing_mode="stretch_width"
    )

    # Customize the title
    title = Title(text="Project Portfolio Visualization", align="left")
    title.text_font_size = '20pt'
    p.title = title

    # Plot points with different styles based on project_type
    for project_type in set(project_types):
        filtered_source = ColumnDataSource({
            k: [v[i] for i in range(len(projects)) if project_types[i] == project_type]
            for k, v in source.data.items()
        })

        if project_type == "Existing":
            # Solid emerald green circles for "Existing"
            p.scatter(
                x="x_value", y="y_value", size="impact",
                color=colors["Existing"], alpha=0.8, source=filtered_source,
                legend_label=project_type
            )
        elif project_type == "Idea":
            # Hollow circles with dashed outline for "Idea"
            p.circle(
                x="x_value", y="y_value", size="impact",
                line_color="black", fill_color=None, line_dash=line_dash_styles["Idea"],
                line_width=2, alpha=0.8, source=filtered_source,
                legend_label=project_type
            )

    # Set up the TapTool callback
    taptool = p.select(type=TapTool)
    taptool.callback = OpenURL(url="update_project?id=@project_id")

    # Apply lighter, modern theme styling
    p.background_fill_color = "#f9f9f9"
    p.border_fill_color = "#f9f9f9"
    p.outline_line_color = "#e0e0e0"
    p.xgrid.grid_line_color = "#dddddd"
    p.ygrid.grid_line_color = "#dddddd"
    p.xaxis.axis_label = "Business Novelty"
    p.yaxis.axis_label = "Customer Novelty"
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"

    script, div = components(p)
    return script, div
