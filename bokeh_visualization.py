from bokeh.palettes import Set2
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource

def create_scatter_plot(data):
    projects = data["projects"]
    business_novelty = data["business_novelty"]
    customer_novelty = data["customer_novelty"]
    impact = data["impact"]
    categories = data.get("categories", ["Existing"] * len(projects))  # Default category is 'Existing'

    # Scale impact values by 10
    scaled_impact = [i * 10 for i in impact]

    source = ColumnDataSource(data={
        'projects': projects,
        'business_novelty': business_novelty,
        'customer_novelty': customer_novelty,
        'impact': scaled_impact,
        'categories': categories,
    })

    p = figure(
        height=420, width=420,
        title="Project Portfolio Visualization",
        toolbar_location=None,
        match_aspect=True,
        tools="hover",
        tooltips="@projects: (Business Novelty: @business_novelty, Customer Novelty: @customer_novelty, Impact: @impact)"
    )

    colors = {"Existing": Set2[3][0], "Idea": Set2[3][1]}  # Color mapping for categories

    for category, color in colors.items():
        filtered_source = ColumnDataSource({k: [v[i] for i in range(len(projects)) if categories[i] == category] for k, v in source.data.items()})
        p.scatter(
            x="business_novelty", y="customer_novelty", size="impact",
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

    # Hide the legend until the color mapping is implemented
    p.legend.visible = False
    
    # Return script and div to embed in the HTML template
    script, div = components(p)
    return script, div
