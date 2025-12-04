import statsmodels.formula.api as smf
from settings.Settings import settings


def run_ols_models(df):
    # Model 1: Price v. Distance to City Center
    print("Building regression models...(1/4)")
    model1 = smf.ols('price ~ nearest_city_center_miles', data=df).fit()
    print("Saving regression model 1...")
    with open(f"{settings.MODELS_DIR}/model1_city_center.txt", "w") as f:
        f.write(model1.summary().as_text())
    print(f"Regression model 1 saved: {settings.MODELS_DIR}/model1_city_center.txt")
    print()

    # Model 2: Price v. Distance to Landmark
    print("Building regression models...(2/4)")
    model2 = smf.ols('price ~ nearest_landmark_miles', data=df).fit()
    print("Saving regression model 2...")
    with open(f"{settings.MODELS_DIR}/model2_landmark.txt", "w") as f:
        f.write(model2.summary().as_text())
    print(f"Regression model 2 saved: {settings.MODELS_DIR}/model2_landmark.txt")
    print()

    # Model 3: Overlay of Both
    print("Building regression models...(3/4)")
    model3 = smf.ols('price ~ nearest_city_center_miles + nearest_landmark_miles', data=df).fit()
    print("Saving regression model 3...")
    with open(f"{settings.MODELS_DIR}/model3_full.txt", "w") as f:
        f.write(model3.summary().as_text())
    print(f"Regression model 3 saved: {settings.MODELS_DIR}/model3_full.txt")
    print()

    # Model 4: Compound Effect of Both
    print("Building regression models...(4/4)")
    model4 = smf.ols('price ~ nearest_city_center_miles * nearest_landmark_miles', data=df).fit()
    print("Saving regression model 4...")
    with open(f"{settings.MODELS_DIR}/model4_interaction.txt", "w") as f:
        f.write(model4.summary().as_text())
    print(f"Regression model 4 saved: {settings.MODELS_DIR}/model4_interaction.txt")
    print()

    # Print models
    print(model1.summary())
    print(model2.summary())
    print(model3.summary())
    print(model4.summary())