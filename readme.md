## How to Run

IMPORTANT: Always run from the project root folder.

Example:

cd alm_ir_hedging_prototype

Running example notebooks:
jupyter notebook

Notes:

* The project assumes the working directory is the root folder.
* If you see import errors, check your current directory.

* The app_data folder contains parquet files for the
  dashboard. These files are produced by an associated
  project (=> alm_ir_hedging_app), packaged in a separate repo. 
  
  The src/data_pipeline/data_pipeline.py module in 
  the alm_ir_hedging_prototype prepares a batch of calculations
  for the streamlit app.

* These parquet files are saved in src/streamlit_app_data/parquet_files 
  folder of the alm_ir_hedging_prototype project, and must be manually 
  moved to the app_data folder. 
