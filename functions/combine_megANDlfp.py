#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 17:44:48 2026

@author: jan
"""

import mne
import json
import os
from pathlib import Path
import shutil


raw_lfp_fname = '/home/jan/Desktop/SyncTest/run001/SYNCHRONIZED_INTRACRANIAL_CLEANED_Report_Json_Session_Report_20260121T134518_raw.fif'
raw_meg_fname = '/home/jan/Desktop/SyncTest/run001/SYNCHRONIZED_EXTERNAL_SCTSFB002PD_medON_stimON_run001_260121_raw.fif'
timestamps_fname = '/home/jan/Desktop/SyncTest/run001/artifact_timestamps_20260429_121415.txt'

def combine_meg_and_lfp(raw_meg_fname, raw_lfp_fname, timestamps_fname, 
                        start_crop=2, end_crop=2,
                        deleteFiles=True):
    
    """
   Align, crop, and combine MEG and LFP recordings into a single MNE Raw object.

   This function:
   1. Loads MEG and LFP FIF files.
   2. Reads synchronization timestamps from a JSON file.
   3. Converts artifact sample indices to time (seconds).
   4. Resamples LFP data to match the MEG sampling frequency.
   5. Crops both signals to a shared time window based on detected artifacts.
   6. Extracts selected LFP channels and appends them to the MEG data.
   7. Saves the combined dataset to disk.
   8. Optionally deletes the original synchronization directory.

   Parameters
   ----------
   raw_meg_fname : str or pathlib.Path
       Path to the MEG raw FIF file.
   raw_lfp_fname : str or pathlib.Path
       Path to the LFP raw FIF file.
   timestamps_fname : str or pathlib.Path
       Path to JSON file containing synchronization timestamps.
   start_crop : float, optional
       Time (in seconds) to crop from the start after alignment (default: 2).
   end_crop : float, optional
       Time (in seconds) to crop from the end after alignment (default: 2).
   deleteFiles : bool, optional
       If True, deletes the directory containing the original MEG file
       (assumed to be intermediate DBSSync output).

   Returns
   -------
   None
       The combined dataset is saved to disk.

   Notes
   -----
   - LFP data is resampled to match MEG sampling frequency.
   - Only channels 'Channel_ONE_THREE_LEFT' and 'Channel_ONE_THREE_RIGHT'
     are retained from the LFP recording.
   - Output filename is derived from the MEG filename by removing
     'SYNCHRONIZED_EXTERNAL_' and inserting '_aligned' before '_raw'.
   - Use caution with `deleteFiles=True`, as it permanently removes directories.
   """
    
    #%% Define Outdir
    out_dir = Path(raw_meg_fname).parent.parent
    
    dir2delete = Path(raw_meg_fname).parent
    
    # Modify filename
    new_name = Path(raw_meg_fname).name.replace('SYNCHRONIZED_EXTERNAL_', '').replace('_raw', '_aligned_raw')
    
    out_fname = out_dir / new_name
    
    #%% Step 1:
    # Import data
    raw_lfp = mne.io.read_raw_fif(raw_lfp_fname)
    raw_meg = mne.io.read_raw_fif(raw_meg_fname)
    
    fs_meg = raw_meg.info['sfreq']
    fs_lfp = raw_lfp.info['sfreq']
    
    with open(timestamps_fname, 'r') as f:
        timestamps = json.load(f)
     
    # Convert samples to timepoints in seconds
    lfp_first_artifact = (timestamps['intracranial']['first_artifact']['sample_index'] - fs_lfp) / fs_lfp 
    lfp_last_artifact = (timestamps['intracranial']['last_artifact']['sample_index'] - fs_lfp) / fs_lfp
    
    meg_first_artifact = (timestamps['extracranial']['first_artifact']['sample_index'] - fs_meg) / fs_meg
    meg_last_artifact = (timestamps['extracranial']['last_artifact']['sample_index'] - fs_meg) / fs_meg
    
    
    #%% Step 2:
    # Resample
    lfp_resampled = raw_lfp.copy().resample(fs_meg)
    fs_lfp_resampled = lfp_resampled.info['sfreq']
    
    #%% Step 3:
    # Crop Timeseries
    lfp_cropped = lfp_resampled.copy().crop(tmin=start_crop, tmax = lfp_last_artifact - lfp_first_artifact - end_crop)
    meg_cropped = raw_meg.copy().crop(tmin=start_crop, tmax = meg_last_artifact - meg_first_artifact - end_crop)
    
    # Sanity Check
    lfp_dur = len(lfp_cropped.times)/fs_lfp_resampled
    meg_dur = len(meg_cropped.times)/fs_meg
    
    print(f'Differnce between MEG- and LFP-Signals is: {meg_dur - lfp_dur}s.')
    
    if meg_dur != lfp_dur:
        print('Adjusting length to the shorter signal!')
        min_len = min(lfp_cropped.n_times, meg_cropped.n_times)
        lfp_cropped = lfp_cropped[:, :min_len]
        meg_cropped = meg_cropped[:, :min_len]
    
    #%% Step 4:
    # Join datastrems
    lfp_cropped = lfp_cropped.pick(['Channel_ONE_THREE_LEFT','Channel_ONE_THREE_RIGHT']).get_data()
    lfp_new = mne.io.RawArray(lfp_cropped, mne.create_info(['LFP_left', 'LFP_right'], sfreq=fs_lfp_resampled, ch_types=['dbs', 'dbs']))
    meg_cropped = meg_cropped.load_data().add_channels([lfp_new], force_update_info=True)
    
    print(f'Saving data to: {out_fname}...')
    meg_cropped.save(out_fname, overwrite=True)
    print('Finished saving.')
    
    #%% Step 5:
    # Delete DBSSync files    
    if deleteFiles:
        print('Deleting input files (from DBSSync) ...')
        print(f"Deleting directory: {dir2delete}")
        if dir2delete.exists() and dir2delete.is_dir():
            shutil.rmtree(dir2delete)