"""
Provides functions for visualizing apartment data, including 2D scatter plots, 3D scatter plots,
and correlation heatmaps. All plots are saved as SVG files in the configured figures directory.

Functions:
- scatter(df, title, xlabel, ylabel): Generates a 2D scatter plot with a regression line.
- plot3d(df, title, xlabel, ylabel, zlabel, xunit, yunit, zunit): Creates a 3D scatter plot of three variables.
- heatmap(df, title): Builds a heatmap of correlations between price and distances to city centers and landmarks.
"""
import matplotlib.pyplot as plt
import seaborn as sns
from Settings import ENV as PROPERTY
from utils.devtools.multithread_logger import AsyncFileLogger

log = AsyncFileLogger()


def histogram(df, column_label, title, xlabel, ylabel):
    fig, ax = plt.subplots()
    df[column_label].plot(kind="hist", bins=20, ax=ax)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    fig.savefig(f"{PROPERTY['FIGURES_DIR']}/{title}.png", dpi=300, bbox_inches="tight")


def scatter(df, title, xlabel, ylabel):
    """
    Generates a 2D scatter plot with a regression line from the DataFrame.
    Saves the figure as an SVG in the configured figures directory and closes the plot.
    :param df: Pandas DataFrame.
    :param title: Plot title.
    :param xlabel: Plot xlabel.
    :param ylabel: Plot ylabel.
    """
    title = title.replace(' ', '_')
    save_path = f"{PROPERTY["FIGURES_DIR"]}/{title}.svg".lower()
    log.info(f"Building 2D scatter plot: {title} ...")

    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=xlabel, y=ylabel, data=df)
    sns.regplot(x=xlabel, y=ylabel, data=df, scatter=False, color='red', truncate=False)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.ylim(bottom=PROPERTY['MIN_PRICE'])
    plt.tight_layout()
    log.info("2D scatter plot created successfully.")
    log.info(f"Saving 2D scatter plot to {save_path}")
    plt.savefig(save_path)
    log.info(f"2D scatter plot saved to {save_path}")
    print(f"2D scatter plot saved to {save_path}")
    plt.close()


def plot3d(df, title, xlabel, ylabel, zlabel, xunit, yunit, zunit):
    """
    Creates a 3D scatter plot of three variables with axis labels including units.
    Saves the figure as an SVG, displays it, and closes the plot.
    :param df: Pandas DataFrame.
    :param title: Plot title.
    :param xlabel: Plot xlabel.
    :param ylabel: Plot ylabel.
    :param zlabel: Plot zlabel.
    :param xunit: Plot xunit.
    :param yunit: Plot yunit.
    :param zunit: Plot zunit.
    """
    title = title.replace(' ', '_')
    save_path = f"{PROPERTY["FIGURES_DIR"]}/{title}.svg".lower()
    log.info(f"Building 3D scatter plot: {title} ...")

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(df[xlabel], df[ylabel], df[zlabel], c="red", s=20, alpha=0.8)
    ax.set_xlabel(f"{xlabel} {xunit}")
    ax.set_ylabel(f"{ylabel} {yunit}")
    ax.set_zlabel(f"{zlabel} {zunit}")
    plt.title("3D Plot: Price vs Distances")
    log.info("3D scatter plot created successfully.")

    log.info(f"Saving 3D scatter plot to {save_path} ...")
    plt.savefig(save_path, orientation='landscape', bbox_inches='tight', format="svg",
                dpi=300)
    log.info(f"3D relationship plot saved: {save_path}")
    plt.show()
    plt.close()


def heatmap(df, title):
    """
    Builds a heatmap showing correlations between price, nearest city center distance, and nearest landmark distance.
    Saves the heatmap as an SVG, displays it, and closes the plot.
    :param df: Pandas DataFrame.
    :param title: Plot title.
    """
    title = title.replace(' ', '_')
    save_path = f"{PROPERTY["FIGURES_DIR"]}/{title}.svg".lower()
    log.info(f"Building basic heatmap: {title}...")

    plt.figure(figsize=(10, 6))
    sns.heatmap(
        df[['price', 'nearest_city_center_miles', 'nearest_landmark_miles']].corr(),
        annot=True,
        cmap='coolwarm'
    )
    plt.title(title)
    log.info("Heat map created successfully.")

    log.info(f"Saving heatmap to {save_path}...")
    plt.savefig(save_path, orientation='landscape', bbox_inches='tight', format="svg",
                dpi=300)
    log.info(f"Correlations heatmap saved: {save_path}.svg")
    plt.show()
    plt.close()