
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
    page_title = "risk factors",
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
""", unsafe_allow_html = True)

# 0.2 Navigation tabs for Curve Analysis page: Historical Data, MC Simulation and PCA 
tab1, tab2, tab3 = st.tabs([
    "eurswap curve",
    "principal component analysis", 
    "mc simulation" ])

# 0.3.0 Data dictionary with all dfs for current streamlit page 
df_dict = current_page_parquet_loader()

# ----------> 1.0 eurswap curve Tab
# 1.1 Add sub-page description 
with tab1:
    
    with st.expander("page info", expanded = False):
        
         st.markdown("""
            **Overview**  
            This section presents sample data of market rates for construction of the eurswap curve, principal component analysis, and monte carlo simulation.<br>
            The eurswap curve is a spot zero rate curve used for discounting, valuation and risk throughout the project.<br>
            The curve is calibrated from end-of-day euribor6m mid-market swap rates across selected tenors.<br>
            Tenor selection determines the set of modelled nodes on the eurswap curve. 
            
            **Content**  
            • The initial cont. compounded spot zero rates and discount factors on the analysis date (i.e the aforementioned eurswap curve)
            
            • The underlying euribor6m spot swap/par rates used for calibration
            
            • The derived euribor6m forward swap/par rates
            
            • Time series of euribor6m par swap rates
            
            • Sample of daily euribor6m rate levels and shifts in selected tenors
            
            • Sample covariance and correlation matrices for daily rate shifts (inputs to pca and mc simulation)  
            """, unsafe_allow_html = True)
         
# 1.2 Prepare dfs with data for rate curves on analysis date.
analysis_dt = pd.to_datetime( df_dict['scenarios']['hist_rates'].index.max() )

disc_factors = (
  df_dict['curve']['disc_factors'].copy()
    .rename( columns = {'DiscFactor' : 'disc factor', 'Node':'node'} ) 
)
curve_nodes_ordr = disc_factors['node'].values.tolist()
pd.Categorical( disc_factors["node"], categories = curve_nodes_ordr, ordered = True )

spot_zero_rates = (
  df_dict['curve']['spot_zero_rates'].copy()
    .rename( columns = {'SpotZeroRate' : 'cc zero rate (%)', 'Node':'node'} ) 
)
pd.Categorical( spot_zero_rates["node"], categories = curve_nodes_ordr, ordered = True )

spot_par_rates = (
  df_dict['curve']['spot_par_rates'].copy()
    .rename( columns = { 'Node':'tenor', 'SpotParRate' : 'spot par rate (%)'} ) 
)
spot_tenors_ordr = spot_par_rates['tenor'].values.tolist()
pd.Categorical( spot_par_rates["tenor"], categories = spot_tenors_ordr, ordered = True )

fwd_par_rates = (
  df_dict['curve']['fwd_par_rates'].copy()
    .rename( columns = { 'Node':'tenor', 'FwdParRate' : 'forward par rate (%)'} ) 
)
fwd_tenors_ordr = fwd_par_rates['tenor'].values.tolist()
pd.Categorical( fwd_par_rates["tenor"], categories = fwd_tenors_ordr, ordered = True )

# 1.3 Add dfs and charts depicting disc. factors, cc zero rates, spot par rates and forward par rates      
with tab1: 
    
    section_1 = st.container(border = False)

    with section_1: 
        
         st.subheader(f"1. eurswap curve and euribor6m swap rates on {analysis_dt.strftime('%Y-%m-%d')}")                 
        
         top_col1, top_col2, top_col3, top_col4 = st.columns([1,1,1,1])
         
         with top_col1: 
             
            disc_factors_chart = (
            alt.Chart(disc_factors)
            .mark_point(size = 100, filled = True)
            .encode(
                x = alt.X("node:N", title = "node", sort = curve_nodes_ordr, axis = alt.Axis(labelAngle = 0, grid = True)), 
                y = alt.Y("disc factor:Q", title = None),
                color = 
                alt.Color( legend = alt.Legend(orient = 'top')
                         ), 
                tooltip = ["node", "disc factor"]
            )
            .properties(height = 400, title = "eurswap disc factors")
            )
            
            chart_container = st.container(border = True)
            
            with chart_container: 
                
                st.altair_chart(disc_factors_chart, use_container_width = True)  

         with top_col2: 
             
            zero_rates_chart = (
            alt.Chart(spot_zero_rates)
            .mark_point(size = 100, filled = True)
            .encode(
                x = alt.X("node:N", title = "node", sort = curve_nodes_ordr, axis = alt.Axis(labelAngle = 0, grid = True)), 
                y = alt.Y("cc zero rate (%):Q", title = None),
                color = 
                alt.Color( legend = alt.Legend(orient = 'top')
                         ), 
                tooltip = ["node", "cc zero rate (%)"]
            )
            .properties(height = 400, title = "eurswap zero curve")
            )
            
            chart_container = st.container(border = True)
            
            with chart_container:  
                           
                st.altair_chart(zero_rates_chart, use_container_width = True)    

         with top_col3: 
             
            spot_par_rates_chart = (
            alt.Chart(spot_par_rates)
            .mark_point(size = 100, filled = True)
            .encode(
                x = alt.X("tenor:N", title = "tenor", sort = spot_tenors_ordr, axis = alt.Axis(labelAngle = 0, grid = True)), 
                y = alt.Y("spot par rate (%):Q", title = None),
                color = 
                alt.Color( legend = alt.Legend(orient = 'top')
                         ), 
                tooltip = ["tenor", "spot par rate (%)"]
            )
            .properties(height = 400, title = "euribor6m spot par curve")
            )
            
            chart_container = st.container(border = True)
            
            with chart_container: 
                            
                st.altair_chart(spot_par_rates_chart, use_container_width = True)    
            
         with top_col4: 
             
            fwd_par_rates_chart = (
            alt.Chart(fwd_par_rates)
            .mark_point(size = 100, filled = True)
            .encode(
                x = alt.X("tenor:N", title = "tenor", sort = fwd_tenors_ordr, axis = alt.Axis( labelAngle = 0, grid = True ) ), 
                y = alt.Y("forward par rate (%):Q", title = None),
                color = 
                alt.Color( legend = alt.Legend(orient = 'top')
                         ), 
                tooltip = ["tenor", "forward par rate (%)"]
            )
            .properties(height = 400, title = "euribor6m forward par curve")
            )

            chart_container = st.container(border = True)
            
            with chart_container:        
                                 
                st.altair_chart(fwd_par_rates_chart, use_container_width = True)                

    with section_1:
                 
         bottom_col1, bottom_col2, bottom_col3, bottom_col4 = st.columns([1,1,1,1])         
         
         with bottom_col1: 
             
              df_container = st.container(border = True)
              
              with df_container: 
                  
                st.dataframe(disc_factors, use_container_width = True)  

         with bottom_col2: 
             
              df_container = st.container(border = True)
              
              with df_container: 
                  
                st.dataframe(spot_zero_rates, use_container_width = True)   
             
         with bottom_col3: 
             
              df_container = st.container(border = True)
              
              with df_container: 
                  
                st.dataframe(spot_par_rates, use_container_width = True)  
                             
         with bottom_col4: 
             
              df_container = st.container(border = True)
              
              with df_container: 
                  
                st.dataframe(fwd_par_rates, use_container_width = True)  

# 1.4 Prepare dfs for swap rate time series 
swap_rate_ts = ( 
 df_dict['scenarios']['hist_rates'].copy()
  .reset_index()
  .rename(columns = {'index':'date'}) 
)

swap_rate_ts_long = (
 swap_rate_ts.melt(
    id_vars = "date",
    var_name = "tenor",
    value_name = "rate" )
)

swap_rate_ts_long["date"] = pd.to_datetime(swap_rate_ts_long["date"])
tenors = [clmn for clmn in swap_rate_ts.columns if clmn != 'date']
swap_rate_ts_long["tenor"] = pd.Categorical( swap_rate_ts_long["tenor"], categories = tenors, ordered = True )
date_tick_vals = pd.date_range( start = swap_rate_ts_long["date"].min(), end = swap_rate_ts_long["date"].max(), freq = "MS" )

# 1.5 Add time series chart
with tab1:
    
    st.subheader("2. time series for euribor6m swap rates (%)")
    
    section_2 = st.container(border=True)
    
    with section_2:
                
        selected_swap_rate_tenors = st.multiselect(
            "select tenors",
            tenors,
            default=["2Y", "5Y", "10Y", "30Y"]   
        )
        
        chart_swap_rate_ts_long = swap_rate_ts_long[swap_rate_ts_long['tenor'].isin(selected_swap_rate_tenors)].copy()
        
        curve_ts_chart = (
            alt.Chart(chart_swap_rate_ts_long)
            .mark_line()
            .encode(
                x=alt.X("date:T", axis=alt.Axis(format="%Y-%m", labelAngle=-60, grid = True)),
                y=alt.Y("rate:Q", title="swap rate (%)"),
                color=alt.Color("tenor:N", sort=tenors, legend = alt.Legend(orient = 'top'))
            )
            .properties(height=600)   
        )
        st.altair_chart(curve_ts_chart, use_container_width = True)    

# 1.6 Prepare dfs with sample rates and rate shifts 
dly_swap_rates = (  
 df_dict['scenarios']['hist_rates'].copy()
  .reset_index()
  .rename(columns = { 'index' : 'date'} )
  .assign( date = lambda df : df.date.dt.strftime("%Y-%m-%d"))
)

dly_swap_shifts = (
 df_dict['scenarios']['hist_shifts'].copy()
  .reset_index()
  .rename(columns = { 'index' : 'date'})
  .assign( date = lambda df : df.date.dt.strftime("%Y-%m-%d"))  
)

with tab1:
    
    st.subheader("3. sample data: daily euribor6m swap rates (%) and shifts (bps)")
    
    section_3 = st.container(border=True)
    
    section_4 = st.container(border=True)
    
    with section_3:
        
        st.dataframe(dly_swap_rates, hide_index = True, use_container_width = True, height = 1000)    
    
    with section_4:
        
        st.dataframe(dly_swap_shifts, hide_index = True, use_container_width = True, height = 1000)            
         
# 1.7 Add Variance-Covariance and Correlation Matrices
swap_rate_cov = ( 
 df_dict['scenarios']['hist_cov_mat'].copy()
  .rename( columns = { 'Node' : 'tenor' } )
)

swap_rate_corr = ( 
 df_dict['scenarios']['hist_corr_mat'].copy()
  .rename( columns = { 'Node' : 'tenor' } )
)

with tab1:
    
    st.subheader("3. sample covariance and correlation for daily swap rate shifts (bps)")
    
    section_5 = st.container(border=True)
    
    section_6 = st.container(border=True)
    
    with section_5:
        
        st.dataframe(swap_rate_cov, hide_index = True, use_container_width = True)
    
    with section_6:
        
        st.dataframe(swap_rate_corr, hide_index = True, use_container_width = True)            
                        
# ----------> 2.0 principal component analysis tab    
# 2.1 Add sub-page description 
with tab2:
    
   with st.expander("page info", expanded = False):        

    st.markdown("""
    **Overview**  
    This section presents the results of principal component analysis (pca) applied to historical euribor6m swap rate shifts.  
    In this project, pca is performed on the sample covariance matrix of rate changes (in bps), extracted from the historical time series in previous section.
    """)

    st.markdown("Let the sample covariance matrix be:")
    st.latex(r"\Sigma \in \mathbb{R}^{n \times n}")

    st.markdown("pca is obtained via eigenvalue decomposition:")
    st.latex(r"\Sigma = E \Lambda E^T")

    st.markdown("where:")
    st.latex(r"E = [e_1, \ldots, e_n]") 
    st.latex(r"\Lambda = \text{diag}(\lambda_1, \ldots, \lambda_n)")
    st.markdown("are the matrix of eigenvectors and diagonal matrix of eigenvalues, respectively.")  
    st.markdown("Each eigenvector satisfies:")
    st.latex(r"\Sigma e_i = \lambda_i e_i")
    st.markdown("""
    The eigenvalues represent the variance explained by each principal component, ordered such that:
    """)

    st.latex(r"\lambda_1 \geq \lambda_2 \geq \cdots \geq \lambda_n")

    st.markdown("""
    **Content**

    • **eigenvalues and explained variance** -> eigenvalues quantify the variance captured by each principal component; specifically, the ratio of variance explained by a 
      given&nbsp;principal component is:  
    """)
    st.latex(r"\frac{\lambda_i}{\sum_{j=1}^{n} \lambda_j}")

    st.markdown("""
    • **principal components** -> eigenvectors which define orthogonal directions of variation in the swap curve and are interpreted as PC1 (level), PC2 (slope), PC3 (curvature).  
    """)

    st.markdown("""
    • **pca factor loadings** -> these represent the impact (in basis points) on the swap curve for a (+1) unit shock in the corresponding PC, and are calculated as: 
    """)

    st.latex(r"f_i = \sqrt{\lambda_i} \, e_i")

    st.markdown("""
    • **pca multipliers (scores)** -> i.e. observed rate shifts, projected into PC space as:
    """)

    st.latex(r"z = E^T \, \Delta r")

    st.markdown("""
    &nbsp; where z contains the pca multipliers (scores), representing the contribution of each principal component (level, slope, curvature) to observed curve movements.
    """)
         
# 2.2 Create and dfs with eigenvalues and eigenvectors
pca_eigvals = df_dict['scenarios']['pca_eigvals'].copy()

pca_eigvecs = (
 df_dict['scenarios']['pca_eigvecs'].copy()
  .rename( columns = { 'Node': 'tenor' } )
)

with tab2:
    
    st.subheader("1. principal component analysis")
    
    section_1 = st.container(border=True)
    
    with section_1:
        
        st.subheader("eigenvalues (principal component variance)")
        
        st.dataframe(pca_eigvals.style.format("{:.4f}"), width = 1500, use_container_width = False, hide_index = True)
        
        st.subheader("eigenvectors (principal components)")
        
        st.dataframe(pca_eigvecs, hide_index = False)         

# 2.3 Create dfs with date for pca factor loadings chart (PC1-PC3)
factor_loadings = ( 
 df_dict['scenarios']['pca_loadings'].copy()
 .loc[:, 'Node' : 'PC3']
 .rename(columns = {'Node' : 'tenor', 'PC1':'PC1 (level)', 'PC2':'PC2 (slope)', 'PC3':'PC3 (curvature)'})
)

factor_loadings_long = (
 factor_loadings.melt(
  id_vars = "tenor",
  value_vars = ['PC1 (level)','PC2 (slope)','PC3 (curvature)'],
  var_name = "PC",
  value_name="swap rate shift (bps)" )
)

pca_tenor_order = factor_loadings['tenor'].to_list()

factor_loadings_long["tenor"] = pd.Categorical(
 factor_loadings_long["tenor"],
 categories = pca_tenor_order,
 ordered = True 
 )

# 2.4 Add chart for pca factor loading  
with tab2:
    
    st.subheader("2. pca factor loadings")    
    
    section_2 = st.container(border=True, width = "stretch", horizontal_alignment = "distribute")
    
    with section_2:
                
        factor_loading_chart = (
        alt.Chart(factor_loadings_long)
         .mark_line( point = True)
         .encode( 
             x = alt.X( "tenor:N", sort = pca_tenor_order, title = "tenor", axis = alt.Axis( labelAngle = 0, grid = True) ),
             y = alt.Y( "swap rate shift (bps):Q", title = "swap rate shift (bps)"),
             color = 
             alt.Color( "PC:N",
                        legend=alt.Legend(orient="top", title = None, direction="horizontal")
             ),
             tooltip = ["tenor", "PC", "swap rate shift (bps)"],              
             strokeDash = alt.StrokeDash("PC:N"),
             size = alt.condition(
                    alt.datum.PC == "PC1 (Level)",
                    alt.value(3),
                    alt.value(1.5)
             ) )
        .properties(height=600, width = "container", padding={"left": 10, "top": 10, "right": 10, "bottom": 10}) 
        )
        
        st.altair_chart( factor_loading_chart, use_container_width = True ) 

# 2.5 Create dfs with data to chart pca scores/multipliers on sample data
swap_rate_shifts = df_dict['scenarios']['hist_shifts'].copy()
multiplier_pca_eigvecs = (
 df_dict['scenarios']['pca_eigvecs'].copy()
 .loc[: , 'PC1' : 'PC3']
)

swap_rate_shifts_mat = swap_rate_shifts.values  # shape: (No. Dates = D, No. Tenors = N)
multiplier_pca_eigvecs_mat = multiplier_pca_eigvecs.values  # shape (No. Tenors = N, No. PCs = K)
pca_multipliers_mat = swap_rate_shifts_mat @ multiplier_pca_eigvecs_mat # (No. Dates = D, No. PCs = K)

pc_multipliers = (
 pd.DataFrame( pca_multipliers_mat, columns=["PC1 (Level)", "PC2 (Slope)", "PC3 (Curvature)"] )
   .assign( date = swap_rate_shifts.index )
   [['date', 'PC1 (Level)', 'PC2 (Slope)', 'PC3 (Curvature)']]
)

pc_multipliers_long = (
 pc_multipliers.melt(
    id_vars = "date",
    var_name = "PC",
    value_name = "PC multiplier" )
)

date_tick_vals = pd.date_range( start = pc_multipliers_long["date"].min(), end = pc_multipliers_long["date"].max(), freq = "MS" )

# 2.6 Add pc multipliers chart 
with tab2:
    
    st.subheader("3. pca multipliers (scores)")

    section_3 = st.container(border=True)
    
    with section_3:
        
        pc_multiplier_chart = (
        alt.Chart(pc_multipliers_long)
         .mark_line()
         .encode(
             x = alt.X( "date:T", title = "date", axis = alt.Axis( values = date_tick_vals, format = "%Y-%m", labelAngle = -60, grid = True ) ),
             y = alt.Y("PC multiplier:Q", title = "pc multiplier (score)"),
             color = 
             alt.Color( "PC:N", legend = alt.Legend( orient="top", title = None )
                      ),
             tooltip=["date", "PC", "PC multiplier"]
         )
         .properties(height = 600)
         .interactive() 
        )
        
        st.altair_chart(pc_multiplier_chart, use_container_width=True)

# ----------> 3.0 MC Simulation & Scenarios Tab     
# 3.1 Add section info 
with tab3:
    
   with st.expander("page info", expanded = False):        
       
    st.markdown("""
    **Overview**  
    This section presents the Monte Carlo simulation framework for euribor6m swap rates, which forms the basis for PnL simulation and CVaR analysis.  
    The simulation generates scenarios of market swap rates by sampling correlated rate shifts based on historical covariance.  
    For each simulated scenario:

    - swap rates are shocked  
    - The eurswap discount curve is recalibrated  
    - discount factors are derived  
    - positions and portfolios are revalued to obtain PnL outcomes  

    The simulation is driven by the sample covariance matrix of historical daily swap rate shifts (in bps),  
    using Cholesky decomposition.
    Let the sample covariance matrix of daily rate shifts be:    
    """)
    st.latex(r"\Sigma \in \mathbb{R}^{n \times n}")

    st.markdown("Cholesky decomposition is given by:")
    st.latex(r"\Sigma = L L^T")

    st.markdown("""where:""")
    st.latex(r"L")
    st.markdown("""is a lower triangular matrix capturing the correlation structure between tenors.""")

    st.markdown("Simulated independent standard normal shocks are given by:")
    st.latex(r"\epsilon \sim \mathcal{N}(0, I)")

    st.markdown("Correlated rate shocks are obtained as:")
    st.latex(r"\Delta r = L \epsilon")

    st.markdown("""where:""")
    st.latex(r"\Delta r")
    st.markdown("""represents simulated daily swap rate shifts across tenors (in basis points).""")

    st.markdown("""
    To obtain shocks over a longer horizon (e.g. 30 days), daily shocks are scaled under the i.i.d. normal assumption:
    """)

    st.latex(r"\Delta r_{(T)} = \sqrt{T} \cdot \Delta r")

    st.markdown("""
    where T is the time horizon in days. This project uses T=30.
    """)
    
    st.markdown("Simulated swap rates are constructed as:")
    st.latex(r"r^{(s)} = r^{(0)} + \Delta r^{(s)}")

    st.markdown("""
    where:""")
    st.latex(r"r^{(0)}") 
    st.latex(r"r^{(s)}")     
    st.markdown( """are the base (current) and the simulated scenario swap curves respectively.""" )  


    st.markdown("""
    **Content**

    • **mc simulated euribor6m swap rate shift scenarios across tenors**  
    
    • **mc simulated euribor6m swap rate curve scenarios**  
    
    • **pca multipliers (scores) for each scenarios** -> i.e. simulated rate shifts projected into  space using:
    """)

    st.latex(r"z^{(s)} = E^T \Delta r^{(s)}")

    st.markdown("""&nbsp;&nbsp;where:""")
    st.latex(r"z^{(s)}")
    st.markdown("""&nbsp;&nbsp;represents the decomposition/representation of each scenario into principal components (level, slope, and curvature).""")

# 3.2 Create dfs with data for mc simulation tab
analysis_dt = pd.to_datetime( df_dict['scenarios']['hist_rates'].index.max() )

base_swap_rates = ( 
 df_dict['scenarios']['hist_rates'][df_dict['scenarios']['hist_rates'].index == analysis_dt]
  .copy()
  .reset_index()
  .rename( columns = {'index' : 'scenario'} )
  .assign( scenario = -1 )
)

base_swap_rates_long = (
 base_swap_rates.melt(
  id_vars = "scenario", 
  var_name = "tenor", 
  value_name = "swap rate (%)" )
)

_mc_swap_rates = (
 df_dict['scenarios']['sim_rates'].copy()
  .rename( columns = {'Scenario' : 'scenario'} )
)

_mc_swap_rates_long = (
 _mc_swap_rates.melt(
  id_vars = "scenario", 
  var_name = "tenor", 
  value_name = "swap rate (%)" )
)

mc_swap_rates = pd.concat([_mc_swap_rates, base_swap_rates], ignore_index = True, axis = 0)
mc_swap_rates_long = pd.concat([_mc_swap_rates_long, base_swap_rates_long], ignore_index = True, axis = 0)

mc_scenarios = _mc_swap_rates.scenario.to_list()   
mc_tenor_ordr = _mc_swap_rates_long.tenor.unique().tolist()   
        
mc_prms = (
 df_dict['scenarios']['sim_parameters'].copy()
  .rename( columns = {'Analysis Date':'analysis date', 'No. Scenarios':'scenarios', 'Time Scaling (Days)':'time scaling (days)'} )
)
mc_prms['analysis date'] = mc_prms['analysis date'].dt.strftime("%Y-%m-%d")

mc_pc_multipliers = (
 df_dict['scenarios']['sim_pc_multipliers'].copy().loc[:,:'PC3']
  .rename( columns = {'Scenario' : 'scenario', 'PC1' : 'PC1 (level)', 'PC2' : 'PC2 (slope)', 'PC3' : 'PC3 (curvature)'} )
)

mc_pc_multipliers_long = (
 mc_pc_multipliers.melt(
  id_vars = "scenario", 
  var_name = "PC", 
  value_name = "multiplier (score)" )     
 )

mc_swap_shifts = (
 df_dict['scenarios']['sim_shifts'].copy()
  .rename( columns = {'Scenario' : 'scenario'} )
)

mc_swap_shifts_long = (
 mc_swap_shifts.melt( 
  id_vars = "scenario", 
  var_name = "tenor", 
  value_name = "swap rate shift (bps)" )
)   

                                                                        
# 3.3 Add dataframe with MC Simulation parameters 
with tab3:
    
    st.subheader("1. mc simulation")
    
    section_1 = st.container(border = True)
    
    with section_1: 
        
        st.dataframe(mc_prms, hide_index = True)
            
# 3.4 Add chart to visualize simulated rate shifts in MC scenarios 
with tab3:
    
    st.subheader("2. simulated euribor6m swap rate shocks")
    
    col1, col2 = st.columns([1,1])
    
    with col1:
        
        left_chart = st.container(border = True)
    
    with col2:
        
        right_chart = st.container(border = True)
    
    with left_chart: 
        
        st.subheader("histogram")
        
        selected_mc_swap_shift_tenor = st.selectbox( # (!) st selector widgets must be uniquely named
         "select tenor", 
         mc_tenor_ordr, 
         index = 0 
        )
        
        chart_mc_swap_shifts_long = mc_swap_shifts_long[mc_swap_shifts_long['tenor'] == selected_mc_swap_shift_tenor]        
        
        mc_swap_shifts_hist_chart = (
        alt.Chart( chart_mc_swap_shifts_long )  
         .mark_bar(opacity = 0.8, stroke="white", strokeWidth=0.5)
         .encode(
             x = alt.X( "swap rate shift (bps):Q", bin = alt.Bin(maxbins = 50), title = 'swap rate shift (bps)',  axis = alt.Axis(grid = True) ),
             y = alt.Y( "count()", title = "frequency"), 
             color = 
             alt.Color( "tenor:N",
                        legend = alt.Legend(orient="top"), 
                        title = None 
                      ) 
         )
         .properties( height = 400 )               
        )
        
        st.altair_chart(mc_swap_shifts_hist_chart, use_container_width = True)
        
    with right_chart: 
        
        st.subheader("density plot")
        
        selected_mc_swap_shift_tenors = st.multiselect(
         "select tenor(s)",
         mc_tenor_ordr,
         default = [mc_tenor_ordr[i] for i in [0, 4]]
        )
        
        chart_mc_swap_shifts_long = mc_swap_shifts_long[mc_swap_shifts_long['tenor'].isin(selected_mc_swap_shift_tenors)]        
        
        mc_swap_shifts_density_chart = (
        alt.Chart( chart_mc_swap_shifts_long )  
         .transform_density( "swap rate shift (bps)", groupby = ["tenor"], as_ = ["swap rate shift (bps)", "density"] )
         .mark_line( size = 2 )
         .encode(
             x = alt.X("swap rate shift (bps):Q", title = "swap rate shift (bps)"),
             y = alt.Y("density:Q", title = "density"),
             color = 
             alt.Color( "tenor:N",
                        legend = alt.Legend(orient="top"),
                        title = None 
                      ), 
             tooltip = [ alt.Tooltip("tenor:N"),
                         alt.Tooltip("swap rate shift (bps):Q"),
                         alt.Tooltip("density:Q")
                       ] )
         )
        
        mc_swap_shifts_moments = (chart_mc_swap_shifts_long.groupby("tenor")["swap rate shift (bps)"].agg(["mean", "std"]).reset_index())

        mc_swap_shifts_mean = mc_swap_shifts_moments.copy()
        mc_swap_shifts_mean["type"] = "μ"
        mc_swap_shifts_mean["value"] = mc_swap_shifts_mean["mean"]

        mc_swap_shifts_std_right = mc_swap_shifts_moments.copy()
        mc_swap_shifts_std_right["type"]  = "+3σ"
        mc_swap_shifts_std_right["value"] = mc_swap_shifts_std_right["mean"] + mc_swap_shifts_std_right["std"] * 3

        mc_swap_shifts_std_left = mc_swap_shifts_moments.copy()
        mc_swap_shifts_std_left["type"]  = "-3σ"
        mc_swap_shifts_std_left["value"] = mc_swap_shifts_std_left["mean"] - mc_swap_shifts_std_left["std"] * 3
        
        mc_swap_shifts_moments_long = pd.concat([mc_swap_shifts_mean, mc_swap_shifts_std_right, mc_swap_shifts_std_left])
        
        chart_mc_swap_shifts_moments = (
         alt.Chart(mc_swap_shifts_moments_long)
         .mark_rule(size=2)
         .encode(
            x = "value:Q",
            color = 
            alt.Color("tenor:N", legend=None),
            strokeDash = alt.StrokeDash( "type:N", scale = alt.Scale( domain=["μ", "+3σ", "-3σ"],
                    range=[[1, 0], [4, 4], [4, 4]]
                )
            ),
            tooltip = ["tenor", "type", "value"] ) 
         )

        mc_swap_shifts_density_chart = (
            alt.layer(mc_swap_shifts_density_chart, chart_mc_swap_shifts_moments)
               .properties(height=400) )

        st.altair_chart(mc_swap_shifts_density_chart, use_container_width=True)
         
# 3.5 Add chart which (always) shows the base curve and the selected MC Scenario curve
with tab3:
    
    st.subheader("3. simulated euribor6m swap rate curves")
    
    section_3 = st.container(border=True)
    
    with section_3:

         selected_mc_scenarios = st.multiselect(
             "select scenario(s)",
             mc_scenarios,
             default = mc_scenarios[:3]   
         )
         
         st.markdown("scenario = -1 corresponds to the base/current swap rate curve")
         chart_mc_swap_rates_long = mc_swap_rates_long[ ( mc_swap_rates_long["scenario"] == -1) | ( mc_swap_rates_long["scenario"].isin(selected_mc_scenarios) ) ]
         mc_swap_rate_curve_chart = (
         alt.Chart( chart_mc_swap_rates_long )
          .mark_line(point = True)
          .encode(
              x = alt.X( "tenor:N", sort = mc_tenor_ordr, title = "tenor", axis = alt.Axis(grid = True) ),
              y = alt.Y( "swap rate (%):Q", title = "swap rate (%)", scale = alt.Scale(domain = [1.5, 4.5]), axis  = alt.Axis( values = np.arange(0, 10.01, 0.10), format = ".2f")),
              color = 
              alt.Color( "scenario:N",
                         legend = alt.Legend(orient="top"), 
                         title = None 
                       ),
              strokeDash = 
              alt.condition( alt.datum.scenario == -1,
                             alt.value([5,5]),
                             alt.value([1,0])
                           ),
              tooltip=["scenario", "tenor", "swap rate (%)"] )
            .properties(height = 600) 
         )
                 
         st.altair_chart(mc_swap_rate_curve_chart, use_container_width = True)        
        
# 3.6 Add dfs with simulated shifts and rates 
with tab3:
    
    st.subheader("4. mc scenarios")
    
    section_4 = st.container(border=True, height = 700)
    
    section_5 = st.container(border=True, height = 700)
    
    with section_4:
        
        st.markdown("""swap rate shifts (bps)""")
        
        st.dataframe(mc_swap_shifts, hide_index = True, height = "stretch")    
    
    with section_5:
        
        st.markdown("""swap rates (%)""")        
        
        st.dataframe(mc_swap_rates, hide_index = True, height = "stretch")    
        
# 3.7 Add df and chart with pca multipliers (scores) for the mc simulated swap rate shifts
with tab3:
    
    st.subheader("5. pca multipliers (scores) for simulated swap rate shifts")

    section_6 = st.container(border=True)
    
    section_7 = st.container(border=True, height = 700)
    
    with section_6:
        
        mc_pc_multiplier_chart = (
        alt.Chart(mc_pc_multipliers_long)
         .mark_line()
         .encode(
             x = alt.X( "scenario:Q", title = "scenarios", axis = alt.Axis( values = mc_scenarios, labelAngle = -90, grid = True ) ),
             y = alt.Y("multiplier (score):Q", title = "pc multiplier (score)"),
             color = 
             alt.Color( "PC:N", legend = alt.Legend( orient="top", title = None )
                      ),
             tooltip=["scenario", "PC", "multiplier (score)"]
         )
         .properties(height = 600, width = 600)
         .interactive() 
        )
        
        st.altair_chart(mc_pc_multiplier_chart, use_container_width=True)
    
    with section_7: 
        
        st.dataframe(mc_pc_multipliers, hide_index = True, height = "stretch")
        
        
