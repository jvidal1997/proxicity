import matplotlib.pyplot as plt
import seaborn as sns
from Settings import ENV as PROPERTY


def scatter(df, title, xlabel, ylabel):
    title = title.replace(' ', '_')
    save_path = f"{PROPERTY["FIGURES_DIR"]}/{title}.svg".lower()
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=xlabel, y=ylabel, data=df)
    sns.regplot(x=xlabel, y=ylabel, data=df, scatter=False, color='red')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


def plot3d(df, title, xlabel, ylabel, zlabel, xunit, yunit, zunit):
    title = title.replace(' ', '_')
    save_path = f"{PROPERTY["FIGURES_DIR"]}/{title}.svg".lower()
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(df[xlabel], df[ylabel], df[zlabel], c="red",
               cmap='viridis', s=20, alpha=0.8)
    ax.set_xlabel(f"{xlabel} {xunit}")
    ax.set_ylabel(f"{ylabel} {yunit}")
    ax.set_zlabel(f"{zlabel} {zunit}")
    plt.title("3D Plot: Price vs Distances")
    print("Build successful.")
    print("Saving 3D relationship plot...")
    plt.savefig(save_path, orientation='landscape', bbox_inches='tight', format="svg",
                dpi=300)
    print(f"3D relationship plot saved: {PROPERTY["FIGURES_DIR"]}/3d_price_distance_plot.svg")
    print()
    plt.show()
    plt.close()


def heatmap(df, title):
    title = title.replace(' ', '_')
    print("Building correlations heatmap...")
    plt.figure(figsize=(10, 6))
    sns.heatmap(
        df[['price', 'nearest_city_center_miles', 'nearest_landmark_miles']].corr(),
        annot=True,
        cmap='coolwarm'
    )
    plt.title(title)
    print("Build successful.")

    print("Saving correlation heatmap...")
    plt.savefig(f"{PROPERTY["FIGURES_DIR"]}/{title}.svg".lower(), orientation='landscape', bbox_inches='tight', format="svg",
                dpi=300)
    print(f"Correlations heatmap saved: {PROPERTY["FIGURES_DIR"]}/{title}.svg")
    print()

    plt.show()
    plt.close()