import pandas as pd
import plotly.express as px


def generate_chart(missing_links, negative_float, high_float, source_name):
    """Generate a chart from validation counts."""

    chart_data = pd.DataFrame({
        "Category": [
            "Missing Links",
            "Negative Float",
            "High Float"
        ],
        "Count": [
            missing_links,
            negative_float,
            high_float
        ]
    })

    fig = px.bar(
        chart_data,
        x="Category",
        y="Count",
        title=f"Schedule Validation Results - {source_name}",
        text="Count"
    )

    fig.update_layout(
        xaxis_title="Validation Category",
        yaxis_title="Number of Findings",
        showlegend=False
    )

    fig.show()