import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

headers = {'User-Agent': "ntufar@gmail.com"}

# Get list of all CIKs
# tickers_cik = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
# tickers_cik =     pd.json_normalize(pd.json_normalize(tickers_cik.json(),max_level=0).values[0])
# tickers_cik["cik_str"] = tickers_cik["cik_str"].astype(str).str.zfill(10)
# tickers_cik.set_index("ticker",inplace=True)
# print(tickers_cik)

# Apple's totoal assets
response = requests.get("https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/Assets.json", headers=headers)

assets_timeserie = pd.json_normalize(response.json()["units"]["USD"])
assets_timeserie["filed"] = pd.to_datetime(assets_timeserie["filed"])
assets_timeserie = assets_timeserie.sort_values("end")


#print(assets_timeserie)

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(go.Scatter(
    x=assets_timeserie["end"],
    y=assets_timeserie["val"],
    name='Total Assets value (USD)',
))



fig.update_layout(
    width=1000,
    height=700,
    paper_bgcolor='white',
    plot_bgcolor='#fafafa',
    hovermode='closest',
    title="Apple Total Assets value over time",
    xaxis = dict(
        title="Time"
    ),
    yaxis = dict(
        title="Total Assets value (USD)"
    ),
    showlegend=False)
    
fig.show()