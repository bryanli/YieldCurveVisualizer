# Parse and visulize Treasury yield curve data

Data are from real time Treasury database:
https://data.treasury.gov/feed.svc/DailyTreasuryYieldCurveRateData?$filter=year(NEW_DATE)%20eq%202020

e.g. to see average value for 3 day intervals:

python parse_treasury_yield_curve.py --interval=3 --legend=true


