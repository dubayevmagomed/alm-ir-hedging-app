from __future__ import annotations
from typing import Dict
from pathlib import Path
import os 
import sys
import pandas as pd 

def parquet_loader(
    ) -> Dict[str, pd.DataFrame]:
    
    PROJECT_ROOT = ""
    for parent in Path(__file__).parents:
        if (parent / "src").exists():
           PROJECT_ROOT = parent 
           APP_DATA_PATH = PROJECT_ROOT / "app_data"
           break
       
    os.chdir(APP_DATA_PATH)
    
    data_dict = {}
    data_dict["curve"] = {
        "nodes": pd.read_parquet("curve_nodes.parquet"),
        "disc_factors": pd.read_parquet("curve_disc_factors.parquet"),
        "spot_zero_rates": pd.read_parquet("curve_spot_zero_rates.parquet"),
        "spot_par_rates": pd.read_parquet("curve_spot_par_rates.parquet"),
        "fwd_par_rates": pd.read_parquet("curve_fwd_par_rates.parquet"),
        "pca_eigvals": pd.read_parquet("curve_pca_eigvals.parquet"),
        "pca_eigvecs": pd.read_parquet("curve_pca_eigvecs.parquet"),
        "pca_loadings": pd.read_parquet("curve_pca_loadings.parquet")
    }

    data_dict["scenarios"] = {
        "hist_rates": pd.read_parquet("scenarios_hist_rates.parquet"),
        "hist_shifts": pd.read_parquet("scenarios_hist_shifts.parquet"),
        "hist_cov_mat": pd.read_parquet("scenarios_hist_cov_mat.parquet"),
        "hist_corr_mat": pd.read_parquet("scenarios_hist_corr_mat.parquet"),
        "sim_rates": pd.read_parquet("scenarios_sim_rates.parquet"),
        "sim_shifts": pd.read_parquet("scenarios_sim_shifts.parquet"),
        "pca_eigvals": pd.read_parquet("scenarios_pca_eigvals.parquet"),
        "pca_eigvecs": pd.read_parquet("scenarios_pca_eigvecs.parquet"),
        "pca_loadings": pd.read_parquet("scenarios_pca_loadings.parquet"),
        "sim_pc_multipliers": pd.read_parquet("scenarios_sim_pc_multipliers.parquet"),
        "sim_parameters": pd.read_parquet("scenarios_sim_parameters.parquet")       
    }
    
    data_dict["liability_position"] = {
        "cashflows": pd.read_parquet("lby_pos_cashflows.parquet"),
        "spot_delta": pd.read_parquet("lby_pos_spot_delta.parquet"),
        "fwd_delta": pd.read_parquet("lby_pos_fwd_delta.parquet"),
        "pcm_delta": pd.read_parquet("lby_pos_pcm_delta.parquet"),
        "spot_gamma": pd.read_parquet("lby_pos_spot_gamma.parquet"), 
        "cashflow_zcb_positions" : pd.read_parquet("lby_pos_cashflow_zcb_positions.parquet")
    }

    data_dict["liability_hedge"] = {
        "full_hedge_instruments": pd.read_parquet("lby_hedge_full_hedge_instruments.parquet"),
        "liquid_hedge_instruments": pd.read_parquet("lby_hedge_liquid_hedge_instruments.parquet")      
    }

    data_dict["liability_portfolio"] = {
        "cashflows": pd.read_parquet("lby_prtfl_cashflows.parquet"),
        "npv": pd.read_parquet("lby_prtfl_npv.parquet"),
        "spot_delta": pd.read_parquet("lby_prtfl_spot_delta.parquet"),
        "fwd_delta": pd.read_parquet("lby_prtfl_fwd_delta.parquet"),
        "spot_gamma": pd.read_parquet("lby_prtfl_spot_gamma.parquet"),
        "sim_pos_pnl": pd.read_parquet("lby_prtfl_sim_pos_pnl.parquet"),
        "sim_pos_grp_pnl": pd.read_parquet("lby_prtfl_sim_pos_grp_pnl.parquet"),
        "sim_prtfl_pnl": pd.read_parquet("lby_prtfl_sim_prtfl_pnl.parquet"),
        "cvar_scenarios": pd.read_parquet("lby_prtfl_cvar_scenarios.parquet"),
        "pv01_delta_cvar_attr": pd.read_parquet("lby_prtfl_pv01_delta_cvar_attr.parquet"), 
        "prtfl_cvar" : pd.read_parquet("lby_prtfl_prtfl_cvar.parquet"), 
        "pos_grp_cvar": pd.read_parquet("lby_prtfl_pos_grp_cvar.parquet"),
        "pos_cvar": pd.read_parquet("lby_prtfl_pos_cvar.parquet"), 
        "positions": pd.read_parquet("lby_prtfl_positions.parquet")      
    }

    data_dict["liability_full_hedge_portfolio"] = {
        "cashflows": pd.read_parquet("lby_prtfl_full_hedge_cashflows.parquet"),
        "npv": pd.read_parquet("lby_prtfl_full_hedge_npv.parquet"),
        "spot_delta": pd.read_parquet("lby_prtfl_full_hedge_spot_delta.parquet"),
        "fwd_delta": pd.read_parquet("lby_prtfl_full_hedge_fwd_delta.parquet"),
        "spot_gamma": pd.read_parquet("lby_prtfl_full_hedge_spot_gamma.parquet"),
        "sim_pos_pnl": pd.read_parquet("lby_prtfl_full_hedge_sim_pos_pnl.parquet"),
        "sim_pos_grp_pnl": pd.read_parquet("lby_prtfl_full_hedge_sim_pos_grp_pnl.parquet"),
        "sim_prtfl_pnl": pd.read_parquet("lby_prtfl_full_hedge_sim_prtfl_pnl.parquet"),
        "cvar_scenarios": pd.read_parquet("lby_prtfl_full_hedge_cvar_scenarios.parquet"),
        "pv01_delta_cvar_attr": pd.read_parquet("lby_prtfl_full_hedge_pv01_delta_cvar_attr.parquet"), 
        "prtfl_cvar" : pd.read_parquet("lby_prtfl_full_hedge_prtfl_cvar.parquet"), 
        "pos_grp_cvar": pd.read_parquet("lby_prtfl_full_hedge_pos_grp_cvar.parquet"),
        "pos_cvar": pd.read_parquet("lby_prtfl_full_hedge_pos_cvar.parquet"), 
        "positions": pd.read_parquet("lby_prtfl_full_hedge_positions.parquet")              
    }

    data_dict["liability_proxy_hedge_portfolio"] = {
        "cashflows": pd.read_parquet("lby_prtfl_proxy_hedge_cashflows.parquet"),
        "npv": pd.read_parquet("lby_prtfl_proxy_hedge_npv.parquet"),
        "spot_delta": pd.read_parquet("lby_prtfl_proxy_hedge_spot_delta.parquet"),
        "fwd_delta": pd.read_parquet("lby_prtfl_proxy_hedge_fwd_delta.parquet"),
        "spot_gamma": pd.read_parquet("lby_prtfl_proxy_hedge_spot_gamma.parquet"),
        "sim_pos_pnl": pd.read_parquet("lby_prtfl_proxy_hedge_sim_pos_pnl.parquet"),
        "sim_pos_grp_pnl": pd.read_parquet("lby_prtfl_proxy_hedge_sim_pos_grp_pnl.parquet"),
        "sim_prtfl_pnl": pd.read_parquet("lby_prtfl_proxy_hedge_sim_prtfl_pnl.parquet"),
        "cvar_scenarios": pd.read_parquet("lby_prtfl_proxy_hedge_cvar_scenarios.parquet"),
        "pv01_delta_cvar_attr": pd.read_parquet("lby_prtfl_proxy_hedge_pv01_delta_cvar_attr.parquet"), 
        "prtfl_cvar" : pd.read_parquet("lby_prtfl_proxy_hedge_prtfl_cvar.parquet"), 
        "pos_grp_cvar": pd.read_parquet("lby_prtfl_proxy_hedge_pos_grp_cvar.parquet"),
        "pos_cvar": pd.read_parquet("lby_prtfl_proxy_hedge_pos_cvar.parquet"), 
        "positions": pd.read_parquet("lby_prtfl_proxy_hedge_positions.parquet")                                     
    }
    
    return data_dict