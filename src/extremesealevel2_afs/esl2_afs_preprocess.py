import numpy as np
from extremesealevel2_afs.I_O import (
    open_input_locations,
)

import logging
# from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# @dataclass
# class PreprocessOutput:
#    preprocess_settings: dict
#    input_locations


def preprocess(
    min_years,
    resample_freq,
    deseasonalize,
    detrend,
    subtract_amean,
    decluster_method,
    decluster_window,
    gpd_pot_threshold,
    # esl_data,
    # esl_data_path,
    total_localsl_file,
    nsamps,
):
    preproc_settings = {}
    preproc_settings["min_yrs"] = min_years
    preproc_settings["store_esls"] = False
    preproc_settings["resample_freq"] = resample_freq
    preproc_settings["deseasonalize"] = deseasonalize
    preproc_settings["detrend"] = detrend
    preproc_settings["subtract_amean"] = subtract_amean
    preproc_settings["ref_to_msl"] = 0
    preproc_settings["declus_method"] = decluster_method
    preproc_settings["declus_window"] = decluster_window
    preproc_settings["extremes_threshold"] = gpd_pot_threshold

    # esl_data        = esl_data
    # esl_data_path   = esl_data_path
    sl_fn = total_localsl_file
    n_samples = nsamps

    f = 10 ** np.linspace(
        -6, 2, num=1001
    )  # input frequencies to compute return heights for
    f = np.append(f, np.arange(101, 183))

    input_locations = open_input_locations(sl_fn, n_samples)

    return (preproc_settings, input_locations)

    # extremesl_fit = get_ESL_statistics(esl_data,esl_data_path,input_locations,args.match_lim,preproc_settings,n_samples,f)
    # extremesl_fit.to_netcdf(os.path.join(os.path.dirname(__file__),'{}_esl_statistics.nc'.format(args.pipeline_id)),mode='w')
