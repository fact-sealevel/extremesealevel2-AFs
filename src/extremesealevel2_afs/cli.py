import click
import logging
import numpy as np
from extremesealevel2_afs.extremesealevel2_AFs_preprocess import preprocess


from extremesealevel2_afs.extremesealevel2_AFs_fit import (
    get_ESL_statistics,
)



from extremesealevel2_afs.extremesealevel2_AFs_project import project_ESL_runner


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@click.command()
@click.option(
    "--min-years",
    type=int,
    default=20,
    show_default=True,
    help="Minimum number of years available.",
)
@click.option(
    "--resample-freq",
    type=str,
    default="D_max",
    show_default=True,
    help="Frequency to resample the raw data to prior to ESL analysis.",
)
@click.option(
    "--deseasonalize",
    type=bool,
    default=True,
    show_default=True,
    help="Boolean to indicate whehter to remove mean seasonal cycle prior to ESL analysis.",
)
@click.option(
    "--detrend",
    type=bool,
    default=True,
    show_default=True,
    help="Boolean to indicate whether to remove linear trend prior to ESL analysis.",
)
@click.option(
    "--subtract-amean",
    type=bool,
    default=False,
    show_default=True,
    help="Boolean to indicate whether to remove annual means prior to ESL analysis.",
)
@click.option(
    "--match-lim",
    type=float,
    default=10.0,
    show_default=True,
    help="Radius around requested locations to find a matching tide gauge in GESLA database (km).",
)
@click.option(
    "--gpd-pot-threshold",
    type=float,
    default=99.0,
    show_default=True,
    help="Percentile for GPD analysis.",
)
@click.option(
    "--decluster-window",
    type=int,
    default=3,
    show_default=True,
    help="Maximum number of days that define a cluster for extreme events.",
)
@click.option(
    "--decluster-method",
    type=str,
    default="rolling_max",
    show_default=True,
    help="Method to use for declustering peaks.",
)
@click.option(
    "--nsamps",
    type=int,
    default=2000,
    show_default=True,
    help="Number of samples to draw.",
)
@click.option(
    "--total-localsl-file",
    type=str,
    help="Total localized sea-level projection file. Site lats/lons are taken from this file and mapped to the GESLA database.",
)
@click.option(
    "--reffreq-data",
    type=str,
    default=0.01,
    show_default=True,
    help="Which protection level frequencies data to use",
)
@click.option(
    "--reffreq-data-file",
    type=str,
    help="Directory or file containing requested protection level frequencies data",
)
@click.option(
    "--esl-data",
    type=str,
    default="gesla3",
    show_default=True,
    help="Type of data used for the ESL analysis.",
)
@click.option(
    "--esl-data-path",
    type=str,
    help="Directory containing requested ESL data.",
)
@click.option(
    "--pipeline-id",
    type=str,
    help="Unique identifier for this instance of the module.",
)
@click.option(
    "--esl-fit-statistics-file",
    type=str,
    help="Path to output ESL statistics file.",
    required=True,
)
@click.option(
    "--quantile-min",
    type=float,
    default=0.5,
    show_default=True,
    help="Minimum quantile to assess.",
)
@click.option(
    "--quantile-max",
    type=float,
    default=0.99,
    show_default=True,
    help="Maximum quantile to assess.",
)
@click.option(
    "--quantile-step",
    type=float,
    default=0.01,
    show_default=True,
    help="Quantile step",
)
@click.option(
    "--target-years",
    type=str,
    default="2050,2100",
    show_default=True,
    help="Comma-delimited list of years to project AFs for (set to none for no output).",
)
@click.option(
    "--target-AFs",
    type=str,
    default=20,
    show_default=True,
    help="Comma-delimited list to AFs to project timing for (set to none for no output).",
)
@click.option(
    "--target-freqs",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--output-fname",
    type=str,
    help="Path to output ESL AFs file.",
)
@click.option(
    "--below-threshold",
    type=str,
    default="mhhw",
    help="How to model events below the GPD threshold (default= log linear extrapolation to mhhw).",
)
@click.option(
    "--output-dir",
    type=str,
    help="Directory to save output files.",
)
def main(
    min_years,
    pipeline_id,
    esl_fit_statistics_file,
    resample_freq,
    deseasonalize,
    detrend,
    subtract_amean,
    match_lim,
    gpd_pot_threshold,
    decluster_window,
    decluster_method,
    nsamps,
    total_localsl_file,
    esl_data,
    esl_data_path,
    quantile_min,
    quantile_max,
    quantile_step,
    reffreq_data,
    reffreq_data_file,
    target_years,
    target_afs,
    target_freqs,
    output_fname,
    below_threshold,
    output_dir,
):

    click.echo("Hello from extremesealevel2-AFs!")

    # call fit preprocess function
    preproc_settings, input_locations = preprocess(
        min_years=min_years,
        resample_freq=resample_freq,
        deseasonalize=deseasonalize,
        detrend=detrend,
        subtract_amean=subtract_amean,
        gpd_pot_threshold=gpd_pot_threshold,
        decluster_window=decluster_window,
        decluster_method=decluster_method,
        nsamps=nsamps,
        total_localsl_file=total_localsl_file,
    )

    f = 10 ** np.linspace(
        -6, 2, num=1001
    )  # input frequencies to compute return heights for
    f = np.append(f, np.arange(101, 183))

    # Create fit ds
    extremesl_fit = get_ESL_statistics(
        esl_data=esl_data,
        path_to_data=esl_data_path,
        input_locations=input_locations,
        match_dist_limit=match_lim,
        preproc_settings=preproc_settings,
        n_samples=nsamps,
        f=f,
        output_dir=output_dir,
    )
    # write fit ds
    extremesl_fit.to_netcdf(esl_fit_statistics_file, mode="w")

    target_freqs = np.array(str(target_freqs).split(",")).astype("float")

    project_ESL_runner(
        quantile_min=quantile_min,
        quantile_max=quantile_max,
        quantile_step=quantile_step,
        target_years=target_years,
        target_AFs=target_afs,
        target_freqs=target_freqs,
        reffreq_data=reffreq_data,
        reffreq_data_file=reffreq_data_file,
        input_locations=input_locations,
        esl_statistics_ds=extremesl_fit,
        output_fname=output_fname,
        f=f,
        below_threshold=below_threshold,
        n_samples=nsamps,
    )