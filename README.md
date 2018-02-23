# findata_fetcher

## Main Idea
Downloads all available fundamentals and price data for tickers specified in
ticker list text files.

## Setup
We suggest that you create a virtual environment to house the necessary versions
of the software you'll need to use findata_fetcher. Once you've done that and
you've activated that environment, you can install the required versions onto
that environment by doing `pip install -r requirements.txt`.

## Usage
(1) `create-ticlist-file-from-screener-result`
(2) `download-ticker-data.py`
(3) `write-cp-datafiles.py`
(4) `write-processed-datafiles.py`
(5) `write-datfile.py`
First create the `ticlist` files (which will reside inside `data/ticker-lists`),
corresponding to the list of companies you want to consider. Standing inside the
`src` directory, continue by downloading the data using
`download-ticker-data.py`, then write the corresponding `cp-data` ('close price'
data) files using `write-cp-datafiles.py`. Finally, run prepare-data.py to write
the `.dat` file corresponding to your specified `ticlist`, `feat_map`, and
`lag_months`.


## Example
`python write_clist_files.py clist_definer clist_pofix`
> Where clist_definer is a file that specifies how to screen to get the list of
> companies that you want (i.e. sector(s), market cap, years trading publicly,
> etc.), and clist_pofix specifies what you want the names of your clist_files
> to be postfixed by.  *Note*: this is yet to be written (need to find a
> screener with an API that I can talk to) --for now, these are written by hand.

`python download_tkr_data.py consg_tech_more_than_10_years_head YOUR_API_KEY`
> Here, `consg_tech_more_than_10_years_head` is a clist_pofix specifying where
> to find the list of companies to use.

`python write_cp_datafiles.py consg_tech_more_than_10_years_head`

`python prepare_data.py consg_tech_more_than_10_years_head jda_map.txt`
> Here, jda_map.txt is a `feat_map` file. A `feat_map` file should reside in
> `scripts/feature_mappings`, should be postfixed as `.txt`, and should abide by
> the following format:
>  * the delimiter is the bar character `|`
>  * the first line should be: `srfile|srfile_feat|mdfile_feat|version`
>  * the first column should be one of (`income`, `balance`, `cashflow`,
>    `growth`, `metrics`), and answers the question of "which srow_data .xlsx
>    file does this reside in?"
>  * the second column answers the question "by what name is the piece of data
>    that you want indexed on the .xlsx file that you specified in column 1?"
>  * the third column answers the question "what name would you like this piece
>    of data to have on the .dat file that will be produced?"
>  * the fourth column should be one of (`ttm`, `mrq`, `ttm_implicit`, or
>    `mrq_implicit`). It specifies whether you want this piece of data to be in
>    the form of 'trailing twelve months' or in 'most recent quarter' form. The
>    `_implicit` versions are the same as the first two, except that while the
>    first two versions rename the corresponding .dat column as specified by
>    `mdfile_feat` _and_ append a `_ttm` or `_mrq` postfix to that .dat column
>    name, the `_implicit` versions do not.


*Note*: You'll need an API key from Quandl. Read [here](https://goo.gl/4VccrT).
