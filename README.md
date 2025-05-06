# Dataset Finder

A tool to help quickly access and filter through datasets. Intended for ACS datasets (specifically, the tool was created for the [ACS bias correction release](https://github.com/AusClimateService/bias-correction-data-release), but it should work with other datasets as long as they follow a consistent directory and file name format.

## Basic Usage

The paths.yml file has been set up with paths corresponding to the locations of the dynamically downscaled and bias adjusted data currently on ia39 and kj66. These have been labelled "ACS_DD" and "ACS_BC" respectively.

Running the line `get_datasets("ACS_DD")` in a JuypterLab cell will print a table containing all the datasets that could be found that follow the given directory structure. Each dataset will have information given about it, such as org, GCM, RCM or any other labels corresponding to {} enclosed names within the directory path format. 

Each of these can be filtered - for example, `get_datasets("ACS_DD", org = "BOM", gcm = "ACCESS")` will only show ACCESS models downscaled by the Bureau. Matches are not exact by default - the given example of `gcm = "ACCESS"` will match both "ACCESS-CM2" and "ACCESS-ESM1-5". This can be changed by adding "exact_match = True" into the argument list.

Multiple values can be supplied for each term. `get_datasets("ACS_DD", org = ("BOM", "CSIRO"), gcm = "ACCESS")` will show all ACCESS models for both the Bureau and CSIRO.

`get_datasets` returns a dataset_info_collection object which can be indexed to access individual dataset_info objects:

```
all_data = get_datasets("ACS_DD")
data = all_data[0]
data.print_info()
```

This will print information about the dataset - in this case, which years it contains.

The dataset_info can then by further filtered down to select years:
```
data.select(year = year_range(1980, 1990))
```
When selecting years, it is required to use year_range as the internal code will be confused by regular Python range (as that returns integers rather than strings which the code uses to match).

Finally, the dataset_info object can be loaded using xarray: `xr.open_mfdataset(data)`.

Further examples can be found in the provided example notebook, with a warning that it may be cumbersome to read directly on Git due to the large tables printed.

## What's next?

- FAQ for this page
- Memory / speed optimisations
- A tool to help come up with the path structures in the first place without needing to manually input
- Suggested output path structures for saving transformed data
- Potential improvements to the way date ranges are parsed
- More options for manipulating / viewing the large output tables - for example, there is currently no way to sort them

## Known Issues / Quirks

- The "GCM" path has an incredibly large number of files and thus takes a very long time to load without filters. Only use this if you have an idea of what you are looking for.
- Using "select" on a collection or dataset_info will modify it in-place instead of returning a modified clone, which may cause confusion if the same table is referenced with multiple queries.

Please contact Andrew Gammon (Andrew.Gammon@bom.gov.au) if you have any suggestions, issues or other feedback.
