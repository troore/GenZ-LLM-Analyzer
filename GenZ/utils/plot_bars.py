# Example data (replace with your actual data)
categories = ['Category A', 'Category B', 'Category C']
group1_values = [10, 15, 8]
group2_values = [12, 18, 6]
group3_values = [12, 18, 6]
group4_values = [12, 18, 6]

import matplotlib.pyplot as plt
import numpy as np

def plot_grouped_bars(title: str,
                      xlabel: str, 
                      ylabel: str,
                      categories: list,
                      labels: list,
                      value_groups: list[list], 
                      figure_name: str = "grouped_bar_plot"):

    # Set the width of each bar
    bar_width = 0.2

    # Create an array of indices for the x-axis
    x = np.arange(len(categories))

    # Create a new figure with custom dimensions (width, height in inches)
    plt.figure(figsize=(12, 6))  # Adjust as needed

    # Create the grouped bars
    for i, value_group in enumerate(value_groups):
        offset = bar_width*i-(bar_width/2)*(len(value_groups)-1)
        label = labels[i]
        plt.bar(x + offset, value_group, width=bar_width, label=label)

    # Add values on top of the bars
    for i in range(len(categories)):
        for j, value_group in enumerate(value_groups):
            offset = bar_width*j-(bar_width/2)*(len(value_groups)-1)-0.05
            plt.text(x[i]+offset, value_group[i]+0.5, "{:.3f}".format(value_group[i]))

    # Customize the plot
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(x, categories)
    plt.legend()

    # Save to figure
    plt.tight_layout()
    plt.savefig('{}.png'.format(figure_name))


plot_grouped_bars(title="Grouped Bar Plot",
                  xlabel="Categories",
                  ylabel="Values",
                  categories=categories,
                  labels=['A', 'B', 'C', 'D'],
                  value_groups=[group1_values,
                                group2_values,
                                group3_values,
                                group4_values])
