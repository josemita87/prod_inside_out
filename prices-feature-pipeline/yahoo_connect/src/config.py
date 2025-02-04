from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import pandas as pd

# Load the main .env file and then the credentials.env file
load_dotenv(".env")
load_dotenv(".credentials.env")

class Config(BaseSettings):
    # Hopsworks Settings
    project_name: str = Field(..., json_schema_extra={'env': 'PROJECT_NAME'})
    feature_group_prices: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_NAME'})
    feature_group_form4_basic: str = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_FORM4_BASIC'})
    feature_group_version: int = Field(..., json_schema_extra={'env': 'FEATURE_GROUP_VERSION'})
    feature_view_version: int = Field(..., json_schema_extra={'env': 'FEATURE_VIEW_VERSION'})
    feature_view_name: str = Field(..., json_schema_extra={'env': 'FEATURE_VIEW_NAME'})
    event_time: str = Field(..., json_schema_extra={'env': 'EVENT_TIME'})
    hopsworks_connect: bool = Field(..., json_schema_extra={'env': 'HOPSWORKS_CONNECT'})
    api_key: str = Field(..., json_schema_extra={'env': 'API_KEY'})
    inference_blueprint: dict = Field({
        "date": pd.to_datetime(["1999-01-01"]),
        "close": [-1.0],
        "ticker": ["INFERENCE_VALUE"],
    })
    
    # Batching Settings
    buffer_size: int = Field(100, json_schema_extra={'env': 'BUFFER_SIZE'})

    # CSV Settings
    csv_path_prices: str = Field(..., json_schema_extra={'env': 'CSV_PATH_PRICES'})
    csv_path_form4: str = Field(..., json_schema_extra={'env': 'CSV_PATH_FORM4'})
    
    # CSV Headers
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

config = Config()
