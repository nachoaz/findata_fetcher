# To Do's

- [X] Download scripts are very much network I/O bound. Parallelize this to make
      downloading faster.
- [ ] Make feat_map command line argument be the name of the actual feature
      mapping file (currently it's whatever the name with the .txt postfixed
      is). 
- [ ] Ensure use of dash and underscores is consistent.
- [ ] Rewrite whatever's affected by 'feat_map' files so that these 'feat_map'
      files can be .dat files instead of .txt files.
- [ ] See if by having longer sleep times between requests (and thus having less
      of a load on server at any point in time) there's less requests that are
      rejected (and thus eventually hopefully less of a need to re-run and
      re-run fetch_data_write_datfile.py over and over.
- [ ] Incorporate `update` option to download_trk_data.py (to 'grow' .xlsx
      files, instead of overwritting them).
