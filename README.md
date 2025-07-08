# SyCLoPS

Author:  Yushan Han
Email:   yshhan@ucdavis.edu

Copyright 2025 Yushan Han

Introduction
=====

The System for classification of Low-Pressure Systems (SyCLoPS) is an all-in-one framework for objective detection and classification of any type of surface low-pressure systems (LPSs) in any large atmospheric dataset and model outputs in one workflow. The required atmopsheric variables for the framework can be found at `manual/Required_variable.png`. SyCLoPS is capable of labeling the following types of LPS:

| LPS node Label         | LPS Full Name                                      |
|------------------------|----------------------------------------------------|
| HAL / HATHL            | High-altitude Low / High-altitude Thermal Low      |
| THL / DOTHL            | Thermal Low / Deep (Orographic) Thermal Low        | 
| DSD / DST / DSE        | Dry / Tropical/ Extratropical Disturbance          |
| TC                     | Tropical Cyclone                                   |
| TD / TD(MD)            | Tropical Depression / TD (Monsoon Depression)      |
| TLO / TLO(ML)          | Tropical Low / TLO (Monsoon Low)                   |
| SS(STLC) / PL(PTLC)    | Subtropical Storm (Subtropical Tropical-Like Cyclone) / Polar Low (Polar TLC) |
| SC / EX                | Subtropical Cyclone / Extratropical Cyclone        |

It also labels the four high-impact LPS tracks: TC, MS (Monsoonal System), SS(STLC), and PL(PTLC) tracks. Tracks are labeled when LPSs are stably labeld as a type of LPS class for a period of time so it can be compared with the corresponding subjective dataset.

Dependencies
=====

The SyCLoPS software is built upon TempestExtremes (TE), the state-of-the-art atmospheric feature detector. The main TE branch can be downloaded here: [https://github.com/ClimateGlobalChange/tempestextremes/tree/master] (Please see the note below.)

**Note:** The main TE branch now lacks the ability to deal with large missing values in datasets (e.g. 1e20), this will result in unreasonable values in the classification process for some datasets. NaNs as missing values are safe to proceed with. We are working on this issue and users can expect a newer TE version with fixes in the near future. For now, users can install this fork of TempestExtremes via CMAKE, which can be found here: [https://github.com/yepkids/tempestextremes], to work around this problem. This fork provides a temporary solution that adds missing value support for operators used by SyCLoPS and has been tested. Note that this is not a stable release, and please report any problems with this fork to Yushan Han (yshhan@ucdavis.edu). You can also choose to convert all missing values in your input files to NaNs.

The SyCLoPS software requires the following Python packages: Xarray, Pandas, PyArrow, multiprocess, and Scipy.

Usage
=====

Simply download the SyCLoPS folder to your machine. Then: 

1. Review the codes and comments in `SyCLoPS_main.py`. Change variable names and other specifications according to your needs.

2. Run `SyCLoPS_main.py` and follow the instructions carefully.

Optional steps for tagging precipitation and size blobs of LPSs can be found in the `optional` folder.


Documentation
=====

1. SyCLoPS manual (in PDF) can be found in the `manual` folder and can also found online here (the online version may be lagging): 
https://climate.ucdavis.edu/syclops.php

2. Details of the various executables that are part of TempestExtremes (TE) can be found in the user guide:
https://climate.ucdavis.edu/tempestextremes.php


Publications
============
If you use the SycLoPS software please cite our publications:

[https://doi.org/10.1029/2024JD041287] Han, Y. and P.A. Ullrich (2025) "The System for Classification of Low-Pressure Systems (SyCLoPS): An all-in-one objective framework for large-scale datasets" J. Geophys. Res. Atm. 130 (1), e2024JD041287, doi: 10.1029/2024JD041287.

[https://dx.doi.org/10.5194/gmd-14-5023-2021] Ullrich, P.A., C.M. Zarzycki, E.E. McClenny, M.C. Pinheiro, A.M. Stansfield and K.A. Reed (2021) "TempestExtremes v2.1: A community framework for feature detection, tracking and analysis in large datasets" Geosci. Model. Dev. 14, pp. 5023–5048, doi: 10.5194/gmd-14-5023-2021.

[http://dx.doi.org/10.5194/gmd-2016-217] Ullrich, P.A. and C.M. Zarzycki (2017) "TempestExtremes v1.0: A framework for scale-insensitive pointwise feature tracking on unstructured grids" Geosci. Model. Dev. 10, pp. 1069-1090, doi: 10.5194/gmd-10-1069-2017. 
