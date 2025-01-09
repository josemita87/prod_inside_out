import hopsworks
import pandas as pd
from loguru import logger
from config import config

class Connection:  
    def __init__(self)-> None:

        #Initialize connection to Hopsworks
        self.project = hopsworks.login(
            project=config.project_name,
            api_key_value=config.api_key,
        )
        self.fs = self.project.get_feature_store()
    
        #Feature group connections
        self.fg_txs = self.fs.get_or_create_feature_group(
            name=config.feature_group_form4_basic,
            version=config.feature_group_version,
            primary_key=['key'],
            event_time='date'
        )
        self.fg_prices = self.fs.get_or_create_feature_group(
            name=config.feature_group_prices,
            version=config.feature_group_version,
            primary_key=['date', 'ticker'],
            event_time='date'
        )

        self.job = None

    def fetch_ticker_data(self) -> pd.DataFrame:
    
        data: pd.DataFrame = self.fg_txs.read()
        tickers = data['ticker'].unique()
        
        return tickers
    

    def fetch_price_data(self, processing_tickers: list) -> pd.DataFrame:
        
        #Insert dummy data infer schema
        blueprint = reduce_mem_storage(pd.DataFrame(config.inference_blueprint))
        self.fg_prices.insert(blueprint)

        try:
            prices_fv = self.fs.get_or_create_feature_view(
                name=config.feature_view_name,
                version=config.feature_view_version,
                query=self.fg_prices.filter(
                    self.fg_prices.ticker.isin(processing_tickers)
                )
            )

            return prices_fv.get_batch_data()
        
        except:  
            return pd.DataFrame()
        

    def push_data(self, data: pd.DataFrame) -> None:
        
        if not data.empty: 
            self.job, _ = self.fg_prices.insert(
                data, write_options = {
                    'start_offline_materialization':False,
                    'mode':'append' 
                }
            )


    def materialization_jobs(self):
        self.job.run()
        
# Auxiliary function
def reduce_mem_storage(df:pd.DataFrame) -> pd.DataFrame:
    """Reduces the memory usage of the given DataFrame"""
    # Drop index column if it exists
    if df.columns.str.contains('index').any():
        df.drop(columns=['index'], inplace=True)
    # Convert the date column to datetime 64ns
    df['date'] = pd.to_datetime(df['date'])
    # Convert the close column to float32
    df['close'] = df['close'].astype('float32')
    # Convert the ticker column to category
    df['ticker'] = df['ticker'].astype('category')

    return df