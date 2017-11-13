# findata_fetcher

## Main Idea
Downloads all available fundamentals and price data for tickers specified in
company list text files; these should be prefixed by market and postfixed by
`clist_pofix` (which provides details on how this set of stocks were screened).

## Usage
Standing inside the `data_fetchers` directory, first download the data using
`download_tkr_data.py` and then write the corresponding datafiles using
`write_raw_datafiles.py`.

For example:
`python download_tkr_data.py consg_tech_more_than_10_years_head YOUR_API_KEY`
`python write_raw_datafiles.py consg_tech_more_than_10_years_head`

*Note*: You'll need an API key from Quandl. Read [here](goo.gl/gbtxsi).
