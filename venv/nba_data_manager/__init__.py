import pandas

#this objects prepares the data for prediction
class nba_data_cleaner:
    #constructor
    def __init__(self,nba_data_importer , seasonsAndDates, additionnalFeatures, westConf, earlyRule, seasonToPred):
        self.nbaDataImporter = nba_data_importer
        self.seasonsAndDates = seasonsAndDates
        self.additionnalFeatures = additionnalFeatures
        self.westConf = westConf
        self.earlyRule = earlyRule
        self.seasonToPred = seasonToPred

    #function that separates regular season and playoff games for every season
    #input => raw data from the nba_data_importer object
    #output => a list of 2 dataframes one for regular season games and one for playoff games
    def sepRegPlayoffs (self, dataGames = pandas.DataFrame()):
        regSeasons = pandas.DataFrame()
        plSeasons = pandas.DataFrame()
        for index, row in self.seasonsAndDates.iterrows():
            regSeason = dataGames.loc[(dataGames['season'] == row['season']) & (dataGames['datetime'] <= row['dates'])].sort_values('datetime')
            regSeasons = pandas.concat([regSeasons, regSeason], ignore_index=True, sort=False)
            plSeason = dataGames.loc[(dataGames['season'] == row['season']) & (dataGames['datetime'] > row['dates'])].sort_values('datetime')
            plSeasons = pandas.concat([plSeasons, plSeason], ignore_index=True, sort=False)
        return [regSeasons, plSeasons]

    #function that deletes columns not relevant for prediction
    #input => reglar season games dataframe and plyoff games dataframe
    #output => a list of 2 dataframes one for regular season games and one for playoff games
    def cleanGames(self,separatedGames = [], columnsToDrop = []):
        separatedGames[0].drop(columnsToDrop, axis=1)
        separatedGames[1].drop(columnsToDrop, axis=1)
        return separatedGames

    #function that adds features relevant for prediction
    #input => regular or playoff season games dataframe
    #output => = regular or playoff season games dataframe with new features
    def addFeatures (self,regSeasons= pandas.DataFrame()):

        #TODO add a check so that the list can only contain possible elements
        if(self.additionnalFeatures.__contains__("vicMargin")):
            regSeasons['awayVicMargin'] = 0
            regSeasons.loc[regSeasons['ylabel'] == 0, 'awayVicMargin'] = regSeasons['away_ftscore'] - regSeasons['home_ftscore']
            regSeasons['homeVicMargin'] = 0
            regSeasons.loc[regSeasons['ylabel'] == 1, 'homeVicMargin'] = regSeasons['home_ftscore'] - regSeasons['away_ftscore']

        if (self.additionnalFeatures.__contains__("qtShare")):
            # la part du total score marqué, par quart temps (je considère que les overtime ne sont pas relevant)
            regSeasons['away1share'] = regSeasons['away1'] / regSeasons['away_ftscore']
            regSeasons['away2share'] = regSeasons['away2'] / regSeasons['away_ftscore']
            regSeasons['away3share'] = regSeasons['away3'] / regSeasons['away_ftscore']
            regSeasons['away4share'] = regSeasons['away4'] / regSeasons['away_ftscore']
            regSeasons['home1share'] = regSeasons['home1'] / regSeasons['home_ftscore']
            regSeasons['home2share'] = regSeasons['home2'] / regSeasons['home_ftscore']
            regSeasons['home3share'] = regSeasons['home3'] / regSeasons['home_ftscore']
            regSeasons['home4share'] = regSeasons['home4'] / regSeasons['home_ftscore']

        return regSeasons

    #function that duplicates games for home and away teams
    #input => regular season games dataframe
    #output => a list of 2 dataframes, one for home games and one for away teams
    def sepHomeAway(self,regSeasons):
        #column selection
        regSeasonsAway = regSeasons[
            ['game_id', 'season', 'away_id', 'away_name', 'away_ftscore', 'awayVicMargin', 'away1', 'away2', 'away3',
             'away4','away1_ot', 'away2_ot', 'away3_ot', 'away4_ot', 'away_pace', 'away_efg', 'away_tov', 'away_orb',
             'away_ftfga', 'away_ortg','away1share', 'away2share', 'away3share', 'away4share', 'ylabel']]
        regSeasonsHome = regSeasons[
            ['game_id', 'season', 'home_id', 'home_name', 'home_ftscore', 'homeVicMargin', 'home1', 'home2', 'home3',
             'home4','home1_ot', 'home2_ot', 'home3_ot', 'home4_ot', 'home_pace', 'home_efg', 'home_tov', 'home_orb',
             'home_ftfga', 'home_ortg','home1share', 'home2share', 'home3share', 'home4share', 'ylabel']]
        #column renaming
        regSeasonsAway = regSeasonsAway.rename(
            columns={'away_id': 'id', 'away_name': 'name', 'away_ftscore': 'ft_score', 'awayVicMargin': 'vicMargin',
                     'away_pace': 'pace', 'away_efg': 'efg', 'away_tov': 'tov',
                     'away_orb': 'orb', 'away_ftfga': 'ftfga', 'away_ortg': 'ortg', 'away1share': '1share',
                     'away2share': '2share', 'away3share': '3share', 'away4share': '4share'})
        regSeasonsHome = regSeasonsHome.rename(
            columns={'home_id': 'id', 'home_name': 'name', 'home_ftscore': 'ft_score', 'homeVicMargin': 'vicMargin',
                     'home_pace': 'pace', 'home_efg': 'efg', 'home_tov': 'tov',
                     'home_orb': 'orb', 'home_ftfga': 'ftfga', 'home_ortg': 'ortg', 'home1share': '1share',
                     'home2share': '2share', 'home3share': '3share', 'home4share': '4share'})

        #add a vicory column for counting regSeaon Victories later
        regSeasonsAway.loc[regSeasonsAway['ylabel'] == 0, 'victory'] = 1
        regSeasonsHome.loc[regSeasonsHome['ylabel'] == 1, 'victory'] = 1
        regSeasonsAway['victory'].fillna(0, inplace=True)
        regSeasonsHome['victory'].fillna(0, inplace=True)

        #creates an index to rejoin the tables later
        regSeasonsAway['team_year'] = regSeasonsAway[['season', 'id']].apply(lambda row: '_'.join(row.values.astype(str)), axis=1)
        regSeasonsHome['team_year'] = regSeasonsHome[['season', 'id']].apply(lambda row: '_'.join(row.values.astype(str)), axis=1)

        return [regSeasonsHome, regSeasonsAway]

    #function that aggregates home and away games and joins them back together
    #input => list of regular season home and away games dataframes
    #output => an aggregated tables with statistics on games per teams per season
    def aggregateRegSeasonGames (self,regSeasonsSep= []):
        # aggregating
        regSeasonsHome = regSeasonsSep[0].groupby('team_year').agg(
            {'season': 'first', 'id': 'first', 'name': 'first', 'ft_score': 'mean',
             'vicMargin': 'mean', 'pace': 'mean', 'efg': 'mean', 'tov': 'mean', 'orb': 'mean',
             'ftfga': 'mean', 'ortg': 'mean', '1share': 'mean', '2share': 'mean',
             '3share': 'mean', '4share': 'mean', 'ylabel': 'mean', 'victory': 'sum'})
        regSeasonsAway = regSeasonsSep[1].groupby('team_year').agg(
            {'season': 'first', 'id': 'first', 'name': 'first', 'ft_score': 'mean',
             'vicMargin': 'mean', 'pace': 'mean', 'efg': 'mean', 'tov': 'mean', 'orb': 'mean',
             'ftfga': 'mean', 'ortg': 'mean', '1share': 'mean', '2share': 'mean',
             '3share': 'mean', '4share': 'mean', 'ylabel': 'mean', 'victory': 'sum'})

        # Joinng the two tables
        regSeasons = pandas.concat([regSeasonsAway, regSeasonsHome])

        # performing aggregation on the unified dataframe
        regSeasons = regSeasons.groupby('team_year').agg(
            {'season': 'first', 'id': 'first', 'name': 'first', 'ft_score': 'mean', 'vicMargin': 'mean', 'pace': 'mean',
             'efg': 'mean', 'tov': 'mean', 'orb': 'mean','ftfga': 'mean', 'ortg': 'mean', '1share': 'mean',
             '2share': 'mean','3share': 'mean', '4share': 'mean', 'victory': 'sum'})

        return regSeasons

    # function that aggregates pl season games, counting playoofs victories
    # input => list of playoff season games dataframes
    # output => an aggregated tables with statistics on playoff games per teams per season
    def aggregatePLSeasonGames(self,plSeasons= pandas.DataFrame()):
        # creates a column containing game winner ID
        plSeasons['plVictories'] = ''
        plSeasons.loc[plSeasons['ylabel'] == 1, 'plVictories'] = plSeasons['home_id']
        plSeasons.loc[plSeasons['ylabel'] == 0, 'plVictories'] = plSeasons['away_id']

        # creates an index to join with regular season later
        plSeasons['team_year'] = plSeasons[['season', 'plVictories']].apply(lambda row: '_'.join(row.values.astype(str)), axis=1)
        #aggregates data (here we only care about nbr of pl wins
        plSeasons = plSeasons[['team_year', 'plVictories']].groupby('team_year').agg('count')

        return(plSeasons)

    # function that deletes all teams not selected in the playoffs (removing data noise)
    # input => aggregated regular eason dataframe, aggregated playoff dataframe, list of seasons, list of team ID in the west conference
    # output => a dataframe containing the aggregated statistics per team per season only for teams that played in the playoffs + the number of PL victories
    def getQualifs (self,regSeasons= pandas.DataFrame(), plSeasons = pandas.DataFrame(),seasonsList = [], westConf = []):

        #calculates who is in the playoffs (8 teams with most victories in each conference)
        regSeasonsQualif = pandas.DataFrame()
        for season in self.seasonsAndDates["season"]:
            regSeasonsQualifWest = regSeasons.loc[(regSeasons["id"].isin(westConf)) & (regSeasons["season"] == season)].nlargest(8, 'victory').copy()
            regSeasonsQualifEst = regSeasons.loc[~(regSeasons["id"].isin(westConf)) & (regSeasons["season"] == season)].nlargest(8, 'victory').copy()
            regSeasonsQualif = pandas.concat([regSeasonsQualif, regSeasonsQualifWest, regSeasonsQualifEst], ignore_index=True, sort=False)

        #recreates the index
        regSeasonsQualif['team_year'] = regSeasonsQualif[['season', 'id']].apply(lambda row: '_'.join(row.values.astype(str)), axis=1)
        regSeasonsQualif.set_index('team_year', inplace=True, drop=True)

        #join with the table containing number of pl victories
        regSeasonsQualif = regSeasonsQualif.join(plSeasons, on='team_year')

        return regSeasonsQualif

    #function that defines who won the playoffs
    #input => output of getQualifs, list of years where the "3 games to win on the first round" rule existed
    #output => same dataframe as input with a plWinner column
    def getPlWins (self,regSeasonsQualif= pandas.DataFrame(), earlyRule= []):
        regSeasonsQualif.loc[(regSeasonsQualif['season'].isin(earlyRule)) & (regSeasonsQualif['plVictories'] == 15), 'plWinner'] = 1
        regSeasonsQualif.loc[regSeasonsQualif['plVictories'] == 16, 'plWinner'] = 1
        regSeasonsQualif['plVictories'].fillna(0, inplace=True)
        regSeasonsQualif['plWinner'].fillna(0, inplace=True)
        return regSeasonsQualif

    #function that separates the year to predict from the onther so that we don't learn on what we xant to predict
    #input => output of getPLWins
    #output => a dataframe without the season to predict and a dataframe with only the season to predict
    def getSets(self,regSeasonsQualif= pandas.DataFrame(), seasonToPred = 2018):
        regSeasonToPred = regSeasonsQualif.loc[regSeasonsQualif['season'] == seasonToPred]
        regSeasonsQualif = regSeasonsQualif.loc[regSeasonsQualif['season'] != seasonToPred]
        return([regSeasonsQualif, regSeasonToPred])

    #fonction that streamlines the data cleaning and processing (it creates a table at each step for easy debugging)
    #output => a dataframe formated to be fed to the nba_predictors
    def cleanGamesData (self):
        print("loading data")
        rawGamesData = self.nbaDataImporter.importGamesExcel()
        print("data loaded, cleaning and formatting")
        separatedGames = self.sepRegPlayoffs(rawGamesData)
        cleanedGames = self.cleanGames(separatedGames)
        cleanedRegSeason = cleanedGames[0]
        cleanedPLSeason = cleanedGames[1]
        cleanedRegSeason = self.addFeatures(cleanedRegSeason)
        sepRegSeason = self.sepHomeAway(cleanedRegSeason)
        aggregatedRegSeason = self.aggregateRegSeasonGames(sepRegSeason)
        aggregatedPLSeason = self.aggregatePLSeasonGames(cleanedPLSeason)
        regSeasonsQualif = self.getQualifs(aggregatedRegSeason, aggregatedPLSeason, self.seasonsAndDates["season"], self.westConf)
        regSeasonsFinal = self.getPlWins(regSeasonsQualif, self.earlyRule)
        finalSets = self.getSets(regSeasonsFinal, self.seasonToPred)
        print("data cleaned and formatted")
        return finalSets




#this objects import the necessary data into the project
class nba_data_importer:

    #constructor
    def __init__(self, pathBasketRefBoxScore, pathBasketRefGames, bucket, excelPath):
        self.pathBasketRefBoxScore = pathBasketRefBoxScore
        self.pathBasketRefGames = pathBasketRefGames
        self.bucket = bucket
        self.excelPath = excelPath

    #import the games data from a parquet file
    def importGamesParquet ():
        bucketGamesUri = f"s3://{bucket}/{self.pathBasketRefGames}"
        return pandas.read_parquet(bucketGamesUri)

    #import the score data from a parquet file
    def importScoresParquet ():
        bucketScoreUri = f"s3://{bucket}/{self.pathBasketRefBoxScore}"
        return pandas.read_parquet(bucketScoreUri)

    #import games data from an excel file
    def importGamesExcel(self):
        return pandas.read_excel(self.excelPath)

    #imports some historical info about the games (unfortunately does not contain the end of regular season date)
    def importGamesInfo(path = ""):
        gamesInfo = pandas.concat([pd.read_html(path)[6], pd.read_html(path)[7]])
        return gamesInfo
