from pydantic import Field
from pydantic_settings import BaseSettings


from dotenv import load_dotenv  

load_dotenv(".env")
load_dotenv(".credentials.env")

class Config(BaseSettings):

    # Hopsworks settings
    project_name: str = Field(..., json_schema_extra={'env': 'PROJECT_NAME'})
    api_key: str = Field(..., json_schema_extra={'env': 'API_KEY'})
    feature_group_prices: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_PRICES'})
    feature_group_form4_basic: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_FORM4_BASIC'})
    feature_group_target: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_TARGET'})
    feature_group_version: int = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_VERSION'})
    event_time: str = Field(..., json_schema_extra={'env': 'EVENT_TIME'})

    # CSV settings
    hopsworks_connect: bool = Field(..., json_schema_extra={'env': 'HOPSWORKS_CONNECT'})
    csv_path_prices: str = Field(..., json_schema_extra={'env': 'CSV_PATH_PRICES'})
    csv_path_form4: str = Field(..., json_schema_extra={'env': 'CSV_PATH_FORM4'})
    csv_path_final: str = Field(..., json_schema_extra={'env': 'CSV_PATH_FINAL'})
    headers: list = Field(
        default=[
            "company_cik", "ticker", "insider_cik", "insider_name", "owner_code",
            "rule105b1", "derivative", "link", "shares", "acquired_disposed",
            "price", "date", "remaining_shares", "ownership", "coding",
            "direct_holding", "indirect_holding", "equity_swap", "timestamp", "key"
        ],
        json_schema_extra={'env': 'CSV_HEADERS'}
    )
    prices_headers: list = Field(
        default=["date", "close", "ticker"],
        json_schema_extra={'env': 'PRICES_HEADERS'}
    )

    #Investment settings
    delta_period: int = Field(..., json_schema_extra={'env': 'DELTA_PERIOD'})
    filter_key: str = Field(..., json_schema_extra={'env':'FILTER_KEY'})
    acquired_disposed: str = Field(..., json_schema_extra={'env': 'ACQUIRED_DISPOSED'})

    #Aggregation
    agg_dict:dict = Field({
        # 'first' method aggregation
        'company_cik': 'first',
        'key': 'first',
        'timestamp': 'first',
        #'insider_cik': 'first',
        #'insider_name': 'first',
        #'acquired_disposed': 'first',
        'date': 'first',
        'market_cap': 'first',
        
        # 'sum' method aggregation
        'shares': 'sum',
        'remaining_shares': 'sum',
        'direct_holding': 'sum',
        'indirect_holding': 'sum',
        
        # 'any' method aggregation (for boolean columns)
        'equity_swap': 'any',
        'rule105b1': 'any',
        
        # 'mode' method aggregation
        'derivative': lambda x: x.mode()[0],
        'owner_code': lambda x: x.mode()[0],
        'ownership': lambda x: x.mode()[0],
        'coding': lambda x: x.mode()[0],
        
        # 'mean' method aggregation
        'price': 'mean'
    })

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instantiate the configuration
config = Config()
