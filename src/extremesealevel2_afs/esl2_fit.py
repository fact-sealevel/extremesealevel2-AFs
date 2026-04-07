import pandas as pd
import os
import numpy as np
import argparse
from extremesealevel2_afs.I_O import open_input_locations, esl_statistics_dict_to_ds, open_gpd_parameters,get_coast_rp_return_curves
from extremesealevel2_afs.esl_analysis import ESL_stats_from_raw_GESLA, ESL_stats_from_gtsm_dmax

# Do not warn about chained assignments
pd.options.mode.chained_assignment = None  # default='warn'

""" extremesealevel2_AFs_fit.py
written by: Tim Hermans t.h.j.hermans@uu.nl (May 2024)
Fitting stage of extremesealevel2 module of FACTS.
"""

def get_ESL_statistics(
    esl_data,
    path_to_data,
    input_locations,
    match_dist_limit,
    output_dir,
    preproc_settings=None,
    n_samples=None,
    f=None):
    print('Extracting ESL information for queried input locations...')
    esl_statistics = {} #initialize dictionary to hold ESL information
    esl_data = esl_data.lower()

    if esl_data == 'gesla3_data':
        esl_data = 'gesla3'
    #derive ESL statistics:

    if esl_data in ['gesla2','gesla3']: #options were gesla2 adn gesla3 #from raw GESLA data
        esl_statistics = ESL_stats_from_raw_GESLA(
            gesla_version = esl_data,
            path_to_gesla = path_to_data,
            input_locations = input_locations,
            output_dir = output_dir,
            preproc_settings = preproc_settings,
            match_dist_limit = match_dist_limit) #dictionary output
        esl_statistics = esl_statistics_dict_to_ds(input_locations,esl_statistics)

    elif esl_data.lower() in ['gtsm_dmax']: #from raw daily maxima from GTSM
        esl_statistics = ESL_stats_from_gtsm_dmax(path_to_data,input_locations,preproc_settings,match_dist_limit)

    elif esl_data.lower() in ['hermans2023','kirezci2020','vousdoukas2018','gtsm_dmax_gpd']: #from pre-made statistics
        esl_statistics = open_gpd_parameters(esl_data,path_to_data,input_locations,n_samples,match_dist_limit)

    elif esl_data.lower() == 'coast-rp': #from COAST-RP return curves
        esl_statistics = get_coast_rp_return_curves(path_to_data,input_locations,f,match_dist_limit)
    else:
        raise Exception('ESL input data type not recognized.')
    esl_statistics.to_netcdf(os.path.join(os.path.dirname(__file__),'aaa_ESL_statistics_ds.nc'),mode='w') #store output ds

    return esl_statistics

def fit_preprocess(
    min_years,
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
    pipeline_id):

    preproc_settings = {}
    preproc_settings['min_years'] = min_years
    preproc_settings['store_esls'] = False
    preproc_settings['resample_freq'] = resample_freq
    preproc_settings['deseasonalize'] = deseasonalize
    preproc_settings['detrend'] = detrend
    preproc_settings['subtract_amean'] = subtract_amean
    preproc_settings['ref_to_msl'] = 0
    preproc_settings['declus_method'] = decluster_method
    preproc_settings['declus_window'] = decluster_window
    preproc_settings['extremes_threshold'] = gpd_pot_threshold

    #esl_data        = esl_data
    #esl_data_path   = esl_data_path
    #sl_fn           = total_localsl_file
    n_samples       = nsamps

    f= 10**np.linspace(-6,2,num=1001) #input frequencies to compute return heights for
    f=np.append(f,np.arange(101,183))


    return (esl_data,
            esl_data_path,
            total_localsl_file,
            preproc_settings,
            n_samples,
            f,
            )
