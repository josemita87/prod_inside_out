# inside-out-clients

Pure infrastructure clients shared across the Inside-Out microservices.

Each client is a thin, parameterised wrapper around an external SDK. The clients
hold **no domain knowledge** — no hardcoded feature-group names or keys, no
field parsing, no data cleaning, and they never import a service `config`.
Callers pass everything in explicitly and own all domain logic.

## Clients and extras

Every SDK lives behind an optional dependency ("extra"), and SDK imports are
lazy (performed when a client is constructed), so importing a module never pulls
a dependency you did not ask for. Install only the extras for the clients you use:

One client per external service (e.g. a single `KafkaClient` covers both
consuming and producing — not separate consumer/producer classes):

| Client | Module | Extra | SDK |
| --- | --- | --- | --- |
| `HopsworksClient` | `inside_out_clients.feature_store` | `feature-store` | `hopsworks` |
| `AlpacaClient` | `inside_out_clients.broker` | `broker` | `alpaca-trade-api` |
| `KafkaClient` | `inside_out_clients.messaging` | `messaging` | `quixstreams` |
| `EdgarClient` | `inside_out_clients.edgar` | `edgar` (+ `edgar-live` for `fetch_live_links`) | `requests` / `selenium` |
| `MarketDataClient` | `inside_out_clients.market_data` | `market-data` | `yfinance` |

```toml
# in a service pyproject.toml
dependencies = ["inside-out-clients[feature-store,messaging]"]

[tool.uv.sources]
inside-out-clients = { path = "../../packages/inside-out-clients" }  # depth varies per service
```

## Usage

```python
from inside_out_clients.feature_store import HopsworksClient

fs = HopsworksClient(project_name="my_project", api_key="...")
bt4 = fs.feature_group(name="bt4", version=1, primary_key=["key"], event_time="date")
fs.insert(bt4, dataframe)
```
