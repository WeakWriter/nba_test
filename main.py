
#imports nécessaires au projet
import pandas
from nba_data_manager import nba_data_cleaner
from nba_data_manager import nba_data_importer
from nba_predictors import nba_predictor
import os

# Press the green button in the gutter to run the script.
if __name__ == '__main__':


    # initialisation de variables nécessaires (info non-présente dns les données et introuvable sous forme de tableau en ligne)
    westConf = [2, 5, 6, 7, 8, 9, 16, 17, 19, 22, 23, 25, 28, 29, 30]  # composition de la conférence ouest
    seasonList = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016,
                  2017, 2018]  # saisons (celui-là existe dans les données)
    endOfPlayoffsList = ["2001-04-18 00:00:00.000", "2002-04-17 00:00:00.000", "2003-04-16 00:00:00.000",
                         "2004-04-17 00:00:00.000", "2005-04-20 00:00:00.000", "2006-04-19 00:00:00.000",
                         "2007-04-18 00:00:00.000", "2008-04-16 00:00:00.000", "2009-04-16 00:00:00.000",
                         "2010-04-14 00:00:00.000", "2011-04-13 00:00:00.000", "2012-04-26 00:00:00.000",
                         "2013-04-17 00:00:00.000", "2014-04-16 00:00:00.000", "2015-04-15 00:00:00.000",
                         "2016-04-13 00:00:00.000", "2017-04-12 00:00:00.000", "2018-04-11 00:00:00.000",
                         "2019-04-10 00:00:00.000"]  # dates de fin de saison régulière
    seasonAndDates = pandas.DataFrame({'season': seasonList, 'dates': endOfPlayoffsList})
    earlyRule = ["2000", "2001","2002"]  # sur ces trois années le premier tour des playoffs se jouait à 3 matchs gagnants
    pathGamesExcel = str(os.getcwd()) + "\\venv\data\dataGames.xlsx"
    pathRatesExcel = str(os.getcwd()) + "\\venv\data\Rates.xlsx"
    gamesPathParquet = "BasketrefBoxscores.parquet/ceb09b1cf1f34cc482ead718f9d95147.snappy.parquet"
    scorePathParquet = "BasketrefGames.parquet/61d3755ef1d348759c292b49676c3a76.snappy.parquet"
    bucket = "betclic-data-test"
    gamesInfoPath = "https://basketball.fandom.com/wiki/List_of_NBA_seasons"  # uniquement si on recherche des infos en ligne
    columnsToDrop = ['location', 'attendance', 'official1', 'official2', 'official3', 'game_id', 'away1', 'away2',
                     'away3', 'away4', 'away1_ot', 'away2_ot', 'away3_ot', 'away4_ot', 'away_wlratio', 'home1', 'home2',
                     'home3', 'home4', 'home1_ot', 'home2_ot', 'home3_ot', 'home4_ot', 'home_wlratio']
    featuresToAdd = ["vicMargin", "qtShare"]
    seasonToPred = 2018
    minPearsonValue = 0.2

    #initialisation des objets
    dataImporter = nba_data_importer(scorePathParquet, gamesPathParquet, bucket,pathGamesExcel)
    dataCleaner = nba_data_cleaner(dataImporter, seasonAndDates, featuresToAdd, westConf,earlyRule, seasonToPred)
    nbaPredictor = nba_predictor(dataCleaner, minPearsonValue)

    predictedValue = nbaPredictor.getRates()

    print(predictedValue)
    predictedValue.to_excel(pathRatesExcel)



