import pandas as pd
import numpy as np
from extremesealevel2_AFs.I_O import (
    get_refFreqs,
    lazy_output_to_ds,
)
import dask
from extremesealevel2_AFs.esl_analysis import (
    multivariate_normal_gpd_samples_from_covmat,
    get_return_curve_gpd,
)
from extremesealevel2_AFs.projecting import compute_AFs, compute_AF_timing
from extremesealevel2_AFs.utils import if_scalar_to_list
from dask.distributed import LocalCluster

# Do not warn about chained assignments
pd.options.mode.chained_assignment = None  # default='warn'

""" extremesealevel2_AFs_project.py
written by: Tim Hermans t.h.j.hermans@uu.nl (May 2024)
Projecting stage of extremesealevel2 module of FACTS.
"""


###from projectESL (https://github.com/Timh37/projectESL):
def compute_projectESL_output(
    loc,
    scale,
    shape,
    rate,
    cov,
    mhhw,
    f,
    below_threshold,
    n_samples,
    refFreq,
    input_locations,
    out_qnts,
    target_years,
    target_AFs,
    target_freqs,
    z_hist=None,
):

    if z_hist is not None:  # if return curve already provided
        z = z_hist

    else:  # derive return curves from GPD samples
        if cov is not None:  # generate scale and shape samples
            scale_samples, shape_samples = multivariate_normal_gpd_samples_from_covmat(
                scale, shape, cov, n_samples, 0
            )
        else:  # use best estimates (means) or provided samples
            scale_samples, shape_samples = (
                scale,
                shape,
            )  # use central estimate scale & shape

        z = get_return_curve_gpd(
            f, scale_samples, shape_samples, loc, rate, below_threshold, mhhw
        )  # compute return curve samples

    # compute quantiles of output:
    if z.ndim > 1:
        z_hist_quantiles = np.quantile(
            z, out_qnts, axis=-1
        )  # dont have to use nanquantile, because either defined for all samples or for none

    else:
        z_hist_quantiles = np.repeat(
            z[None, :], len(out_qnts), axis=0
        )  # central estimate parameters used to compute z, so there is no uncertainty in z_hist --> repeat

    if len(target_years) > 0:  # compute AFs for target years
        slr_in = input_locations.sea_level_change.sel(years=target_years)

        af, max_af, z_fut = compute_AFs(
            f=f,
            z_hist=z,
            slr=slr_in,  # input_locations.sea_level_change.sel(years=target_years),
            refFreq=refFreq,
        )
        z_fut_quantiles = np.quantile(z_fut, out_qnts, axis=1)
        af_quantiles = np.quantile(af, out_qnts, axis=0)

    else:
        af_quantiles = np.nan
        max_af = np.nan
        z_fut_quantiles = np.nan

    if len(target_AFs) > 0:  # compute timing of target AFs
        af_timing = []
        for target_af in np.array(target_AFs):  # loop over target AFs to compute timing
            af_timing.append(
                compute_AF_timing(
                    f, z, input_locations.sea_level_change, refFreq, target_af
                )
            )

        af_timing_quantiles = np.quantile(np.vstack((af_timing)), out_qnts, axis=-1)
        af_timing_quantiles = np.round(
            np.where(
                af_timing_quantiles >= input_locations.years[-1].values,
                9999,
                af_timing_quantiles,
            )
        )
    else:
        af_timing_quantiles = np.nan

    if len(target_freqs) > 0:  # compute timing of target AFs
        f_timing = []
        for target_freq in np.array(
            target_freqs
        ):  # loop over target AFs to compute timing
            f_timing.append(
                compute_AF_timing(
                    f,
                    z,
                    input_locations.sea_level_change,
                    refFreq,
                    np.round(target_freq / refFreq).astype("int"),
                )
            )

        f_timing_quantiles = np.quantile(np.vstack((f_timing)), out_qnts, axis=-1)
        f_timing_quantiles = np.round(
            np.where(
                f_timing_quantiles >= input_locations.years[-1].values,
                9999,
                f_timing_quantiles,
            )
        )
    else:
        f_timing_quantiles = np.nan

    return (
        z_hist_quantiles,
        z_fut_quantiles,
        af_quantiles,
        max_af,
        af_timing_quantiles,
        f_timing_quantiles,
    )


def project_ESLs_lazily(
    esl_statistics,
    f,
    below_threshold,
    n_samples,
    refFreqs,
    input_locations,
    out_qnts,
    target_years,
    target_AFs,
    target_freqs,
):

    target_years = if_scalar_to_list(target_years)
    target_AFs = if_scalar_to_list(target_AFs)
    target_freqs = if_scalar_to_list(target_freqs)

    locs = scales = shapes = rates = covs = mhhws = z_hists = [
        None for k in esl_statistics.locations
    ]  # initialize input parameters for each location with None

    if "z_hist" in esl_statistics:  # if return curves provided, use these as input
        z_hists = esl_statistics["z_hist"].values

    else:  # else use GPD parameters as input
        locs = esl_statistics["loc"].values
        scales = esl_statistics["scale"].values
        shapes = esl_statistics["shape"].values
        rates = esl_statistics["avg_extr_pyear"].values

        if "cov" in esl_statistics:  # if covariance matrix is provided, use it
            covs = [k.tolist() for k in esl_statistics["cov"].values]

        elif (
            "scale_samples" in esl_statistics and "shape_samples" in esl_statistics
        ):  # if scale/shape samples provided directly
            scales = esl_statistics["scale_samples"].values
            shapes = esl_statistics["shape_samples"].values

        if "mhhw" in esl_statistics:
            mhhws = esl_statistics["mhhw"].values
        else:
            if below_threshold == "mhhw":
                print(
                    'Warning: cannot compute return heights below threshold using "mhhw" because MHHW value is not available from ESL data. Continuing without modeling below threshold.'
                )
                below_threshold = None
    lazy_results = []

    for i, location in enumerate(esl_statistics.locations):
        lazy_result = dask.delayed(compute_projectESL_output)(
            locs[i],
            scales[i],
            shapes[i],
            rates[i],
            covs[i],
            mhhws[i],
            f,
            below_threshold,
            n_samples,
            refFreqs[i],
            input_locations.sel(locations=location),
            out_qnts,
            target_years,
            target_AFs,
            target_freqs,
            z_hists[i],
        )
        lazy_results = np.append(lazy_results, lazy_result)

    return lazy_results


def project_ESL_runner(
    quantile_min,
    quantile_max,
    quantile_step,
    target_years,
    target_AFs,
    target_freqs,
    reffreq_data,
    reffreq_data_file,
    input_locations,
    esl_statistics_ds,
    output_fname,
    f,
    below_threshold,
    n_samples,
):
    out_qnts = np.arange(quantile_min, quantile_max + quantile_step, quantile_step)

    if target_years != "none":
        target_years = np.array(str(target_years).split(",")).astype("int")
    else:
        target_years = []

    if target_AFs != "none":
        target_AFs = np.array(str(target_AFs).split(",")).astype("int")
    else:
        target_AFs = []

    cluster = LocalCluster()
    _client = cluster.get_client()

    f = 10 ** np.linspace(
        -6, 2, num=1001
    )  # input frequencies to compute return heights for
    f = np.append(f, np.arange(101, 183))
    if np.array(reffreq_data).dtype == "int" or np.array(reffreq_data).dtype == "float":
        reffreqs = get_refFreqs(reffreq_data, input_locations, esl_statistics_ds)
    else:
        reffreqs = get_refFreqs(
            refFreq_data=reffreq_data,
            input_locations=input_locations,
            esl_statistics=esl_statistics_ds,
            path_to_refFreqs=reffreq_data_file,
        )

    output = dask.compute(
        *project_ESLs_lazily(
            esl_statistics_ds,
            f,
            below_threshold,
            n_samples,
            reffreqs,
            input_locations,
            out_qnts,
            target_years,
            target_AFs,
            target_freqs,
        )
    )
    output_ds = lazy_output_to_ds(
        output, f, out_qnts, esl_statistics_ds, target_years, target_AFs, target_freqs
    )
    output_ds["refFreq"] = (["locations"], reffreqs)

    output_ds.to_netcdf(
        output_fname,
        mode="w",
    )