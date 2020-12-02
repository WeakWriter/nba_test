from nba_data_manager import nba_data_cleaner
from nba_data_manager import nba_data_importer
import pandas
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn import linear_model
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler



class nba_predictor:

    def __init__(self,nba_data_cleaner, pearsonValue = 0.2, defaultValue = 0.005):
        self.nbaDataCleaner = nba_data_cleaner
        self.pearsonValue = pearsonValue
        self.defaultValue = defaultValue

    #function that selects feature with a corellation to playoff withs higer that pearsonValue
    #input => clean regular season games dataframe
    #output => list of features correlated to pl wins
    def getFeatures(self, regSeasonsData = pandas.DataFrame()):
        print("selecting features")
        corr = regSeasonsData.corr().abs()
        corr = corr.loc[corr['plVictories'] > self.pearsonValue]
        print('features selected' + str(list(corr.index)))
        return(list(corr.index))

    #produces a linear regression predictor
    #input => list of features to consider, clean regular season games dataframe, a boolean indicating if the data must be scaled or not (defaults to false)
    #output a list containing a linear regression model and the mean error rate of the linear regression model
    def linearPrediction (self, features = [], regSeasonsData = pandas.DataFrame(), scaling = False):
        print("linear regression, initiation")
        data = regSeasonsData[features]

        if scaling:
            scaler = StandardScaler()
            data = scaler.fit_transform(data)
            print("INFO: Data scaled")

        x = data.drop(['plWinner', 'plVictories'], axis=1, errors='ignore')
        y = regSeasonsData["plWinner"]
        xTrain, xValid, yTrain, yValid = train_test_split(x, y)
        lgModel = linear_model.LinearRegression()
        print("fitting model...")
        lgModel.fit(xTrain, yTrain)
        print("testing")
        lgModelPredicted = lgModel.predict(xValid)
        lgMAE = str(mean_absolute_error(lgModelPredicted, yValid))
        print("model trained, Mean Absolute Error: " + lgMAE)
        return [lgModel, lgMAE]

    #function that tests the accuracy of a random forest regressor with crossvalidation
    def randfoCrossval(self, estimators, crossval, method, x, y):
        model = RandomForestRegressor(n_estimators=estimators, criterion=method)
        scores = -1 * cross_val_score(model, x, y, cv=crossval, scoring='neg_mean_absolute_error')
        return scores.mean()

    # produces a random forest regressor
    # input => list of features to consider, clean regular season games dataframe, a boolean indicating if the data must be scaled or not (defaults to false)
    #          number of folds for k-crossval, minimum number of tree to try, maximum number of trees to try and step in between
    # output a list containing a la random forest regressor model and the mean error rate of the random forest regressor model
    def rfrPrediction (self, features = [],regSeasonsData = pandas.DataFrame(), scaling = False, k = 10, mintree = 50, maxTree = 150, stepTree = 10):

        print("random forest, initiation")
        data = regSeasonsData[features]
        if scaling:
            scaler = StandardScaler()
            data = scaler.fit_transform(data)
            print("INFO: Data scaled")

        x = data.drop(['plWinner', 'plVictories'], axis=1, errors='ignore')
        y = regSeasonsData["plWinner"]
        xTrain, xValid, yTrain, yValid = train_test_split(x, y)
        print("testing hyperparameters...")
        minError = 1
        minFactors = mintree
        method = ""
        for estimators in np.arange(start=mintree, stop=maxTree, step=stepTree):
            testMethod = 'mae'
            error = self.randfoCrossval(estimators, k, testMethod, x, y)
            if error < minError:
                minError = error
                minFactors = estimators
                method = testMethod
            testMethod = 'mse'
            error = self.randfoCrossval(estimators, k, testMethod, x, y)
            if error < minError:
                minError = error
                minFactors = estimators
                method = testMethod
        print("minimal error is with " + str(minFactors) + " trees, " + method + " splitting criterion, the cross validated MAE is " + str(minError))

        rfrModel = RandomForestRegressor(n_estimators=minFactors, criterion=method)
        print("training model...")
        rfrModel.fit(xTrain, yTrain)
        rfrPredicted = rfrModel.predict(xValid)
        rfrMAE = str(mean_absolute_error(rfrPredicted, yValid))
        print("model trained, Mean Absolute Error: " + rfrMAE)
        return [rfrModel,rfrMAE]

    # produces a hybrid predition (rfr value where >0, lg otherwise, with values <0 set to default)
    # input => list of features to consider, clean regular season games dataframe, a rfr model and a lgmodel, a default value for the predicted values <0
    # output a list containing a la random forest regressor model and the mean error rate of the random forest regressor model
    def hybridPred (self, features = [],regSeasonsData = pandas.DataFrame(), regSeasonData = pandas.DataFrame(), rfrModel = 0, lgModel = 0, defaultValue = 0.005):
        features.append('season')
        features.append('name')
        dataSeason = regSeasonData[features]
        xSeason = dataSeason.drop(['plWinner', 'plVictories', 'season', 'name'], 1).copy()
        infoSeason = dataSeason[['plWinner', 'plVictories', 'name']]

        lgModelPredictedSeason = lgModel.predict(xSeason)
        resultSeason = xSeason.copy()
        resultSeason = resultSeason.join(infoSeason, on='team_year').sort_values('plVictories', ascending=False)
        resultSeason['predictedWinLG'] = lgModelPredictedSeason

        rfrPredictedSeason = rfrModel.predict(xSeason)
        resultSeason['predictedWinRFR'] = rfrPredictedSeason


        resultSeason.loc[resultSeason["predictedWinRFR"] == 0, 'predictedWin'] = resultSeason["predictedWinLG"]
        resultSeason.loc[resultSeason["predictedWinRFR"] > 0, 'predictedWin'] = resultSeason["predictedWinRFR"]
        resultSeason.loc[resultSeason["predictedWin"] < 0, 'predictedWin'] = defaultValue


        resultSeason["cote"] = 1 / resultSeason["predictedWin"]
        resultSeason = resultSeason.sort_values('predictedWin', ascending=False)

        # les résultats finaux
        return resultSeason[["name", "cote"]]

    #streamlines the predction process
    #output => a table containing team names and rates
    def getRates(self):
        dataSets = self.nbaDataCleaner.cleanGamesData()
        regSeasonsData = dataSets[0]
        regSeasonData = dataSets[1]
        features = self.getFeatures(regSeasonsData)
        lgModel = self.linearPrediction(features, regSeasonsData)[0]
        rfrModel = self.rfrPrediction(features, regSeasonsData)[0]
        return(self.hybridPred(features,regSeasonsData, regSeasonData, rfrModel, lgModel, self.defaultValue))



