from bokeh.palettes import HighContrast3
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource

def create_scatter_plot(data):
    # project data
    #projects = data["projects"]
    print(data)
    
    business_novelty = data["business_novelty"]
    customer_novelty = data["customer_novelty"]
    impact = 50

    source = ColumnDataSource(data=data)


   


    p = figure(height=350, title="Project Portfolio Visualization", toolbar_location=None, tools="hover", tooltips="@projects: Business Novelty: @business_novelty, Customer Novelty: @customer_novelty, Impact: @impact")


    p.scatter(x="business_novelty", y="customer_novelty", size="impact", color=HighContrast3[0], alpha=0.6, source=source)


    p.xaxis.axis_label = "Business Novelty"
    p.yaxis.axis_label = "Customer Novelty"
    p.y_range.start = 0
    p.x_range.start = 0
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"

    # Return script and div to embed in the HTML template
    script, div = components(p)
    return script, div