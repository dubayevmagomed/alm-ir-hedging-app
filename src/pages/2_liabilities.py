
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
    "liability portfolio (unhedged)",
    "portfolio risk",
    "mc PnL simulation & CVaR"
])

# 0.3.0 Data dictionary with all dfs for the streamlit app  
df_dict = current_page_parquet_loader()

# ----------> 1.0 Casfhlows Tab
# 1.1 Add sub-page description 
with tab1:
    
    with st.expander("page info", expanded = False):
         st.markdown("""
            **Overview**  
            This section presents pension liabilities which will be hedge using IRS overlay/hedge. 
            The liabilities are modelled as a single, aggregated short position of Zero Coupon Bond instruments.
            Maturity of ZCBs corresponds to the payment schedule of the funds projected cashflows (outflows). 
            The position is priced using discount factors from the eurswap curve (see risk factor page for details).
            Nonclameture: The pension liabilities without IRS overlay/hedge are referred to as "liability portfolio (unhedged)"
            
            **Content**  
            • Cashflow profile of liabilities.  
            
            • PV of unhedged liability portfolio, i.e. without overlay, and overview of underlying ZCB instruments.                         
            """)
         
# 1.1 Create df for liability cashflows chart 
analysis_dt = pd.to_datetime(df_dict['liability_position']['cashflows']['Date'].unique()[0])

cashflows = (
 df_dict['liability_position']['cashflows']
  .copy()[['Payment Date', 'Cashflow', 'PV']]
  .rename( columns = { 'Payment Date' : 'payment date', 'Cashflow' : 'cashflow', 'PV' : 'present value' } )
)

cashflows_long = (
 cashflows.melt(
  id_vars = "payment date", 
  value_vars = ["cashflow", "present value"], 
  var_name = "metric", 
  value_name = "value" )
)

# 1.2 Add cashflow chart 
with tab1:         
    
    st.subheader(f"1. cashflow profile")
    
    section_1 = st.container(border=True)
    
    with section_1: 
        
        cashflows_chart = (
        alt.Chart( cashflows_long  )     
         .mark_bar(size=20, opacity=0.7)
         .encode( 
             x = alt.X("payment date:T", title = "payment date", axis=alt.Axis(format="%Y-%m", labelAngle=-45)),
             xOffset = "metric:N",
             y = alt.Y("value:Q", title = "EUR", stack = None),
             color = 
             alt.Color( "metric:N",
                        scale = alt.Scale( domain=["cashflow", "present value"], range=["#0023C0", "#16F95E"]),
                        title = None,
                        legend=alt.Legend(orient="top")
                     ),
             tooltip=[ alt.Tooltip( "payment date:T", title="date"),
                       alt.Tooltip( "metric:N"),
                       alt.Tooltip( "value:Q", format=",.0f")
                     ] 
        )
        .properties(height = 600)
        )
        
        st.altair_chart(cashflows_chart, use_container_width=True)

# 1.2 Add dfs with liability portfolio, position and underlying ZCB instruments 
liability_prtfl = (
  df_dict['liability_portfolio']['npv'].copy()
   .rename(
     columns = {'Date' : 'analysis date',
                'Portfolio ID' : 'portfolio id', 
                'Position Grp' : 'position group', 
                'Position ID' : 'position id', 
                'Ccy' : 'currency', 
                'Curve' : 'curve', 
                'PV' : 'present value'
                })
   .assign(curve = lambda df : df['curve'].str.lower()) 
   .iloc[[0],:]
)

liability_prtfl['analysis date'] = liability_prtfl['analysis date'].dt.strftime('%Y-%m-%d')

zcbs = (
 df_dict['liability_position']['cashflow_zcb_positions'].copy() 
  .rename(
    columns = { 'Cashflow Zero Coupon Bond' : 'instrument',
                'Notional' : 'notional', 
                'Ccy' : 'currency', 
                'Maturity Date' : 'maturity date', 
                'Maturity Years' : 'maturity years', 
                'Curve' : 'curve', 
                'PV' : 'present value'
                })
  .assign( instrument = lambda df : np.where(df['instrument'], df['instrument'] + 'Y', df['instrument']), 
           curve = lambda df : df.curve.str.lower()
         ) 
)

zcb_total_row = (
 zcbs[['notional','present value']].sum().to_frame().T
  .assign( 
    **{ 'instrument' : 'aggregated position' , 
        'currency' : 'EUR',
        'maturity date' : pd.to_datetime(zcbs['maturity date'].max()),  
        'maturity years' : zcbs['maturity years'].max(), 
        'curve' : 'eurswap', 
        'DF' : ''
      } )
  [zcbs.columns]
)

zcb_instruments = pd.concat( [zcb_total_row, zcbs]).reset_index(drop=True)
zcb_instruments['maturity date'] = zcb_instruments['maturity date'].dt.strftime('%Y-%m-%d')

with tab1:
    
    st.subheader(f"2. liability portfolio and zcb instruments on {analysis_dt.strftime('%Y-%m-%d')}")
    
    section_2 = st.container(border=True)
    
    section_3 = st.container(border=True, height = 800)
    
    with section_2:

        numeric_clmns = liability_prtfl.select_dtypes( include = 'number').columns
                
        st.dataframe( liability_prtfl.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), hide_index = True)
    
    with section_3:
        
        numeric_clmns = zcb_instruments.select_dtypes(include = 'number').columns

        st.dataframe( zcb_instruments.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns } ), height = "stretch" )
        
# ----------> 2.0 risk sensitivities Tab 
# 2.1 Add sub-page description 
with tab2:
    
 with st.expander("page info"):
     
   st.markdown("""
     **Overview**  
     This section presents risk sensitivities for the liability portfolio. Sensitivities are calculated wrt. to spot par rates and forward par rates""")
    
   st.markdown("""
    Forward sensitivities are derived from spot pv01 delta, via spot-to-forward transformation (Jacobian).""") 
      
   st.markdown("""  """)
   st.markdown("""  """)   
     
   st.markdown("**a. Spot Rate Sensitivities (spot PV01 delta and gamma):**")

   st.latex(r"\text{PV01}_{\text{spot}} = \frac{\partial \text{PV}}{\partial r}, \quad \quad \Gamma_{\text{spot}} = \frac{\partial^2 \text{PV}}{\partial r^2}")
    
   st.markdown("&nbsp;&nbsp;represent the first- and second-order sensitivities to spot par swap rates used for construction of the of the discount curve. Thus: ")

   st.latex(r"r \in \mathbb{R}^{N \times 1}")
    
   st.markdown("&nbsp;&nbsp;is the observed vector of euribor6m swap rates across selected tenors (2Y, 3Y,...). Both measures are calculated for a 1 bps rate shift.")
   
   st.markdown("""  """)
   st.markdown("""  """)   
   
   st.markdown("**b. Forward Rate Sensitivities (forward PV01 delta):**")

   st.latex(r"\text{PV01}_{\text{forward}} = \frac{\partial \text{PV}}{\partial f}", )

   st.markdown("""&nbsp;&nbsp;provide an alternative measure of spot delta risk in terms of forward rates. The transformation of spot delta to forward delta risk is defined via the Jacobian:""")
    
   st.latex(r"\text{PV01}_{\text{forward}} = J_{r \rightarrow f} \text{PV01}_{\text{spot}}")

   st.latex(r"J_{r \rightarrow f} = \frac{\partial r}{\partial f}")

   st.latex(r"(J_{r \rightarrow f})_{ij} = \frac{\partial r_{j}}{\partial f_{i}}")
   
   st.markdown("&nbsp;&nbsp;The Jacobian captures the relationship between spot and forward rates, implied by the constructed curve.")
   
   st.markdown("""  """)
   st.markdown("""  """)   
   
   st.markdown("""
    **Content**

    • Spot PV01 delta and gamma  
    
    • Forward PV01 delta (via spot-to-forward transformation)  
    """)

# 2.2 Prepare dfs with risk sensitivities 
sens_prms = (
 df_dict['liability_portfolio']['spot_delta']
 [ df_dict['liability_portfolio']['spot_delta']['Position ID'] == 'Total' ]
 .copy()[['Date','Portfolio ID','Curve','Ccy']]
 .assign( Curve = lambda df : df.Curve.str.lower() )
 .rename(columns = { 'Date' : 'analysis date', 'Portfolio ID' : 'portfolio id', 'Ccy' : 'currency', 'Curve' : 'curve'})
)
sens_prms['analysis date'] = sens_prms['analysis date'].dt.strftime("%Y-%m-%d")

# spot delta 
_df = (
  df_dict['liability_portfolio']['spot_delta']
  [ df_dict['liability_portfolio']['spot_delta']['Position ID'] == 'Total' ]
)
_sens_type = _df['Sensitivity'].values[0].lower()
_sens_clmns = [clmn for clmn in _df.select_dtypes( include = 'number').columns if clmn != 'Total'] + ['Total']
spot_delta = _df[_sens_clmns].T.reset_index().rename( columns = {'index':'tenor', 1 : _sens_type } )

spot_tenor_sort_ordr = [clmn for clmn in _df.select_dtypes( include = 'number').columns if clmn != 'Total']

# spot gamma 
_df = (
  df_dict['liability_portfolio']['spot_gamma']
  [ df_dict['liability_portfolio']['spot_gamma']['Position ID'] == 'Total' ]
)
_sens_type = _df['Sensitivity'].values[0].lower()
_sens_clmns = [clmn for clmn in _df.select_dtypes( include = 'number').columns if clmn != 'Total'] + ['Total']
spot_gamma = _df[_sens_clmns].T.reset_index().rename( columns = {'index':'tenor', 1 : _sens_type } )

# fwd delta
_df = (
  df_dict['liability_portfolio']['fwd_delta']
  [ df_dict['liability_portfolio']['fwd_delta']['Position ID'] == 'Total' ]
 )
_sens_type = _df['Sensitivity'].values[0].lower()
_sens_clmns = [clmn for clmn in _df.select_dtypes( include = 'number').columns if clmn != 'Total'] + ['Total']
fwd_delta = _df[_sens_clmns].T.reset_index().rename( columns = {'index':'tenor', 1 : _sens_type } )

fwd_tenor_sort_ordr = [clmn for clmn in _df.select_dtypes( include = 'number').columns if clmn != 'Total']

with tab2: 
    
    st.subheader(f"1. portfolio risk sensitivities")                 
         
    section_0 = st.container(border = False)
    
    with section_0:
        
        st.dataframe(sens_prms, hide_index = True, width = "stretch")

    section_1 = st.container(border = False, width = 2000)

    with section_1: 
            
         top_col1, top_col2, top_col3 = st.columns([1,1,1])
         
         with top_col1: 
            
            col_container = st.container(border = True)
            
            with col_container: 
                
                st.markdown("spot pv01", text_alignment = "center")
                
                spot_delta_chart = (
                alt.Chart(spot_delta[spot_delta.tenor != 'Total'])
                .mark_bar(opacity = 0.8, stroke="white", strokeWidth=0.5)
                .encode(
                    x=alt.X("tenor:N", title="tenor", sort = spot_tenor_sort_ordr, axis = alt.Axis(labelAngle=-65, grid = True)),
                    y=alt.Y("spot pv01:Q", title=None),
                    color=alt.condition(
                        alt.datum["spot pv01"] > 0,
                        alt.value("#0411a1b6"),  
                        alt.value("#a1045db6")   
                    ),
                    tooltip=["tenor", alt.Tooltip("spot pv01:Q", format=",.0f")]
                )
                .properties(height = 450, width = 500)
                )
                
                st.altair_chart(spot_delta_chart)
                

         with top_col2: 
             
            col_container = st.container(border = True)
            
            with col_container: 

                st.markdown("forward PV01", text_alignment = "center")
             
                fwd_delta_chart = (
                alt.Chart(fwd_delta[fwd_delta.tenor != 'Total'])
                .mark_bar(opacity = 0.8, stroke="white", strokeWidth=0.5)
                .encode(
                    x=alt.X("tenor:N", title="tenor", sort = fwd_tenor_sort_ordr, axis = alt.Axis(labelAngle=-65, grid = True, values = fwd_tenor_sort_ordr)),
                    y=alt.Y("forward pv01:Q", title=None),
                    color=alt.condition(
                        alt.datum["forward pv01"] > 0,
                        alt.value("#0411a1b6"), 
                        alt.value("#a1045db6")   
                    ),
                    tooltip=["tenor", alt.Tooltip("forward pv01:Q", format=",.0f")]
                )
                .properties(height = 450, width = 500)
                )
                
                st.altair_chart(fwd_delta_chart)
            
         with top_col3: 
             
            col_container = st.container(border = True)
                         
            with col_container: 

                st.markdown("spot gamma", text_alignment = "center")
             
                spot_gamma_chart = (
                alt.Chart(spot_gamma[spot_gamma.tenor != 'Total'])
                .mark_bar(opacity = 0.8, stroke="white", strokeWidth=0.5)
                .encode(
                    x=alt.X("tenor:N", title="tenor", sort = spot_tenor_sort_ordr, axis = alt.Axis(labelAngle=-65, grid = True)),
                    y=alt.Y("gamma:Q", title=None),
                    color=alt.condition(
                        alt.datum["gamma"] > 0,
                        alt.value("#020202b6"), 
                        alt.value("#a1045db6")   
                    ),
                    tooltip=["tenor", alt.Tooltip("gamma:Q", format=",.0f")]
                )
                .properties(height = 450, width = 500)
                )
                
                st.altair_chart(spot_gamma_chart)
                
    with section_1: 
            
         bottom_col1, bottom_col2, bottom_col3 = st.columns([1,1,1])               
         
    with bottom_col1: 
        
        df_container = st.container(border = True, height = 400, vertical_alignment = "center")
        
        with df_container: 
        
            st.dataframe(spot_delta.style.format( { spot_delta.columns[1] : "{:,.2f}" } ), height = "content")
    
    with bottom_col2: 
        
        df_container = st.container(border = True, height = 400, vertical_alignment = "center")
        
        with df_container: 
        
            st.dataframe(fwd_delta.style.format( { fwd_delta.columns[1] : "{:,.2f}" } ), height = "content")    
            
    with bottom_col3: 
        
        df_container = st.container(border = True, height = 400, vertical_alignment = "center")
        
        with df_container: 
        
            st.dataframe(spot_gamma.style.format( { spot_gamma.columns[1] : "{:,.2f}" } ), height = "content")                
             
# ----------> 3.0 risk sensitivities Tab 
# 3.1 Add sub-page description 
with tab3:
    
 with st.expander("page info"):

    st.markdown("""
    **Overview**  
    This section presents the simulation of portfolio PnL under Monte Carlo scenarios of swap rate movements, 
    together with tail risk measurement via Conditional Value-at-Risk (CVaR).  

    PnL is obtained by full revaluation of the portfolio under simulated yield curves.  
    In addition, a first-order approximation based on spot PV01 is used to attribute tail risk to underlying rate exposures.
    """)

    st.markdown("**a. Monte Carlo PnL (Full Revaluation)**")

    st.markdown("&nbsp;&nbsp;&nbsp;PnL in a mc scenario is defined as the change in portfolio value:")

    st.latex(r"\text{PnL}^{(s)} = \text{PV}^{(s)} - \text{PV}^{(0)}")

    st.markdown("""&nbsp;&nbsp;&nbsp;where: """)

    st.latex(r"\text{PV}^{(0)}, \quad \text{PV}^{(s)}") 

    st.markdown("""are the base and scenario present values respectively.""")
    
    st.markdown("**b. Monte Carlo CVaR (Expected Shortfall)**")

    st.markdown("&nbsp;&nbsp;&nbsp;Tail risk is measured using CVaR:")

    st.latex(r"\text{CVaR}_{\alpha} = \mathbb{E}\left[ \text{PnL} \mid \text{PnL} \leq \text{VaR}_{\alpha} \right]")

    st.markdown("""&nbsp;&nbsp;&nbsp;where:""") 

    st.latex(r"\text{VaR}_{\alpha}")

    st.markdown("""&nbsp;&nbsp;&nbsp;is the chosen quantile of the PnL distribution. CVaR represents the average loss across the worst-performing scenarios. """)

    st.markdown("**c. First-Order PnL Approximation (Delta PnL)**")

    st.markdown("&nbsp;&nbsp;&nbsp;A first-order approximation of PnL is given by:")

    st.latex(r"\text{PnL}^{(s)} \approx \frac{\partial \text{PV}}{\partial r} \cdot \Delta r^{(s)}")

    st.markdown("""&nbsp;&nbsp;&nbsp;where:""")
    
    st.latex(r"\frac{\partial \text{PV}}{\partial r} , \quad \Delta r^{(s)} ") 

    st.markdown("""&nbsp;&nbsp;&nbsp;are the spot PV01 vector and the vector of rate shifts in a given scenario.""")

    st.markdown("**d. Delta-Based CVaR Attribution**")

    st.markdown("""&nbsp;&nbsp;&nbsp;Tail risk can be attributed to rate exposures by averaging first-order PnL across tail scenarios:""")

    st.latex(r"\text{CVaR}_{\alpha}^{\Delta} \approx \mathbb{E}\left[ \frac{\partial \text{PV}}{\partial r} \cdot \Delta r \;\middle|\; \text{PnL} \leq \text{VaR}_{\alpha} \right]")

    st.markdown("""&nbsp;&nbsp;&nbsp;This provides an approximative decomposition of tail losses in terms of underlying rate tenors.""")

    st.markdown("""
        **Content**  
        The section is organized as follows:

        • Hedging instruments (IRS)  
        
        • Hedge construction (weights and notionals)  
        
        • PnL comparison: benchmark hedge vs. unhedged portfolio  
        
        • Risk sensitivities of the hedged portfolio  
        
        • Monte Carlo CVaR and PnL of the hedged portfolio  

    """)
    
 # 3.2 Create dfs with portfolio CVaR, simulated PnL and CVaR PV01 attribution 
cvar = ( 
 df_dict['liability_portfolio']['prtfl_cvar'].copy()
  [ [clmn for clmn in df_dict['liability_portfolio']['prtfl_cvar'] if 'omponent' not in clmn] ]
  .rename( columns = {'Date' : 'analysis date', 'Ccy' : 'currency', 'Curve' : 'curve'} )
  .assign( curve = lambda df : df.curve.str.lower() )
 )
cvar.columns = [clmn.lower() for clmn in cvar.columns]

var_loss = - cvar.iloc[:,-2][0]
mc_pnl = (
 df_dict['liability_portfolio']['sim_prtfl_pnl'].copy()[['Scenario', 'PnL']]
  .rename( columns = {'Scenario' : 'scenario'} )
  .assign(
    **{ 'tail scenario' : lambda df : np.where( df.PnL <= var_loss, 'Y', 'N' ) , 
        'scenario rank' : lambda df : df.PnL.rank().astype('int')
      } )
  [['scenario','scenario rank','tail scenario','PnL']]
)

cvar_pv01_attr = ( 
 df_dict['liability_portfolio']['pv01_delta_cvar_attr']
  .copy()
  [ [ clmn for clmn in (df_dict['liability_portfolio']['pv01_delta_cvar_attr'])
                       .select_dtypes( include = 'number')
                        .columns 
      if clmn != 'Total'
    ] + ['Total'] ]
  .T 
  .reset_index()  
  .rename( columns = {'index' : 'tenor', 0 : 'average PnL i CVaR tail', 1 :'average PnL as % of mc CVaR/tail loss' } ) 
)

with tab3:
    
    st.subheader("1. portfolio MC CVaR")
    
    section_1 = st.container(border = True)
    
    with section_1:
        
        numeric_clmns = cvar.select_dtypes( include = 'number').columns
        
        cvar['analysis date'] = cvar['analysis date'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(cvar.style.format( { clmn: "{:,.2f}" for clmn in numeric_clmns }  ), hide_index = True)
    
    st.subheader("2. simulated PnL distribution")
    
    section_2 = st.container(border = True, height = 700)
    
    with section_2:
              
        pnl_hist_chart = (
            alt.Chart(mc_pnl[['scenario','PnL']])
            .mark_bar(opacity=0.8)
            .encode(
                x=alt.X(
                    "PnL:Q",
                    bin=alt.Bin(maxbins=50),
                    title="PnL (EUR)",
                    axis=alt.Axis(grid=True)
                ),
                y=alt.Y("count()", title=None)
            )
        )

        pnl_density_chart = (
            alt.Chart(mc_pnl[['scenario','PnL']])
            .transform_density(
                "PnL",
                as_=["PnL", "density"]
            )
            .mark_line(size=2, color="green")
            .encode(
                x=alt.X("PnL:Q", title ="PnL (EUR)"),
                y=alt.Y("density:Q", title = None)
            )
        )

        var_line = (
            alt.Chart( cvar.iloc[:,[-2]].rename(columns = {'standalone 95.0% mc var' : '95% VaR'} ) * -1 )
            .mark_rule(color="red", size=3)
            .encode ( x = "95% VaR:Q" )
        )
        
        var_label = (
            alt.Chart(pd.DataFrame({
                "x": [ cvar.iloc[:,-2][0] * -1 ],
                "text": ["VaR Quantile"]
            }))
            .mark_text(
                dx=10,
                dy=-10,
                color="red",
                fontSize=12
            )
            .encode(
                x="x:Q",
                y=alt.value(0),
                text="text:N"
            )
        )
        
        pnl_chart = (
            alt.layer(pnl_hist_chart, pnl_density_chart, var_line, var_label)
            .resolve_scale( y = "independent" )   
            .properties(height=400)
        )

        st.altair_chart(pnl_chart, use_container_width = True, height = "stretch")
    
    section_3 = st.container(border = True, height = "content", width = 2000)
    
    with section_3:
        
        st.subheader("3. spot PV01 CVaR attribution")        

        st.dataframe(cvar_pv01_attr.style.format( 
                     { clmn : "{:,.2f}" 
                       for clmn in cvar_pv01_attr.columns if clmn != 'tenor'
                      }  ), height = "content"
                    )
                       
    section_4 = st.container(border = True, height = "content", width = 2000)  
        
    with section_4:
        
        st.subheader("4. pnl scenarios (full revaluation)")        
        
        st.dataframe(mc_pnl.style.format( { 'PnL' : "{:,.2f}" }  ), hide_index = True, height = "content")
        
        
