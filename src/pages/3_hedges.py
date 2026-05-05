import os 
import streamlit as st
import pandas as pd 
import numpy as np 
import altair as alt
from typing import Dict
from pathlib import Path
from app_util.parquet_loader import parquet_loader

@st.cache_data
def current_page_parquet_loader(
    ) -> parquet_loader:
    
    return parquet_loader() 

# ----------> Page structure and layout 
# 0.0 Page layout 
st.set_page_config(
    page_title = "liabilities",
    layout = "wide",
    initial_sidebar_state = "expanded")

# 0.1 CSS injection for control of font-size 
st.markdown(
"""            
<style>   
/* ---- Base font size ---- */
html, body, [data-testid="stAppViewContainer"] {
    font-size: 10pt;
}

/* ---- Title (h1) ---- */
h1 {
    font-size: 12pt !important;
}

/* ---- Subheaders (h2, h3 etc.) ---- */
h2, h3 {
    font-size: 10pt !important;
}

/* ---- Spacing under headers ---- */
h1, h2, h3 {
    margin-bottom: 0.3rem; 
}

</style>
"""
, unsafe_allow_html = True)

# 0.2 Navigation tabs for liabilities page: cashflows, risk sensitivities and mc CVaR
tab1, tab2, tab3 = st.tabs([
    "benchmark hedge",
    "liquid proxy hedge",
    "portfolio risk impact"
])

# 0.3.0 Data dictionary with all dfs for the streamlit app  
df_dict = current_page_parquet_loader()

# ----------> 1.0 Benchmark Hedge Tab
# 1.1 Add sub-page description 
with tab1: 
    
    with st.expander("page info"):

        st.markdown("""
        **Overview**  
        This section presents and analyzes the construction of interest rate hedging strategies for the liability portfolio using fixed/float IRS instruments.

        Two approaches are considered:
        - A **benchmark hedge**, which fully neutralizes PV01 exposure across all tenors  
        - A **liquid proxy hedge**, which restricts instruments to liquid tenors and minimizes residual risk using the sample covariance matrix  

        Both approaches aim to reduce the portfolio’s sensitivity to interest rate movements, but differ in instrument availability and optimality criteria.  
        The benchmark hedge serves as a reference point for evaluating the effectiveness of the liquid proxy hedge.

        This section focuses on the construction of the benchmark hedge, while the liquid proxy hedge is presented in the following section (tab).
        """)

        st.markdown("**a. Benchmark Hedge (Full PV01 Neutralization)**")

        st.markdown("""&nbsp;&nbsp; The benchmark hedge neutralizes PV01 exposure at each tenor by constructing a hedging portfolio such that:""")

        st.latex(r"\frac{\partial \text{PV}_{\text{portfolio}}}{\partial r} + \frac{\partial \text{PV}_{\text{hedge}}}{\partial r} = 0")

        st.markdown("&nbsp;&nbsp; Equivalently:")

        st.latex(r"\frac{\partial \text{PV}_{\text{hedge}}}{\partial r} = - \frac{\partial \text{PV}_{\text{portfolio}}}{\partial r}")

        st.markdown("""&nbsp;&nbsp; Let:""")
        
        st.latex(r"\mathbf{d} \in \mathbb{R}^n") 
        st.latex(r"H \in \mathbb{R}^{n \times n}") 
        st.latex(r"w \in \mathbb{R}^n")         
        
        st.markdown("""&nbsp;&nbsp; denote the liability PV01 vector, matrix of instrument PV01s across tenors and hedge notionals.""")
        
        st.markdown("""&nbsp;&nbsp; The benchmark hedge is obtained by solving:""")

        st.latex(r"H w = -d")

        st.markdown("""&nbsp;&nbsp; this produces an exact hedge under the assumption that instruments are available at all tenors.""")

        st.markdown("**b. Hedging Instrument Representation**")

        st.markdown("""&nbsp;&nbsp; Let the hedging matrix be defined as:""")

        st.latex(r"H \in \mathbb{R}^{n \times k}")

        st.markdown("""&nbsp;&nbsp; where each column corresponds to the PV01 profile of a hedging instrument:""")

        st.latex(r"H = \begin{bmatrix} h^{(1)} & h^{(2)} & \cdots & h^{(k)} \end{bmatrix}")
        
        st.markdown("""&nbsp;&nbsp; thus "n" is the number of swap rates for curve calibration and PV01 risk, and "k" is the number of available hedging IRS instruments""")

        st.markdown("""&nbsp;&nbsp; Each column vector is defined as:""")

        st.latex(r"h^{(j)} = \frac{\partial \text{PV}_{\text{IRS}_j}}{\partial r}")

        st.markdown("""&nbsp;&nbsp; where:""")
        
        st.latex(r"h^{(j)} \in \mathbb{R}^n") 
        
        st.markdown("""&nbsp;&nbsp; is the PV01 vector of the j-th hedging instrument, and each instrument is an at-the-money fixed/float IRS with notional of 1 mEUR.""")  
    
        st.markdown("""&nbsp;&nbsp; Thus, each element of the matrix is given by:""")

        st.latex(r"H_{ij} = \frac{\partial \text{PV}_{\text{IRS}_j}}{\partial r_i}")

        st.markdown("""&nbsp;&nbsp; which represents the sensitivity of instrument j to a 1 bps shift in the swap rate at tenor i.""")

        st.markdown("""&nbsp;&nbsp; The weights, w, therefore represent scaling of these unit PV01 profiles, i.e. notionals applied to each fixed/float IRS instrument.""")
        
        st.markdown("""&nbsp;&nbsp; Finally, a negative notional/weight is interpreted as a payer position and positive notional/weight corresponds to a receiver position.""")

        st.markdown("""
        **Content**  
        The section is organized as follows:

        • Hedging instruments (IRS), hedge weights and notionals
        
        • Fully Hedged liability portfolio, risk sensitivities and MC CVaR (including component CVaR)
        
        • MC PnL comparison: benchmark (full) hedge vs. unhedged portfolio in simulated scenarios  
        """)

# 1.2 Add dfs with instruments used for the full benchmark hedge and hedge weights/notionals
analysis_dt = df_dict['liability_full_hedge_portfolio']['positions'].copy()['Date'].iloc[0]
curve = df_dict['liability_full_hedge_portfolio']['positions'].copy()['Curve'].iloc[0]
full_hedge_prtfl_id = df_dict['liability_full_hedge_portfolio']['prtfl_cvar'].copy()['Portfolio ID'].iloc[0]
mc_horizon_days = df_dict['liability_full_hedge_portfolio']['prtfl_cvar'].copy()['Time Horizon (Days)'].iloc[0]

full_hedge_irs = (
 df_dict['liability_hedge']['full_hedge_instruments'].copy()
 [[clmn for clmn in df_dict['liability_hedge']['full_hedge_instruments'].columns if clmn.lower() != 'ccy']]
  .rename( columns = 
     { clmn_nm : clmn_nm.lower()
           for clmn_nm in df_dict['liability_hedge']['full_hedge_instruments'].loc[:,:'Curve'].columns.to_list()
     }  ) 
)

full_hedge_wgts = (
 df_dict['liability_full_hedge_portfolio']['positions'].copy()
  [['Position ID', 'Notional']]
  .rename( columns = 
     { clmn_nm : clmn_nm.lower()
           for clmn_nm in df_dict['liability_full_hedge_portfolio']['positions'].columns.to_list()
     }
        )
  .assign(
    **{ 'hedge weights (w)' : lambda df : 
                              np.where(  ( df['position id'].str.contains('Payer') ),  
                                      df.notional / -1e6, 
                                      np.where( df['position id'].str.contains('@'), df.notional /1e6, 0 ) ), 
        'notional' : lambda df : np.where( df['position id'].str.contains('Payer') , df.notional * -1, df.notional )
      } )  
  )

with tab1:
    
    st.subheader(f"1. benchmark (full) hedge: IRS instruments, hedge notionals and weights on {analysis_dt.strftime("%Y-%m-%d")}")
    
    section_1 = st.container(border = True)
    
    with section_1: 
        
        st.latex(r"H \in \mathbb{R}^{n \times n}")
        
        numeric_clmns = full_hedge_irs.select_dtypes( include = 'number').columns 
        
        st.dataframe( full_hedge_irs.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True)
        
        st.latex(r"w \in \mathbb{R}^n")    
        
        numeric_clmns = full_hedge_wgts.select_dtypes( include = 'number').columns
        
        st.dataframe( full_hedge_wgts[full_hedge_wgts['position id'].str.contains('@')]
                      .style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True)

# 1.3 Add dfs with fully hedged portfolio risk (sensitivities and CVaR)     
prtfl_spot_delta = (
    df_dict['liability_full_hedge_portfolio']['spot_delta']
    .copy()
    .loc[: , 'Position Grp' : ]
    .drop( ['Ccy','Curve'], axis = 1)
    .rename(  columns = 
            { clmn_nm : clmn_nm.lower() for 
              clmn_nm in df_dict['liability_full_hedge_portfolio']['spot_delta'].loc[:,:'Total'].columns.to_list() }
           )    
)
spot_delta_sens_tp = prtfl_spot_delta['sensitivity'][0]
prtfl_spot_delta.drop('sensitivity', axis = 1, inplace = True)

prtfl_gamma = (
    df_dict['liability_full_hedge_portfolio']['spot_gamma']
    .copy()
    .loc[: , 'Position Grp' : ]
    .drop( ['Ccy','Curve'], axis = 1)
    .rename(  columns = 
            { clmn_nm : clmn_nm.lower() for 
              clmn_nm in df_dict['liability_full_hedge_portfolio']['spot_gamma'].loc[:,:'Total'].columns.to_list() }
           )    
)
gamma_sens_tp = prtfl_gamma['sensitivity'][0]
prtfl_gamma.drop('sensitivity', axis = 1, inplace = True)

prtfl_fwd_delta = (
    df_dict['liability_full_hedge_portfolio']['fwd_delta']
    .copy()
    .loc[: , 'Position Grp' : ]
    .drop( ['Ccy','Curve'], axis = 1)
    .rename(  columns = 
            { clmn_nm : clmn_nm.lower() for 
              clmn_nm in df_dict['liability_full_hedge_portfolio']['fwd_delta'].loc[:,:'Total'].columns.to_list() }
           )    
)
fwd_delta_sens_tp = prtfl_fwd_delta['sensitivity'][0]
prtfl_fwd_delta.drop('sensitivity', axis = 1, inplace = True)

cvar = (
    df_dict['liability_full_hedge_portfolio']['pos_cvar']
     .copy()
     .loc[:, 'Position Grp' : ]
     .drop(['Ccy', 'Curve'], axis = 1)
     .rename(  columns = 
             { clmn_nm : clmn_nm.lower() for 
               clmn_nm in df_dict['liability_full_hedge_portfolio']['pos_cvar'].columns.to_list() }
           )         
)

cvar_row = [ '', 'Total portfolio mc cvar', mc_horizon_days, np.nan, np.nan, cvar.sum().iloc[-1] ]
total_row = pd.DataFrame( data = [cvar_row], columns = cvar.columns ) 
 
with tab1:
    
    st.subheader(f"2. {full_hedge_prtfl_id} risk on {analysis_dt.strftime("%Y-%m-%d")}, {curve} curve, all amounts in EUR:")
    
    section_2 = st.container(border = True)
    
    with section_2: 
        
        # spot PV01/delta 
        st.subheader(spot_delta_sens_tp)
                
        numeric_clmns = prtfl_spot_delta.select_dtypes( include = 'number').columns 
        
        st.dataframe( prtfl_spot_delta.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True)

        # spot gamma                
        st.subheader(gamma_sens_tp)
                
        numeric_clmns = prtfl_gamma.select_dtypes( include = 'number').columns 
        
        st.dataframe( prtfl_gamma.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True)        

        # fwd PV01/delta        
        st.subheader(fwd_delta_sens_tp)
        
        numeric_clmns = prtfl_fwd_delta.select_dtypes( include = 'number').columns
        
        st.dataframe( prtfl_fwd_delta.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True)        

        # mc cvar
        st.subheader('mc cvar')
        
        numeric_clmns = cvar.select_dtypes( include = 'number').columns
        
        cvar = pd.concat([cvar, total_row])        
        
        st.dataframe( cvar.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True )

# 1.4 Prepare dfs for mc PnL scatter plot: mc PnL of the unhedged liability position plotted against full hedge mc pnl
grp_pnl = (
    df_dict['liability_full_hedge_portfolio']['sim_pos_grp_pnl']
    .copy()
    .loc[: , 'Position Grp' : ]
    .drop( ['Ccy','Curve'], axis = 1) 
    .rename(  columns = 
            { clmn_nm : clmn_nm.lower() for 
              clmn_nm in df_dict['liability_full_hedge_portfolio']['sim_pos_grp_pnl'].columns.to_list() }
           )    
)

grp_pnl_wide = (
 grp_pnl.pivot(index = 'scenario', columns = 'position grp', values = 'pnl')
  .reset_index()
)
grp_pnl_wide.columns.name = None 

with tab1: 
    
    st.subheader("3. PnL correlation in simulated scenarios: liabilities vs benchmark irs hedge PnL (y-axis) ")
    
    row_1 = st.container(border = True, height = 600)
    
    with row_1: 
        
        pnl_scatter_chart = (
         alt.Chart(grp_pnl_wide)
         .mark_circle()
         .encode(
             x = alt.X("liabilities:Q", title = "liabilities mc PnL"),
             y = alt.Y("Benchmark IRS Hedge:Q", title = None),
         ) )
        
        slope, intercept = np.polyfit(grp_pnl_wide["liabilities"], grp_pnl_wide["Benchmark IRS Hedge"], 1)
        
        st.markdown(f"<p style='text-align: center;'>β = {slope:.5f}</p>", unsafe_allow_html = True )

        st.altair_chart(pnl_scatter_chart, use_container_width=True, height = "stretch")

# 2.1 Add sub-page description 
with tab2: 
    
    with st.expander("page info"):

        st.markdown("""
        **Overview**  
        This section presents and analyzes the construction of a liquid proxy hedge for the liability portfolio using fixed/float IRS instruments.

        In contrast to the benchmark hedge, which assumes instruments are available at all tenors, the proxy hedge restricts the hedging set to a subset of liquid maturities.

        The hedge is constructed to minimize residual risk rather than fully eliminate PV01 exposure, using the sample covariance matrix of swap rate changes.

        This approach reflects practical market constraints and provides an implementable approximation to the benchmark hedge.
        """)

        st.markdown("**a. Liquid Proxy Hedge (Minimum-Variance Hedge)**")

        st.markdown("""&nbsp;&nbsp; The proxy hedge minimizes the variance of the residual exposure after hedging:""")

        st.latex(r"\epsilon = d + H w")

        st.markdown("""&nbsp;&nbsp; where the objective is to minimize:""")

        st.latex(r"\min_{w} \; \epsilon^T \Sigma \epsilon")

        st.markdown("""&nbsp;&nbsp; Expanding the objective:""")

        st.latex(r"\min_{w} \; (d + H w)^T \Sigma (d + H w)")

        st.markdown("""&nbsp;&nbsp; The optimal hedge is given by:""")

        st.latex(r"w^* = - (H^T \Sigma H)^{-1} H^T \Sigma d")

        st.markdown("""&nbsp;&nbsp; This solution minimizes the variance of the hedged portfolio and accounts for correlations between rate movements across tenors.""")

        st.markdown("**b. Hedging Instrument Representation**")

        st.markdown("""&nbsp;&nbsp; Let the hedging matrix be defined as:""")

        st.latex(r"H \in \mathbb{R}^{n \times k}")

        st.markdown("""&nbsp;&nbsp; where each column corresponds to the PV01 profile of a hedging instrument:""")

        st.latex(r"H = \begin{bmatrix} h^{(1)} & h^{(2)} & \cdots & h^{(k)} \end{bmatrix}")

        st.markdown("""&nbsp;&nbsp; Each column vector is defined as:""")

        st.latex(r"h^{(j)} = \frac{\partial \text{PV}_{\text{IRS}_j}}{\partial r}")

        st.markdown("""&nbsp;&nbsp; where:""")

        st.latex(r"h^{(j)} \in \mathbb{R}^n")

        st.markdown("""&nbsp;&nbsp; is the PV01 vector of the j-th hedging instrument, and each instrument is an at-the-money fixed/float IRS with notional of 1 mEUR.""")

        st.markdown("""&nbsp;&nbsp; Thus, each element of the matrix is given by:""")

        st.latex(r"H_{ij} = \frac{\partial \text{PV}_{\text{IRS}_j}}{\partial r_i}")

        st.markdown("""&nbsp;&nbsp; which represents the sensitivity of instrument j to a 1 bps shift in the swap rate at tenor i.""")

        st.markdown("""&nbsp;&nbsp; The weights, w, therefore represent scaling of these unit PV01 profiles, i.e. notionals applied to each fixed/float IRS instrument.""")

        st.markdown("""&nbsp;&nbsp; Finally, a negative notional/weight is interpreted as a payer position and positive notional/weight corresponds to a receiver position.""")

        st.markdown("""
        **Content**  
        The section is organized as follows:

        • Liquid Hedging instruments (IRS), hedge weights, notionals and sample covariance matrix for market swap rate shifts (see risk factors page for details)
        
        • Liquid Proxy Hedged liability portfolio, risk sensitivities and MC CVaR (including component CVaR)
        
        • MC PnL comparison: liquid (proxy) hedge vs. unhedged portfolio in simulated scenarios  
        """)
    
# 2.2 Add dfs with instruments used for the proxy benchmark hedge and hedge weights/notionals
analysis_dt = df_dict['liability_proxy_hedge_portfolio']['positions'].copy()['Date'].iloc[0]
curve = df_dict['liability_proxy_hedge_portfolio']['positions'].copy()['Curve'].iloc[0]
proxy_hedge_prtfl_id = df_dict['liability_proxy_hedge_portfolio']['prtfl_cvar'].copy()['Portfolio ID'].iloc[0]
mc_horizon_days = df_dict['liability_proxy_hedge_portfolio']['prtfl_cvar'].copy()['Time Horizon (Days)'].iloc[0]

proxy_hedge_irs = (
 df_dict['liability_hedge']['liquid_hedge_instruments'].copy()
 [[clmn for clmn in df_dict['liability_hedge']['liquid_hedge_instruments'].columns if clmn.lower() != 'ccy']] 
 .rename( columns = 
     { clmn_nm : clmn_nm.lower()
           for clmn_nm in df_dict['liability_hedge']['liquid_hedge_instruments'].loc[:,:'Curve'].columns.to_list()
     }  )
)

proxy_hedge_wgts = (
 df_dict['liability_proxy_hedge_portfolio']['positions'].copy()
  [['Position ID', 'Notional']]
  .rename( columns = 
     { clmn_nm : clmn_nm.lower()
           for clmn_nm in df_dict['liability_proxy_hedge_portfolio']['positions'].columns.to_list() }
        )
  .assign(
    **{ 'hedge weights (w)' : lambda df : 
                              np.where(  ( df['position id'].str.contains('Payer') ),  
                                      df.notional / -1e6, 
                                      np.where( df['position id'].str.contains('@'), df.notional /1e6, 0 ) ), 
        'notional' : lambda df : np.where( df['position id'].str.contains('Payer') , df.notional * -1, df.notional )
      } )  
)

with tab2:
    
    st.subheader(f"1. liquid (proxy) hedge: IRS instruments, hedge notionals and weights on {analysis_dt.strftime("%Y-%m-%d")}")
    
    section_1 = st.container(border = True)
    
    with section_1: 
        
        st.latex(r"H \in \mathbb{R}^{n \times k}")
        
        numeric_clmns = proxy_hedge_irs.select_dtypes( include = 'number').columns 
        
        st.dataframe( proxy_hedge_irs.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True)
        
        st.latex(r"w^* \in \mathbb{R}^k")    
        
        numeric_clmns = proxy_hedge_wgts.select_dtypes( include = 'number').columns
        
        st.dataframe( proxy_hedge_wgts[proxy_hedge_wgts['position id'].str.contains('@')]
                      .style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True)

# 1.3 Add dfs with fully hedged portfolio risk (sensitivities and CVaR)     
prtfl_spot_delta = (
    df_dict['liability_proxy_hedge_portfolio']['spot_delta']
    .copy()
    .loc[: , 'Position Grp' : ]
    .drop( ['Ccy','Curve'], axis = 1)
    .rename(  columns = 
            { clmn_nm : clmn_nm.lower() for 
              clmn_nm in df_dict['liability_proxy_hedge_portfolio']['spot_delta'].loc[:,:'Total'].columns.to_list() }
           )    
)
spot_delta_sens_tp = prtfl_spot_delta['sensitivity'][0]
prtfl_spot_delta.drop('sensitivity', axis = 1, inplace = True)

prtfl_gamma = (
    df_dict['liability_proxy_hedge_portfolio']['spot_gamma']
    .copy()
    .loc[: , 'Position Grp' : ]
    .drop( ['Ccy','Curve'], axis = 1)
    .rename(  columns = 
            { clmn_nm : clmn_nm.lower() for 
              clmn_nm in df_dict['liability_proxy_hedge_portfolio']['spot_gamma'].loc[:,:'Total'].columns.to_list() }
           )    
)
gamma_sens_tp = prtfl_gamma['sensitivity'][0]
prtfl_gamma.drop('sensitivity', axis = 1, inplace = True)

prtfl_fwd_delta = (
    df_dict['liability_proxy_hedge_portfolio']['fwd_delta']
    .copy()
    .loc[: , 'Position Grp' : ]
    .drop( ['Ccy','Curve'], axis = 1)
    .rename(  columns = 
            { clmn_nm : clmn_nm.lower() for 
              clmn_nm in df_dict['liability_proxy_hedge_portfolio']['fwd_delta'].loc[:,:'Total'].columns.to_list() }
           )    
)
fwd_delta_sens_tp = prtfl_fwd_delta['sensitivity'][0]
prtfl_fwd_delta.drop('sensitivity', axis = 1, inplace = True)

cvar = (
    df_dict['liability_proxy_hedge_portfolio']['pos_cvar']
     .copy()
     .loc[:, 'Position Grp' : ]
     .drop(['Ccy', 'Curve'], axis = 1)
     .rename(  columns = 
             { clmn_nm : clmn_nm.lower() for 
               clmn_nm in df_dict['liability_proxy_hedge_portfolio']['pos_cvar'].columns.to_list() }
           )         
)

cvar_row = [ '', 'Total portfolio mc cvar', mc_horizon_days, np.nan, np.nan, cvar.sum().iloc[-1] ]
total_row = pd.DataFrame( data = [cvar_row], columns = cvar.columns ) 
 
with tab2:
    
    st.subheader(f"2. {proxy_hedge_prtfl_id} risk on {analysis_dt.strftime("%Y-%m-%d")}, {curve} curve, all amounts in EUR:")
    
    section_2 = st.container(border = True)
    
    with section_2: 
        
        # spot PV01/delta 
        st.subheader(spot_delta_sens_tp)
                
        numeric_clmns = prtfl_spot_delta.select_dtypes( include = 'number').columns 
        
        st.dataframe( prtfl_spot_delta.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True)

        # spot gamma                
        st.subheader(gamma_sens_tp)
                
        numeric_clmns = prtfl_gamma.select_dtypes( include = 'number').columns 
        
        st.dataframe( prtfl_gamma.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True)        

        # fwd PV01/delta        
        st.subheader(fwd_delta_sens_tp)
        
        numeric_clmns = prtfl_fwd_delta.select_dtypes( include = 'number').columns
        
        st.dataframe( prtfl_fwd_delta.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True)        

        # mc cvar
        st.subheader('mc cvar')
        
        numeric_clmns = cvar.select_dtypes( include = 'number').columns
        
        cvar = pd.concat([cvar, total_row])        
        
        st.dataframe( cvar.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True )

# 1.4 Prepare dfs for mc PnL scatter plot: mc PnL of the unhedged liability position plotted against full hedge mc pnl
grp_pnl = (
    df_dict['liability_proxy_hedge_portfolio']['sim_pos_grp_pnl']
    .copy()
    .loc[: , 'Position Grp' : ]
    .drop( ['Ccy','Curve'], axis = 1) 
    .rename(  columns = 
            { clmn_nm : clmn_nm.lower() for 
              clmn_nm in df_dict['liability_proxy_hedge_portfolio']['sim_pos_grp_pnl'].columns.to_list() }
           )    
)

grp_pnl_wide = (
 grp_pnl.pivot(index = 'scenario', columns = 'position grp', values = 'pnl')
  .reset_index()
)
grp_pnl_wide.columns.name = None 

with tab2: 
    
    st.subheader("3. PnL correlation in simulated scenarios: liabilities vs liquid proxy irs hedge PnL (y-axis) ")
    
    row_1 = st.container(border = True, height = 600)
    
    with row_1: 
        
        pnl_scatter_chart = (
         alt.Chart(grp_pnl_wide)
         .mark_circle()
         .encode(
             x = alt.X("liabilities:Q", title = "liabilities mc PnL"),
             y = alt.Y("Liquid Proxy Hedge:Q", title = None),
         ) )
        
        slope, intercept = np.polyfit(grp_pnl_wide["liabilities"], grp_pnl_wide["Liquid Proxy Hedge"], 1)
        
        st.markdown(f"<p style='text-align: center;'>β = {slope:.5f}</p>", unsafe_allow_html = True )

        st.altair_chart(pnl_scatter_chart, use_container_width=True, height = "stretch")

# 3.1 Add sub-page description 
with tab3: 
    
    with st.expander("page info"):

        st.markdown("""
        **Overview**  
        This section compares key metrics across unhedged, fully hedged, and proxy-hedged liability portfolios to assess the risk reduction achieved by the liquid IRS proxy hedge.

        **Content**  
        For each portfolio, we compare:
        
        • CVaR
        
        • Risk sensitivities         
        
        • Density of simulated PnL distribution        
        """)

# 3.1 Add portfolio overview 
sens_prms = ( 
 pd.concat(
 [ df[df['Position ID'] == 'Total'][['Portfolio ID', 'Ccy', 'Curve', 'PV']] 
   for df in [ df_dict['liability_portfolio']['npv'].copy(), 
               df_dict['liability_proxy_hedge_portfolio']['npv'].copy(), 
               df_dict['liability_full_hedge_portfolio']['npv'].copy()                
             ] ] 
 ).reset_index(drop = True)
  .rename( columns = {'PV' : 'present value', 'Ccy' : 'currency'} ) 
)
sens_prms.columns = [clmn.lower() for clmn in sens_prms.columns]

with tab3:
    
    st.subheader(f"1. portfolios on {analysis_dt.strftime("%Y-%m-%d")}:")
    
    section_1 = st.container(border = True)
    
    with section_1: 
        
        numeric_clmns = sens_prms.select_dtypes( include = 'number' ).columns 

        # overview 
        st.dataframe(sens_prms.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True )
        
# 3.2 Gather and add df with mc cvar figures 
var_clmn = [ clmn for clmn in df_dict['liability_portfolio']['prtfl_cvar'].columns if 'mc var' in clmn.lower()]
cvar_clmn = [ clmn for clmn in df_dict['liability_portfolio']['prtfl_cvar'].columns if 'mc cvar' in clmn.lower() and 'component' not in clmn.lower()]
unhedged_var = df_dict['liability_portfolio']['prtfl_cvar'][var_clmn].iloc[0,0]
unhedged_cvar  = df_dict['liability_portfolio']['prtfl_cvar'][cvar_clmn].iloc[0,0]

cvar_clmns = [clmn for clmn in df_dict['liability_portfolio']['prtfl_cvar'].columns 
                if 'component' not in clmn.lower() and
                   'date'      not in clmn.lower() and
                   'ccy'       not in clmn.lower() and
                   'curve'     not in clmn.lower()
             ]
cvar = (
 pd.concat( 
   df for df in [ df_dict['liability_portfolio']['prtfl_cvar'], 
                  df_dict['liability_proxy_hedge_portfolio']['prtfl_cvar'], 
                  df_dict['liability_full_hedge_portfolio']['prtfl_cvar']
                ] 
          )[cvar_clmns].reset_index(drop = True)
  .rename( columns = { clmn : clmn.lower() for clmn in df_dict['liability_portfolio']['prtfl_cvar'].columns } )    
  .assign( **{ 'mc var reduction (%)' : lambda df : ( df[var_clmn[0].lower()] / unhedged_var - 1 ) * 100, 
               'mc cvar reduction (%)' : lambda df : ( df[cvar_clmn[0].lower()] / unhedged_cvar - 1 ) * 100      
             }
  )
)

with tab3:
    
    st.subheader(f"2. hedge impact on portfolio mc cvar")
    
    section_2 = st.container(border = True)
    
    with section_2: 
        
        numeric_clmns = cvar.select_dtypes( include = 'number' ).columns 

        # overview 
        st.dataframe(cvar.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True )

# 3.3 Gather and add dfs with portfolio spot pv01, fwd pv01 and gamma 
# aggregated spot PV01 sens 
spot_pv01_clmns = (
 ['Portfolio ID'] + 
 [ clmn for clmn in df_dict['liability_portfolio']['spot_delta'].loc[:,'Total':].columns if clmn != 'Total'] + 
 ['Total'] 
)
spot_pv01_sens_tp = df_dict['liability_portfolio']['spot_delta']['Sensitivity'][0]
spot_pv01 = (
 pd.concat(
 [ df[spot_pv01_clmns] 
   for df in [ df_dict['liability_portfolio']['spot_delta']
                [ df_dict['liability_portfolio']['spot_delta']['Position ID'] == 'Total' ], 
               df_dict['liability_proxy_hedge_portfolio']['spot_delta']
               [ df_dict['liability_proxy_hedge_portfolio']['spot_delta']['Position ID'] == 'Total' ]
             ] ] 
 ).reset_index(drop = True)
  .rename( columns = { clmn : clmn.lower() for clmn in spot_pv01_clmns if not 'Y' in clmn} )    
)
_clmns = ['unhedged','proxy hedged']
spot_pv01 = spot_pv01.iloc[:,1:].T
spot_pv01.columns = _clmns 
spot_pv01 = spot_pv01.reset_index().rename(columns = { 'index':'tenor' })

# aggregated spot gamma 
spot_gamma_clmns = (
 ['Portfolio ID'] + 
 [ clmn for clmn in df_dict['liability_portfolio']['spot_gamma'].loc[:,'Total':].columns if clmn != 'Total'] + 
 ['Total'] 
)
spot_gamma_sens_tp = df_dict['liability_portfolio']['spot_gamma']['Sensitivity'][0]
spot_gamma = (
 pd.concat(
 [ df[spot_gamma_clmns] 
   for df in [ df_dict['liability_portfolio']['spot_gamma']
                [ df_dict['liability_portfolio']['spot_gamma']['Position ID'] == 'Total' ], 
               df_dict['liability_proxy_hedge_portfolio']['spot_gamma']
               [ df_dict['liability_proxy_hedge_portfolio']['spot_gamma']['Position ID'] == 'Total' ]
             ] ] 
 ).reset_index(drop = True)
  .rename( columns = { clmn : clmn.lower() for clmn in spot_gamma_clmns if not 'Y' in clmn} )    
)

_clmns = ['unhedged','proxy hedged']
spot_gamma = spot_gamma.iloc[:,1:].T
spot_gamma.columns = _clmns 
spot_gamma = spot_gamma.reset_index().rename(columns = { 'index':'tenor' })

# aggregated forward pv01 
fwd_pv01_clmns = (
 ['Portfolio ID'] + 
 [ clmn for clmn in df_dict['liability_portfolio']['fwd_delta'].loc[:,'Total':].columns if clmn != 'Total'] + 
 ['Total'] 
)
fwd_pv01_sens_tp = df_dict['liability_portfolio']['fwd_delta']['Sensitivity'][0]
fwd_pv01 = (
 pd.concat(
 [ df[fwd_pv01_clmns] 
   for df in [ df_dict['liability_portfolio']['fwd_delta']
                [ df_dict['liability_portfolio']['fwd_delta']['Position ID'] == 'Total' ], 
               df_dict['liability_proxy_hedge_portfolio']['fwd_delta']
               [ df_dict['liability_proxy_hedge_portfolio']['fwd_delta']['Position ID'] == 'Total' ]
             ] ] 
 ).reset_index(drop = True)
  .rename( columns = { clmn : clmn.lower() for clmn in fwd_pv01_clmns if not 'Y' in clmn} )    
)

_clmns = ['unhedged','proxy hedged']
fwd_pv01 = fwd_pv01.iloc[:,1:].T
fwd_pv01.columns = _clmns 
fwd_pv01 = fwd_pv01.reset_index().rename(columns = { 'index':'tenor' })

with tab3: 
          
    st.subheader(f"3. risk sensitivities by portfolio type:")
      
    section_4 = st.container(border = False)
        
    with section_4: 
        
        row1_col1, row1_col2, row1_col3 = st.columns([1,1,1])
                        
        with row1_col1:
                
            # spot PV01/delta 
            st.subheader(spot_pv01_sens_tp)
                    
            numeric_clmns = spot_pv01.select_dtypes( include = 'number' ).columns 

            df_container = st.container(border = True)
            
            with df_container: 
                
                st.dataframe( spot_pv01.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True )
                    
        with row1_col2:
                
            # spot gamma 
            st.subheader(gamma_sens_tp)
                    
            numeric_clmns = spot_gamma.select_dtypes( include = 'number' ).columns 

            df_container = st.container(border = True)
            
            with df_container:
                
                st.dataframe( spot_gamma.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True )
            
                            
        with row1_col3:
                
            # forward PV01/delta  
            st.subheader(fwd_pv01_sens_tp)
                    
            numeric_clmns = fwd_pv01.select_dtypes( include = 'number' ).columns 

            df_container = st.container(border = True)

            with df_container:
                
                st.dataframe( fwd_pv01.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "content", hide_index = True )       
        
        row2_col1, row2_col2, row2_col3 = st.columns([1,1,1])     
        
        with row2_col1: 
            
            tenor_order = [tenor for tenor in spot_pv01['tenor'].values.tolist() if tenor != 'total']
            
            spot_pv01_long = (
             spot_pv01.copy()
              .melt( id_vars = "tenor", var_name = "portfolio", value_name="pv01")
            )
            
            spot_pv01_long = spot_pv01_long[spot_pv01_long["tenor"] != "total"]

            chart_container = st.container(border = True, height = 600)
            
            with chart_container: 
            
                spot_pv01_chart = (
                 alt.Chart(spot_pv01_long)
                 .mark_bar()
                 .encode(
                    x = alt.X("tenor:N", title="tenor", sort = tenor_order),
                    y = alt.Y("pv01:Q", title = "spot PV01"),
                    color = alt.Color( "portfolio:N", title="Portfolio", legend=alt.Legend( orient="top", labelLimit = 500, title = None)  ),                  
                    xOffset = "portfolio:N",
                    tooltip = ["tenor", "portfolio", "pv01"] )
                )
                
                st.altair_chart(spot_pv01_chart, use_container_width=True, height = "stretch")                       
            
        with row2_col2: 
            
            tenor_order = [tenor for tenor in spot_gamma['tenor'].values.tolist() if tenor != 'total']
            
            spot_gamma_long = (
             spot_gamma.copy()
              .melt( id_vars = "tenor", var_name = "portfolio", value_name="gamma")
            )
            
            spot_gamma_long = spot_gamma_long[spot_gamma_long["tenor"] != "total"]

            chart_container = st.container(border = True, height = 600)
            
            with chart_container: 
            
                spot_gamma_chart = (
                 alt.Chart(spot_gamma_long)
                 .mark_bar()
                 .encode(
                    x = alt.X("tenor:N", title="tenor", sort = tenor_order),
                    y = alt.Y("gamma:Q", title = "spot gamma"),
                    color = alt.Color( "portfolio:N", title="Portfolio", legend=alt.Legend( orient="top", labelLimit = 500, title = None)  ),                  
                    xOffset = "portfolio:N",
                    tooltip = ["tenor", "portfolio", "gamma"] )
                )
                
                st.altair_chart(spot_gamma_chart, use_container_width=True, height = "stretch")                                   
            
        with row2_col3: 
            
            tenor_order = [tenor for tenor in fwd_pv01['tenor'].values.tolist() if tenor != 'total']
            
            fwd_pv01_long = (
             fwd_pv01.copy()
              .melt( id_vars = "tenor", var_name = "portfolio", value_name="forward pv01")
            )
            
            fwd_pv01_long = fwd_pv01_long[fwd_pv01_long["tenor"] != "total"]

            chart_container = st.container(border = True, height = 600)
            
            with chart_container: 
            
                fwd_pv01_chart = (
                 alt.Chart(fwd_pv01_long)
                 .mark_bar()
                 .encode(
                    x = alt.X("tenor:N", title="tenor", sort = tenor_order),
                    y = alt.Y("forward pv01:Q", title = "forward pv01"),
                    color = alt.Color( "portfolio:N", title="Portfolio", legend=alt.Legend( orient="top", labelLimit = 500, title = None)  ),                  
                    xOffset = "portfolio:N",
                    tooltip = ["tenor", "portfolio", "forward pv01"] )
                )
                
                st.altair_chart(fwd_pv01_chart, use_container_width=True, height = "stretch")
                        
# 3.4 mc PnL density plots  
pnl_clmns = ['portfolio type', 'tail scenario', 'scenario rank', 'Scenario', 'PnL']

unhedged_var_loss = df_dict['liability_portfolio']['prtfl_cvar'].iloc[:,-3][0] * -1
proxyhedged_var_loss = df_dict['liability_proxy_hedge_portfolio']['prtfl_cvar'].iloc[:,-3][0] * -1
fullyhedged_var_loss = df_dict['liability_full_hedge_portfolio']['prtfl_cvar'].iloc[:,-3][0] * -1



unhedged_pnl = (
 df_dict['liability_portfolio']['sim_prtfl_pnl']
 .assign(**{ 'portfolio type' : 'unhedged', 
             'tail scenario' : lambda df : np.where( df.PnL <= unhedged_var_loss, 'Y', 'N' ), 
             'scenario rank' : lambda df : df.PnL.rank().astype('int')
           } ) 
 [pnl_clmns]
 .rename( columns = { clmn : clmn.lower() for clmn in pnl_clmns } )
)

proxyhedged_pnl = (
 df_dict['liability_proxy_hedge_portfolio']['sim_prtfl_pnl']
 .assign(**{ 'portfolio type' : 'unhedged', 
             'tail scenario' : lambda df : np.where( df.PnL <= proxyhedged_var_loss, 'Y', 'N' ), 
             'scenario rank' : lambda df : df.PnL.rank().astype('int')
           } )
 [pnl_clmns]
 .rename( columns = { clmn : clmn.lower() for clmn in pnl_clmns } ) 
)

fullyhedged_pnl = (
 df_dict['liability_full_hedge_portfolio']['sim_prtfl_pnl']
 .assign(**{ 'portfolio type' : 'unhedged', 
             'tail scenario' : lambda df : np.where( df.PnL <= fullyhedged_var_loss, 'Y', 'N' ), 
             'scenario rank' : lambda df : df.PnL.rank().astype('int')
           } )
 [pnl_clmns]
 .rename( columns = { clmn : clmn.lower() for clmn in pnl_clmns } ) 
)

def plot_pnl_distribution(df, color="navy"):

    density_chart = (
        alt.Chart(df)
        .transform_density("pnl", as_=["pnl_value", "density"])
        .mark_line(size=2)
        .encode(
            x=alt.X("pnl_value:Q", title="mc PnL", axis=alt.Axis(grid=True)),
            y=alt.Y("density:Q", title=None, axis=alt.Axis(grid=True, labels=False)),
            color=alt.value(color),
            tooltip=[
                alt.Tooltip("pnl_value:Q"),
                alt.Tooltip("density:Q")
            ]
        )
    )

    moments = (
        df.groupby("portfolio type")["pnl"]
        .agg(["mean", "std"])
        .reset_index()
    )

    mean = moments.copy()
    mean["type"] = "μ"
    mean["value"] = mean["mean"]

    std_right = moments.copy()
    std_right["type"] = "+3σ"
    std_right["value"] = std_right["mean"] + 3 * std_right["std"]

    std_left = moments.copy()
    std_left["type"] = "-3σ"
    std_left["value"] = std_left["mean"] - 3 * std_left["std"]

    moments_long = pd.concat([mean, std_left, std_right])

    moment_chart = (
        alt.Chart(moments_long)
        .mark_rule(size=2)
        .encode(
            x="value:Q",
            color=alt.value(color),
            strokeDash=alt.StrokeDash(
                "type:N",
                scale=alt.Scale(
                    domain=["μ", "+3σ", "-3σ"],
                    range=[[1, 0], [4, 4], [4, 4]]
                ),
                legend=alt.Legend(title=None, orient="top")
            ),
            tooltip=["type", "value"]
        )
    )

    return alt.layer(density_chart, moment_chart)


with tab3: 
    
    st.subheader(f"4. simulated PnL distributions:")
        
    chart1_col, chart2_col, chart3_col = st.columns([1,1,1])
    
    with chart1_col:
        
        st.markdown("unhedged portfolio")
        
        chart_container = st.container(border=True)

        with chart_container:
            
            st.altair_chart(plot_pnl_distribution(unhedged_pnl,color="#00BFFF"), height=500)

    with chart2_col:
        
        st.markdown("proxy hedged portfolio")
        
        chart_container = st.container(border=True)

        with chart_container:
        
            st.altair_chart(plot_pnl_distribution(proxyhedged_pnl, color="#BB86FC"), height=500)

    with chart3_col:
        
        st.markdown("fully hedged portfolio")
        
        chart_container = st.container(border=True)

        with chart_container:
        
            st.altair_chart(plot_pnl_distribution(fullyhedged_pnl, color ="#39FF14"), height=500)
 