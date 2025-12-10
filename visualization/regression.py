"""
Provides functionality to run ordinary least squares (OLS) regression analyses on apartment/listing data.
Includes four models examining the relationship between apartment prices and distances to city centers and landmarks.
Each model summary is saved as a text file and printed to the console.

Functions:
- run_ols_models(df): Runs four OLS regression models on the DataFrame and saves/prints their summaries.
"""
import statsmodels.formula.api as smf
from Settings import ENV as PROPERTY


def run_ols_models(df):
    """
    Runs four ordinary least squares (OLS) regression models on the DataFrame to analyze the relationship between
    apartment prices and distances to city centers and landmarks.

    Saves each model summary as a text file in the configured models directory and prints the summaries to the console.
    :param df: DataFrame of apartment prices and distances to city centers and landmarks.
    """
    # Model 1: Price v. Distance to City Center
    print("Building regression models...(1/4)")
    model1 = smf.ols('price ~ nearest_city_center_miles', data=df).fit()
    print("Saving regression model 1...")
    with open(f"{PROPERTY["FIGURES_DIR"]}/model1_city_center.txt", "w") as f:
        f.write(model1.summary().as_text())
    print(f"Regression model 1 saved: {PROPERTY["FIGURES_DIR"]}/model1_city_center.txt")
    print()

    # Model 2: Price v. Distance to Landmark
    print("Building regression models...(2/4)")
    model2 = smf.ols('price ~ nearest_landmark_miles', data=df).fit()
    print("Saving regression model 2...")
    with open(f"{PROPERTY["FIGURES_DIR"]}/model2_landmark.txt", "w") as f:
        f.write(model2.summary().as_text())
    print(f"Regression model 2 saved: {PROPERTY["FIGURES_DIR"]}/model2_landmark.txt")
    print()

    # Model 3: Overlay of Both
    print("Building regression models...(3/4)")
    model3 = smf.ols('price ~ nearest_city_center_miles + nearest_landmark_miles', data=df).fit()
    print("Saving regression model 3...")
    with open(f"{PROPERTY["FIGURES_DIR"]}/model3_full.txt", "w") as f:
        f.write(model3.summary().as_text())
    print(f"Regression model 3 saved: {PROPERTY["FIGURES_DIR"]}/model3_full.txt")
    print()

    # Model 4: Compound Effect of Both
    print("Building regression models...(4/4)")
    model4 = smf.ols('price ~ nearest_city_center_miles * nearest_landmark_miles', data=df).fit()
    print("Saving regression model 4...")
    with open(f"{PROPERTY["FIGURES_DIR"]}/model4_interaction.txt", "w") as f:
        f.write(model4.summary().as_text())
    print(f"Regression model 4 saved: {PROPERTY["FIGURES_DIR"]}/model4_interaction.txt")
    print()

    # Print models
    print(model1.summary())
    print(model2.summary())
    print(model3.summary())
    print(model4.summary())