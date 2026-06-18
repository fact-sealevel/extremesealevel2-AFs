# extremesealevel2-afs

This module samples input from the `facts-total` module to generate samples of local mean sea-level change, ultimately calculating return curves for future extreme sea level events at user defined return periods.

Code by Tim Hermans with modifications by FACTS dev team, Spring 2026.

> [!CAUTION]
> This is a prototype. It is likely to change in breaking ways. It might delete all your data. Don't use it in production.

## Example

Below is an example of how to setup and run this module as a standalone application in a Docker container. 

> [!WARNING]
> This will download ~ 48 GB to your machine.

First, download required input data and place it in a `data/input` sub-directory of the project root:
```
# Make input data dir
mkdir -p ./data/input

# Download input data
curl -sL https://zenodo.org/records/20296846/files/extremesealevel2_AFs_fulldata.tgz | tar -zx -C ./data/input

# Make output data dir
mkdir -p ./data/output
```

Add totaled sealevel change data to input directory. This module requires output from the [facts-total](https://github.com/fact-sealevel/facts-total). Move the file you would like to use to `./data/input`. Alternatively, you can mount a volume to the container with the directory holding the totaled output and pass the filename as an arg.

Build a Docker image:
```
docker build -t extremesealevel2-afs .
```

Then, run the application in a Docker container based on the image

```shell
docker run --rm \
-v "./data/input:/mnt/data_in" \
-v "./data/output:/mnt/data_out" \
extremesealevel2-afs \
--pipeline-id "aaa" \
--esl-fit-statistics-file "/mnt/data_out/esl_fit_statistics_ds.nc" \
--min-years 20 \
--resample-freq "D_max" \
--deseasonalize 1 \
--detrend 1 \
--subtract-amean 0 \
--match-lim 10 \
--gpd-pot-threshold 99 \
--decluster-window 3 \
--decluster-method "rolling_max" \
--nsamps 1000 \
--total-localsl-file "/mnt/data_in/all-modules_local_total.nc" \
--esl-data "gesla3_data" \
--esl-data-path "/mnt/data_in/extremesealevel2_AFs_fulldata/esl_data/gesla3_data" \
--quantile-min 0.01 \
--quantile-max 0.99 \
--quantile-step 0.01 \
--reffreq-data "custom" \
--reffreq-data-file "/mnt/data_in/extremesealevel2_AFs_fulldata/refFreqs/flopros_estimates_at_coastrp_locations.nc" \
--target-AFs 20 \
--output-fname "/mnt/data_out/project_ESL_output.nc" \
--output-dir "/mnt/data_int" \
--below-threshold "mhhw"
```

## Features 
```shell
Usage: extremesealevel2-afs [OPTIONS]

Options:
  --min-years INTEGER             Minimum number of years available.
                                  [default: 20]
  --resample-freq TEXT            Frequency to resample the raw data to prior
                                  to ESL analysis.  [default: D_max]
  --deseasonalize BOOLEAN         Boolean to indicate whehter to remove mean
                                  seasonal cycle prior to ESL analysis.
                                  [default: True]
  --detrend BOOLEAN               Boolean to indicate whether to remove linear
                                  trend prior to ESL analysis.  [default:
                                  True]
  --subtract-amean BOOLEAN        Boolean to indicate whether to remove annual
                                  means prior to ESL analysis.  [default:
                                  False]
  --match-lim FLOAT               Radius around requested locations to find a
                                  matching tide gauge in GESLA database (km).
                                  [default: 10.0]
  --gpd-pot-threshold FLOAT       Percentile for GPD analysis.  [default:
                                  99.0]
  --decluster-window INTEGER      Maximum number of days that define a cluster
                                  for extreme events.  [default: 3]
  --decluster-method TEXT         Method to use for declustering peaks.
                                  [default: rolling_max]
  --nsamps INTEGER                Number of samples to draw.  [default: 2000]
  --total-localsl-file TEXT       Total localized sea-level projection file.
                                  Site lats/lons are taken from this file and
                                  mapped to the GESLA database.
  --reffreq-data TEXT             Which protection level frequencies data to
                                  use  [default: 0.01]
  --reffreq-data-file TEXT        Directory or file containing requested
                                  protection level frequencies data
  --esl-data TEXT                 Type of data used for the ESL analysis.
                                  [default: gesla3]
  --esl-data-path TEXT            Directory containing requested ESL data.
  --pipeline-id TEXT              Unique identifier for this instance of the
                                  module.
  --esl-fit-statistics-file TEXT  Path to output ESL statistics file.
                                  [required]
  --quantile-min FLOAT            Minimum quantile to assess.  [default: 0.5]
  --quantile-max FLOAT            Maximum quantile to assess.  [default: 0.99]
  --quantile-step FLOAT           Quantile step  [default: 0.01]
  --target-years TEXT             Comma-delimited list of years to project AFs
                                  for (set to none for no output).  [default:
                                  2050,2100]
  --target-AFs TEXT               Comma-delimited list to AFs to project
                                  timing for (set to none for no output).
                                  [default: 20]
  --target-freqs FLOAT            [default: 1.0]
  --output-fname TEXT             Path to output ESL AFs file.
  --below-threshold TEXT          How to model events below the GPD threshold
                                  (default= log linear extrapolation to mhhw).
  --output-dir TEXT               Directory to save output files.
  --help                          Show this message and exit.
```

See the above by running:
```shell
docker run --rm extremesealevel2-afs --help
```

## Results
If successful, this program will write two NetCDF files to `./data/output`. 

## Support
Source code is available online at https://github.com/fact-sealevel/extremesealevel2-AFs. This software is open source, available under the MIT license.

Please file issues in the issue tracker at https://github.com/fact-sealevel/extremesealevel2-AFs/issues.