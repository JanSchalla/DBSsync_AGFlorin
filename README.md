# DBSsync_GUI

Adaptaions:
 - A timestamp.txt file is created with the marked timestamps of the intra- and extracranial artifacts.
 - combine_megANDlfp.py combines MEG data with LFP data into one .fif file. LFP is upsampled to MEG sampling frequency. LFP Channels are saved as MISC channels in .fif file. artifact_timestamp_YYYYMMDD_HHMMSS.txt file is needed to get timings of artifacts.

This repository is attached to a manuscript which has been submitted for publication on November, the 28th 2025. A preprint describing the toolbox design and functionnalities is available at: https://www.researchsquare.com/article/rs-8228751/v1

Instructions:

1. Clone this repository
2. Create a virtual environment using anaconda prompt as explained in the Create virtual env.txt file
3. Run the script called "DBSsync_main.py"
4. To have more information about how to use the GUI, click on the Help button in the GUI Menu

More detailed instructions and explanations about the GUI can be found in the "Documentation DBSsync GUI.pdf" file.
