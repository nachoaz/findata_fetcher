# findata_fetcher

## Main Idea
Downloads all available fundamentals and price data for tickers specified in
company list text files; these should be prefixed by market and postfixed by
`clist_pofix` (which provides details on how this set of stocks were screened).

## Usage
Standing inside the `data_fetchers` directory, first download the data using
`download_tkr_data.py` and then write the corresponding datafiles using
`write_raw_datafiles.py`.

*Note*: You'll need an API key from Quandl. Read
[here](http://help.quandl.com/article/320-where-can-i-find-my-api-key).
