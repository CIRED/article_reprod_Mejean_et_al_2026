# /home/leblanc/bin/anaconda3/envs/MostUpdated/bin/python

import pyam
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import pandas as pd
import matplotlib.gridspec as gridspec
import seaborn as sns
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes, mark_inset
import numpy as np

dpi=100 # dpi
sns.set(style="whitegrid")  # Apply Seaborn style

pd.DataFrame.iteritems = pd.DataFrame.items

# Enable LaTeX rendering
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman"]
})

exec(open('lib.py').read())

##################################
# LOAD DATA
##################################

results_folder = "outputs/"

output_fig = "figures/"

if not os.path.exists(output_fig):
    os.mkdir(output_fig)

list_file = [elt for elt in os.listdir(results_folder) if ".xlsx" in elt]
df_data = pyam.concat( [pyam.IamDataFrame(results_folder+x) for x in list_file])

# Mdels results from simulations

input_fold = "input_data/"
list_file = [elt for elt in os.listdir(input_fold) if ".xlsx" in elt and not '.log' in elt]
list_file_noE3M = [e for e in list_file if not "E3ME" in e]
df_simu = pyam.concat( [pyam.IamDataFrame(input_fold+x) for x in list_file_noE3M])
df_e3m = pyam.IamDataFrame(input_fold+'macroMIP_T2.6_inequality_E3ME.xlsx')
df_e3m = pyam.IamDataFrame(df_e3m.timeseries().reset_index().drop("unnamed: 0",axis=1))
df_simu = pyam.concat( [df_simu,df_e3m])


df_simu = drop_duplicates_model(df_simu, df_data)

df_data = pyam.concat( [df_data, df_simu])

# Compute emissions per capita

df_data.divide("Emissions|CO2", "Population", "Emissions_Capita", append=True,  ignore_units=True)
df_data.divide("Emissions|CO2", "GDP|MER", "Emissions_GDP", append=True,  ignore_units=True)

df_data = df_data.rename( {"unit": {u:u.replace('$','\$') for u in df_data.unit}})

# Compute income by decile
for i in range(4):
    df_data.multiply('Income|Household', "Income|Q"+str(i+1), "Income|Household|Qtemp"+str(i+1), append=True,  ignore_units=True)
    df_data.multiply('Income|Household|Qtemp'+str(i+1), 100, "Income|Household|Q"+str(i+1), append=True,  ignore_units=True)
    df_data.multiply('Expenditure|Household', "Consumption|Q"+str(i+1), "Consumption|Household|Qtemp"+str(i+1), append=True,  ignore_units=True)
    df_data.divide('Consumption|Household|Qtemp'+str(i+1), 100, "Consumption|Household|Q"+str(i+1), append=True,  ignore_units=True)

df_data.divide("Population", float(1000), "Population_for_perCap_computation", append=True,  ignore_units=True)

df_data.divide("GDP|MER", "Population_for_perCap_computation", "GDP/capita", append=True,  ignore_units=True)
df_data.divide("Expenditure|Household", "Population_for_perCap_computation", "Expenditure|Household /capita", append=True,  ignore_units=True)
df_data.divide("Consumption|Household|Q1", "Population_for_perCap_computation", "Consumption|Household|Q1 /capita", append=True,  ignore_units=True)

df_data.multiply("Consumption|Household|Q1 /capita", 4, "Consumption|Household|Q1 /capita true", append=True,  ignore_units=True)

############################################
# FILTER
############################################

df_nofilter = df_data.copy()

var2select = ['Inequality index|Gini', 'Inequality index|Consumption Gini', 'GDP|MER', 'Expenditure|Household', 'Emissions_Capita',"Emissions_GDP"]
var2select += ['Revenue|government|Tax|Carbon Tax', "Value Added|Labor Compensation|Gross","Value Added|Labor Compensation|Net", "GDP|MER"]
var2select += ['Consumption Elasticity']
for i in range(4):
    var2select += ['Income|Household|Q'+str(i+1), 'Consumption|Household|Q'+str(i+1)]
var2select += ['Price|Carbon','Emissions|CO2','Final Energy']
var2select += ['Revenue|government|Tax|Carbon Tax - breakeven']

var2select += [v for v in df_data.variable if "/capita" in v] 

# rename regions
reg_dict = {"BRA":"Brazil","CHN":"China", "IND":"India","Kenya":"Africa", "KEN":"Africa", "AFR":"Africa"}
df_data = df_data.rename(region = reg_dict)

#order_region = ['China', 'India', 'Africa', 'Brazil', 'Europe', 'USA']
order_region = ['India', 'China', 'Africa', 'Brazil', 'USA', 'Europe']

year2select = [yr for yr in df_data.year if yr <=2050 and yr>=2015]

model2select = [elt for elt in df_data.model if not 'IMACLIM' in elt]
model2select = [elt for elt in df_data.model if not 'IMACLIMx' in elt]

df_data = df_data.filter(region=order_region, year=year2select, model=model2select )
# export before filtering by variables
df_data.to_excel("../all_results.xlsx")
df_data = df_data.filter(variable=var2select)

# model and scenario rename
dict_sc_rename_gl = {'SUP_1p5C_Lab':'Labor Tax Cuts', 'SUP_1p5C_Lump':'Lump Sum Transfers'}
dict_scenario_rename = {s:s.replace('SUP_1p5C_Lab','Labor Tax Cuts').replace('SUP_1p5C_Lump','Lump Sum Transfers') for s in df_data.scenario}
dict_rename_model = {'E3ME v1.0':'E3ME', 'GEM-E3_V2023':'GEM-E3', 'JRC-GEM-E3 v2021':'JRC-GEM-E3', 'IMACLIM 2.0':'IMACLIM-R'}
df_data = df_data.rename( {"model":dict_rename_model, "scenario":dict_scenario_rename})

sc2select = [sc for sc in df_data.scenario if any(e in sc for e in ["SUP_NPi_Default",dict_sc_rename_gl["SUP_1p5C_Lab"], dict_sc_rename_gl["SUP_1p5C_Lump"]])]
sc_variant = [''] + list(set([sc.split('__')[1] for sc in sc2select if len(sc.split('__'))>1 and not 'sensit_first_decile' in sc.split('__')[1]]))
df_data = df_data.filter( scenario=sc2select)


####################
# set color map

#color_map_model = {k:'AR6-SSP'+str(i+1) for i,k in enumerate(df_data.model)}
color_map_model = {'E3ME v1.0':'AR6-SSP2', 'GEM-E3_V2023':'AR6-SSP4', 'IMACLIM 2.0':'AR6-SSP1', 'JRC-GEM-E3 v2021':'AR6-SSP3'}
color_map_scenario = {'AR6 database':'grey','Labor Tax Cuts':'AR6-SSP2', 'Lump Sum Transfers':'AR6-SSP4', 'Labor Tax Cuts__LaborShareImpact':'AR6-SSP2', 'Lump Sum Transfers__LaborShareImpact':'AR6-SSP4'}
marker_map_model = {'E3ME v1.0':'+', 'GEM-E3_V2023':'o', 'IMACLIM 2.0':'^', 'JRC-GEM-E3 v2021':'x'}
marker_map_scenario = {'Labor Tax Cuts':'o', 'Lump Sum Transfers':'+', 'Labor Tax Cuts__LaborShareImpact':'o', 'Lump Sum Transfers__LaborShareImpact':'+'}
# used dict rename to rename models
color_map_model = {dict_rename_model[k]:v for k,v in color_map_model.items()}
color_map_region = {r:['b','g','r','c','m','y'][i] for i,r in enumerate(order_region)}
marker_map_model = {dict_rename_model[k]:v for k,v in marker_map_model.items()}
pyam.run_control().update({"color": {"model": color_map_model}})
pyam.run_control().update({"color": {"scenario": color_map_scenario}})
pyam.run_control().update({"color": {"region": color_map_region, "model": color_map_model}})
pyam.run_control().update({"marker": {"model": marker_map_model}})
pyam.run_control().update({"marker": {"scenario": marker_map_scenario}})


##########################
# Normalise function
##########################

df_data_nonorm = df_data.copy()

##########################
##########################
# PLOTS
##########################
##########################

##########################
# FIGURE 2 & 3
##########################

low_chnindafr = -15.5
low_usaeur = -5.7
h_chnindafr = 2.2
h_usaeur = 1.4
dict_ymin = { 'Inequality index|Consumption Gini': {'China':low_chnindafr, 'India':low_chnindafr, 'Africa':low_chnindafr, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}}
dict_ymax = { 'Inequality index|Consumption Gini': {'China':h_chnindafr, 'India':h_chnindafr, 'Africa':h_chnindafr, 'USA':h_usaeur,'Europe':h_usaeur, 'Brazil':h_usaeur}}

low_chnindafr = -10.5
low_usaeur = -3.8
dict_ymin_figB = { 'Inequality index|Consumption Gini': {'China':low_chnindafr, 'India':low_chnindafr, 'Africa':low_chnindafr, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}}

low_chnindafr = -15.5
low_usaeur = -6
dict_ymin_figC = { 'Inequality index|Consumption Gini': {'China':low_chnindafr, 'India':low_chnindafr, 'Africa':low_chnindafr, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}}

low_chnindafr = 1
low_usaeur = 1.2
dict_ymax_figC = { 'Inequality index|Consumption Gini': {'China':low_chnindafr, 'India':low_chnindafr, 'Africa':low_chnindafr, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}}

# GINI
for sc_v in sc_variant:
    for var in ['Inequality index|Consumption Gini']:
        if sc_v != '':  
            sc_selection = [sc for sc in sc2select if sc_v in sc] + ['SUP_NPi_Default']
            sc_2_plot = [sc for sc in sc_selection if not 'SUP_NPi_Default' in sc]
        else:
            sc_selection = [sc for sc in sc2select if not any(e in sc for e in sc_variant[1:])] 
            sc_2_plot = [sc for sc in sc_selection if not 'SUP_NPi_Default' in sc]
        df2plot = df_data.filter( variable=var, scenario=sc_selection)
        df2plot = normalize_data(df2plot, sc_norm='SUP_NPi_Default', type_norm="ginipoint") 
        df2plot = df2plot.filter( scenario=sc_2_plot)
        # df_normbyx
        df_normbyx = df_data.filter( variable=var, scenario=sc_2_plot)
        df_normbyx = normalize_data_by_x(df_normbyx, sc_2_plot, [s for s in sc_2_plot if 'Lump' in s][0])
        df_normbyx = df_normbyx.filter( scenario=[s for s in sc_2_plot if dict_sc_rename_gl['SUP_1p5C_Lab'] in s])
        # save scenario variant data, or do the big plot if the first variant is passed
        if sc_v == '':
            df2plot_noLSimpact = df2plot.copy()
            df_normbyx_noLSimpact = df_normbyx.copy()
        elif sc_v == 'LaborShareImpact':
            #plot_one_figure_allvariant(df2plot_noLSimpact, df_normbyx_noLSimpact, df2plot, df_normbyx, var, "__all_variant", dict_ymin=dict_ymin, dict_ymax=dict_ymax)      
            figB_plot_one_figure_allvariant( df2plot, var, "",subtitle="2", dict_ymin=dict_ymin_figB, dict_ymax=dict_ymax, ytitle='Gini scenario - Gini baseline')      
            figB_plot_one_figure_allvariant( df2plot_noLSimpact, var, "",subtitle="3", dict_ymin=dict_ymin_figC, dict_ymax=dict_ymax_figC, ytitle='Gini scenario - Gini baseline')      

###########################################################""
# Figure A.1 & A.2
# Gini scenario - Gini baseline (% share of each effect)
###########################################################""

# prepare data for figure C
dict_sc_rename = {'Cons. + Inc.':r'Gini scenario - Gini baseline:  Cons. + Inc. Channels',
                  'Cons. percent': r'Consumption Channel only',
                  'Inc. percent': r'Income Channel only'}
sc_rename = {s:s.split('__')[0] for s in df2plot.scenario if not 'sensit_first_decile' in s}
df1 = df2plot.rename( {'variable':{'Inequality index|Consumption Gini':'Cons. + Inc.'}})
df1 = df1.rename( {'scenario':sc_rename})
df2 = df2plot_noLSimpact.rename( {'variable':{'Inequality index|Consumption Gini':'Cons.'}})
df2plot_figC = pyam.concat( [df1, df2])
df2plot_figC.subtract( 'Cons. + Inc.', 'Cons.', 'Inc.', append=True, ignore_units=True)
df2plot_figC.divide( 'Cons.', 'Cons. + Inc.', 'Cons. ratio', append=True, ignore_units=True)
df2plot_figC.multiply( 'Cons. ratio', 100, 'Cons. percent', append=True, ignore_units=True)
df2plot_figC.divide( 'Inc.', 'Cons. + Inc.', 'Inc. ratio', append=True, ignore_units=True)
df2plot_figC.multiply( 'Inc. ratio', 100, 'Inc. percent', append=True, ignore_units=True)

df2plot_figC = df2plot_figC.rename( {'variable':dict_sc_rename})
    
fig_C_plotting(df2plot_figC, year=2040, scenario="Lump Sum Transfers", figname="Figure_Annex.2")
fig_C_plotting(df2plot_figC, year=2040, scenario="Labor Tax Cuts", figname="Figure_Annex.3")
#fig_C_plotting(df2plot_figC, year=2040, scenario="Labor Tax Cut", figname="Figure_C_LTC_short.pdf", ymin_arg=-200, ymax_arg=200)

##########################
# FIGURE Annex A.6.1 & A.6.2 - Consumption bottom quartile
##########################

h_chnindafr = 20
h_usaeur = 20
dict_ymax = { 'Consumption|Household|Q1': {'China':h_chnindafr, 'India':h_chnindafr, 'Africa':h_chnindafr, 'USA':h_usaeur,'Europe':h_usaeur, 'Brazil':h_usaeur}}

low_chnindafr = -37
low_usaeur = -15
dict_ymin_figB = { 'Consumption|Household|Q1': {'China':low_chnindafr, 'India':low_chnindafr, 'Africa':low_chnindafr, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}}

low_chnindafr = -0.5
low_usaeur = -0.7
dict_ymin_figC = { 'Consumption|Household|Q1': {'China':low_chnindafr, 'India':low_chnindafr, 'Africa':low_chnindafr, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}}

low_chnindafr = 8.5
low_usaeur = 3
dict_ymax_figC = { 'Consumption|Household|Q1': {'China':low_chnindafr, 'India':low_chnindafr, 'Africa':low_chnindafr, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}}

mod_2_filter = [m for m in df_data.model if not 'JRC' in m]
mod_2_filter = [m for m in df_data.model]
# Quartile
for var in ['Consumption|Household|Q'+str(i+1) for i in range(4)]:
    for sc_v in sc_variant:
        if sc_v != '':
            sc_selection = [sc for sc in sc2select if sc_v in sc and not 'SUP_NPi_Default' in sc and not 'sensit_first_decile' in sc] + ['SUP_NPi_Default']
            sc_2_plot = [sc for sc in sc_selection if not 'SUP_NPi_Default' in sc]
        else:
            sc_selection = [sc for sc in sc2select if not any(e in sc for e in sc_variant[1:]) and not 'SUP_NPi_Default' in sc and not 'sensit_first_decile' in sc] + ['SUP_NPi_Default']
            sc_2_plot = [sc for sc in sc_selection if not 'SUP_NPi_Default' in sc]
        df2plot = df_data.filter( variable=var, scenario=sc_selection, model=mod_2_filter)
        df2plot = normalize_data(df2plot, sc_norm='SUP_NPi_Default', type_norm="percent")
        df2plot = df2plot.filter( scenario=sc_2_plot)
        # df_normbyx
        #df_normbyx = df_data.filter( variable=var, scenario=sc_2_plot, model=mod_2_filter)
        #df_normbyx = normalize_data_by_x(df_normbyx, sc_2_plot, [s for s in sc_2_plot if 'Lump' in s][0])
        #df_normbyx = df_normbyx.filter( scenario=[s for s in sc_2_plot if dict_sc_rename_gl['SUP_1p5C_Lab'] in s])
        # save scenario variant data, or do the big plot if the first variant is passed
        if sc_v == '':
            df2plot_noLSimpact = df2plot.copy()
            figB_plot_one_figure_allvariant(df2plot_noLSimpact, var, "",subtitle="Annex_6.2."+var.replace('|',''), dict_ymin=dict_ymin_figB, dict_ymax=dict_ymax, ytitle=r"$\frac{Cons. scenario - Cons. baseline}{Cons. baseline}$ (\%)")
            #figB_plot_one_figure_allvariant(df2plot, var, "",subtitle="Annex_6.2."+var.replace('|',''))
        elif sc_v == 'LaborShareImpact':
            figB_plot_one_figure_allvariant( df2plot, var, "",subtitle="Annex_6.1."+var.replace('|',''), dict_ymin=dict_ymin_figB, dict_ymax=dict_ymax, ytitle=r"$\frac{Cons. scenario - Cons. baseline}{Cons. baseline}$ (\%)")

##########################
# FIGURE Annex A.19.1.x & A.19.2.x - Consumption bottom quartile
##########################

for var in ['Consumption|Household|Q1']:
    var_t = var.split('|')[0]
    for sc_v in ['Labor Tax Cuts','Lump Sum Transfers']:
        sc_t  =sc_v.replace(' ','_')
        sc_selection = [sc for sc in sc2select if sc_v in sc and '__LaborShareImpact' in sc and not '1.02' in sc and not '0.98' in sc] + ['SUP_NPi_Default']
        sc_2_plot = [sc for sc in sc_selection if not 'SUP_NPi_Default' in sc]
        df2plot = df_data.filter( variable=var, scenario=sc_selection)
        df2plot = normalize_data(df2plot, sc_norm='SUP_NPi_Default', type_norm="percent")
        df2plot = df2plot.filter( scenario=sc_2_plot)
        figB_plot_one_figure_allvariant_quartile(df2plot, var, "",subtitle="Annex_19."+var_t+'.'+sc_t)

###########################################################""
# Figure 4
# Pure income effect
###########################################################

sc_selection = [sc for sc in sc2select if not 'SUP_NPi_Default' in sc]
sc_2_plot = [sc for sc in sc_selection if '__LaborShareImpact' in sc and not 'sensit_first_decile' in sc]
for var in ['Inequality index|Consumption Gini']:
    df2plot = df_data.filter( variable=var, scenario=sc_selection)
    #df1 = normalize_data_by_x(df2plot, [s for s in sc_selection if 'SUP_1p5C_Lab' in s], 'SUP_1p5C_Lab')
    #df2 = normalize_data_by_x(df2plot, [s for s in sc_selection if 'SUP_1p5C_Lump' in s], 'SUP_1p5C_Lump')
    df1 = normalize_data(df2plot.filter(scenario= [s for s in sc_selection if dict_sc_rename_gl['SUP_1p5C_Lab'] in s]), dict_sc_rename_gl['SUP_1p5C_Lab'], type_norm="ginipoint")
    df2 = normalize_data(df2plot.filter(scenario= [s for s in sc_selection if dict_sc_rename_gl['SUP_1p5C_Lump'] in s]), dict_sc_rename_gl['SUP_1p5C_Lump'], type_norm="ginipoint")
    df2plot = pyam.concat( [df1, df2])
    df2plot = df2plot.filter(scenario = sc_2_plot)
    df2plot_norm = df2plot.copy()
    df_normbyx_norm = normalize_data(df2plot, sc_norm='SUP_1p5C_Lab__LaborShareImpact'.replace( 'SUP_1p5C_Lab', dict_sc_rename_gl['SUP_1p5C_Lab']), type_norm="differences")
    df_normbyx_norm = df_normbyx_norm.filter(scenario='SUP_1p5C_Lump__LaborShareImpact'.replace( 'SUP_1p5C_Lump', dict_sc_rename_gl['SUP_1p5C_Lump']))
    #plot_one_figure(df2plot, df_normbyx_norm, var, '_norm')

df2plot_norm_wLS = df2plot_norm.filter(scenario='Labor Tax Cuts__LaborShareImpact')
df2plot_norm_woLS = df2plot_norm.filter(scenario='Lump Sum Transfers__LaborShareImpact')

#plot_diff(df_normbyx, df_normbyx_noLSimpact, df2plot_norm_wLS, 'Inequality index|Consumption Gini', "__diff")

def compute_pyam_func( df, x_biais):
    df = df.timeseries()
    df = df.apply( lambda x: np.log(x + x_biais))
    return pyam.IamDataFrame(df)

y1min = -1.6
x_biais = 1-y1min
#figC_plot_diff( df2plot_norm_wLS , df2plot_norm_woLS, 'Inequality index|Consumption Gini', "Figure_3.2", y1min=y1min)
#figC_plot_diff_log( compute_pyam_func(df2plot_norm_wLS, x_biais) , compute_pyam_func(df2plot_norm_woLS, x_biais), 'Inequality index|Consumption Gini', "Figure_3.2_log", y1min=y1min, xbiais=x_biais)
figC_plot_diff_nonlog( df2plot_norm_wLS, df2plot_norm_woLS, 'Inequality index|Consumption Gini', "Figure_3.2_log", y1min=y1min, xbiais=x_biais)
figC_plot_diff_log( df2plot_norm_wLS, df2plot_norm_woLS, 'Inequality index|Consumption Gini', "Figure_3.2_log", y1min=y1min, xbiais=x_biais)

###########################################################""
# Figure 1 - Plot equité efficacité tradeoff
#   + A.1 (consumption channel only)
#   + A.18.x (income by quartile)
###########################################################

sc_selection = ['SUP_1p5C_Lab__LaborShareImpact'.replace( 'SUP_1p5C_Lab', dict_sc_rename_gl['SUP_1p5C_Lab']), 'SUP_1p5C_Lump__LaborShareImpact'.replace( 'SUP_1p5C_Lump', dict_sc_rename_gl['SUP_1p5C_Lump']),'SUP_NPi_Default'] # including normalisation
sc_2_plot = [sc for sc in sc_selection if not 'SUP_NPi_Default' in sc]
#region_selection = ['Europe', 'IND']
year_select = 2045

var_g = 'Inequality index|Consumption Gini'
var_c = 'Expenditure|Household'

def df2plot_fig1( df_data, sc_selection, year_select, var_g, var_c, sc_2_plot):
    df2plot_g = df_data.filter( variable=var_g, scenario=sc_selection)
    df2plot_g = normalize_data(df2plot_g, sc_norm='SUP_NPi_Default', type_norm="ginipoint")
    df2plot_g = df2plot_g.filter( scenario=sc_2_plot)
#df2plot_g *= -1 # Plot losses in Gini
    df2plot_g = df2plot_g.multiply(var_g, -1, "-"+var_g, ignore_units=True)

    df2plot_c = df_data.filter( variable=var_c, scenario=sc_selection)
    df2plot_c = normalize_data(df2plot_c, sc_norm='SUP_NPi_Default', type_norm="percent")
    df2plot_c = df2plot_c.filter( scenario=sc_2_plot)

    df2plot = pyam.concat( [df2plot_g, df2plot_c])
    return df2plot

df2plot = df2plot_fig1( df_data, sc_selection, year_select, var_g, var_c, sc_2_plot)

df2plot.to_csv('csv_Figures_1.csv')

############ plot all

#rename_dict = {'variable': {"-Inequality index|Consumption Gini":r"Gini Baseline - Gini Scenario($\Delta$)", r"Expenditure|Household":r"$\frac{Cons. scenario - Cons. baseline}{Cons. baseline}$ (\%)"}}
rename_dict = {'variable': {"-Inequality index|Consumption Gini":r"Gini Baseline - Gini Scenario", r"Expenditure|Household":r"$\frac{Cons. scenario - Cons. baseline}{Cons. baseline}$ (\%)"}}

low_chnindbra = 3
low_usaeur = 1.7
dict_ymax_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}
low_chnindbra = -55
low_usaeur = -15
dict_ymin_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}


# nuage with subplots
figA_plot_all_nuage_subplot(df2plot, "-Inequality index|Consumption Gini", "Expenditure|Household", "Figure_Annex.1", rename_dict=rename_dict, mode="color_model", ymax=dict_ymax_fig1, ymin=dict_ymin_fig1)
figA_plot_all_nuage_subplot(df2plot,  "-Inequality index|Consumption Gini", "Expenditure|Household","Figure_1", rename_dict=rename_dict, mode="color_scenario", ymax=dict_ymax_fig1, ymin=dict_ymin_fig1)

low_chnindbra = 23
low_usaeur = 23
dict_ymax_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}
low_chnindbra = -44
low_usaeur = -18
dict_ymin_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}

dict_ymin={}
dict_ymax={}
for i in range(3):
    dict_ymin[i+1]=dict_ymin_fig1.copy()
    dict_ymax[i+1]=dict_ymax_fig1.copy()

low_chnindbra = 5
low_usaeur = 2
dict_ymax_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}
low_chnindbra = -61
low_usaeur = -18
dict_ymin_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}

dict_ymin[4]=dict_ymin_fig1.copy()
dict_ymax[4]=dict_ymax_fig1.copy()



# By quartile- A.18.x (income by quartile) 
sc_selection = ['SUP_1p5C_Lab__LaborShareImpact'.replace( 'SUP_1p5C_Lab', dict_sc_rename_gl['SUP_1p5C_Lab']), 'SUP_1p5C_Lump__LaborShareImpact'.replace( 'SUP_1p5C_Lump', dict_sc_rename_gl['SUP_1p5C_Lump']),'SUP_NPi_Default'] # including normalisation
sc_2_plot = [sc for sc in sc_selection if not 'SUP_NPi_Default' in sc]
var_g = 'Inequality index|Consumption Gini'
for i in range(4):
    var_c = "Consumption|Household|Q"+str(i+1)
    df2plot = df2plot_fig1( df_data, sc_selection, year_select, var_g, var_c, sc_2_plot)   
    rename_dict = {'variable': {"-Inequality index|Consumption Gini":r"Gini Baseline - Gini Scenario", var_c:r"$\frac{Cons. scenario - Cons. baseline}{Cons. baseline}$ (\%)"}}
    figA_plot_all_nuage_subplot(df2plot, "-"+var_g, var_c, "Figure_Annex_18.Q"+str(i+1), rename_dict=rename_dict, mode="color_scenario", do_zoom=False, ymax=dict_ymax[i+1], ymin=dict_ymin[i+1] )
    figA_plot_all_nuage_subplot(df2plot, "-"+var_g, var_c, "Figure_Annex_18.Q"+str(i+1)+"_2035", rename_dict=rename_dict, mode="color_scenario", do_zoom=False, year2filter=[2035], ymax=dict_ymax[i+1], ymin=dict_ymin[i+1])

# By quartile- A.20.x (income by quartile) - No labor share impact scenarios
sc_selection = ['SUP_1p5C_Lab'.replace( 'SUP_1p5C_Lab', dict_sc_rename_gl['SUP_1p5C_Lab']), 'SUP_1p5C_Lump'.replace( 'SUP_1p5C_Lump', dict_sc_rename_gl['SUP_1p5C_Lump']),'SUP_NPi_Default'] # including normalisation
sc_2_plot = [sc for sc in sc_selection if not 'SUP_NPi_Default' in sc]
var_g = 'Inequality index|Consumption Gini'
for i in range(4):
    var_c = "Consumption|Household|Q"+str(i+1)
    df2plot = df2plot_fig1( df_data, sc_selection, year_select, var_g, var_c, sc_2_plot)
    rename_dict = {'variable': {"-Inequality index|Consumption Gini":r"Gini Baseline - Gini Scenario", var_c:r"$\frac{Cons. scenario - Cons. baseline}{Cons. baseline}$ (\%)"}}
    figA_plot_all_nuage_subplot(df2plot, "-"+var_g, var_c, "Figure_Annex_20.Q"+str(i+1), rename_dict=rename_dict, mode="color_scenario", do_zoom=False, ymax=dict_ymax[i+1], ymin=dict_ymin[i+1] )
    figA_plot_all_nuage_subplot(df2plot, "-"+var_g, var_c, "Figure_Annex_20.Q"+str(i+1)+"_2035", rename_dict=rename_dict, mode="color_scenario", do_zoom=False, year2filter=[2035], ymax=dict_ymax[i+1], ymin=dict_ymin[i+1])


##########################################
# Figure Emissions_Capitapercent.pdf
# + Emissions_Capitadifferences.pdf
#/ Consumption losses VERSUS Emissions per capita
##########################################


scenario_selec='Labor Tax Cuts'

for sc_v in sc_variant[0:1]:
    if sc_v != '':
        sc_selection = [sc for sc in sc2select if sc_v in sc] + ['SUP_NPi_Default']
        sc_2_plot = [sc for sc in sc_selection if not 'SUP_NPi_Default' in sc]
    else:
        sc_selection = [sc for sc in sc2select if not any(e in sc for e in sc_variant[1:])]
        sc_2_plot = [sc for sc in sc_selection if not 'SUP_NPi_Default' in sc]
    var = 'Expenditure|Household'
    df2plot = df_data.filter( variable=var, scenario=sc_selection)
    df2plot = normalize_data(df2plot, sc_norm='SUP_NPi_Default', type_norm="percent")
    df2plot = df2plot.filter( scenario=scenario_selec)
    var = 'Emissions_Capita'
    df2plot_y = df_data.filter( variable=var, scenario=sc_selection)
    df2plot_y = normalize_data(df2plot_y, sc_norm='SUP_NPi_Default', type_norm="percent")
    df2plot_y = df2plot_y.filter( scenario=scenario_selec)
    rename_dict = {"Emissions_Capita":r"CO2 Emissions per Capita (\%)", "Expenditure|Household":r"Consumption losses (\%)"}
    plot_losses_emi(df2plot, df2plot_y, var, "percent", rename_dict=rename_dict)

    df2plot_y = df_data.filter( variable=var, scenario=sc_selection)
    df2plot_y = normalize_data(df2plot_y, sc_norm='SUP_NPi_Default', type_norm="differences")
    df2plot_y = df2plot_y.filter( scenario=scenario_selec)
    rename_dict = {"Emissions_Capita":r"CO2 Emissions per Capita ($\Delta$)", "Expenditure|Household":r"Consumption losses (\%)"}
    plot_losses_emi(df2plot, df2plot_y, var, "differences", rename_dict=rename_dict)

def fix_Imaclim_unit(df):
    df = df.timeseries()
    df.loc[("IMACLIM-R", slice(None), slice(None), "GDP|MER"), :] *= 1000
    df = pyam.IamDataFrame(df)
    return df

##########################################
# Figure A.4.2 : carbon revenus on GDP
# Figure A.4 : carbon revenues

low_chnindbra = 3500
low_usaeur = 2700
dict_ymax_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':355}
low_chnindbra = -50
low_usaeur = -50
dict_ymin_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':-50}

# carbon revenues
var = 'Revenue|government|Tax|Carbon Tax'
sc_selection = ['Labor Tax Cuts', 'Lump Sum Transfers']
df2plot = df_data.filter( variable=var, scenario=sc_selection)
fig_annex_simple(df2plot, "scenario", "Figure_Annex_4", dict_ymin=dict_ymin_fig1, dict_ymax=dict_ymax_fig1)

low_chnindbra = 27.5
low_usaeur = 12
dict_ymax_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}
low_chnindbra = -1
low_usaeur = -1
dict_ymin_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}

# carbon revenues on GDP
df = df_data.filter(variable=['Revenue|government|Tax|Carbon Tax',"GDP|MER"])
df = df.divide( 'Revenue|government|Tax|Carbon Tax', "GDP|MER", "CO2 revenue / GDP", ignore_units=True)
df = df.multiply( "CO2 revenue / GDP", 100,  "CO2 revenue / GDP %", ignore_units=True)
var = "CO2 revenue / GDP %"
df2plot = df.filter( variable=var, scenario=sc_selection)
fig_annex_simple(df2plot, "scenario", "Figure_Annex_4.2", dict_ymin=dict_ymin_fig1, dict_ymax=dict_ymax_fig1, title_fig=r"CO2 revenues / GDP ($\%$)")


##########################################
# Figure A.8.1 : carbon intensity : emissions per capita
# Figure A.8.2 : carbon intensity : emissions / GDP

low_chnindbra = 8.5
low_usaeur = 16.3
dict_ymax_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}
low_chnindbra = 0
low_usaeur = -2.5
dict_ymin_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}

# carbon emissions per capita
var = "Emissions_Capita"
df2plot = df_data.filter( variable=var, scenario=sc_selection)
fig_annex_simple(df2plot, "scenario", "Figure_Annex_8.1__emissions_per_capita", dict_ymin=dict_ymin_fig1, dict_ymax=dict_ymax_fig1, title_fig=r"CO2 emissions / GDP ($\%$)")


low_chnindbra = 0.85
low_usaeur = 0.5
dict_ymax_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}
low_chnindbra = 0
low_usaeur = -0.2
dict_ymin_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}

# carbon emissions on GDP
var = "Emissions_GDP"
df2plot = df_data.filter( variable=var, scenario=sc_selection)
fig_annex_simple(df2plot, "scenario", "Figure_Annex_8.2__emissions_on_GDP", dict_ymin=dict_ymin_fig1, dict_ymax=dict_ymax_fig1, title_fig=r"CO2 emissions / GDP ($\%$)")

##########################################
# Figure A.9 : Consumtpion elasticity

low_chnindbra = 1.5
low_usaeur = 1.2
dict_ymax_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}
low_chnindbra = 0.970
low_usaeur = 0.7
dict_ymin_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}

# consumption elasticity
var = "Consumption Elasticity"
df2plot = df_data.filter( variable=var, scenario=sc_selection)
fig_annex_simple(df2plot, "scenario", "Figure_Annex_9__consumption_elasticity", dict_ymin=dict_ymin_fig1, dict_ymax=dict_ymax_fig1, title_fig=r"CO2 emissions / GDP ($\%$)")
fig_annex_simple(df2plot, "scenario", "Figure_Annex_9__consumption_elasticity_no_alignment", title_fig=r"CO2 emissions / GDP ($\%$)")

##########################################
# Figure A.16 : (Gini) Breakeven carbon revenues

# Revenue|government|Tax|Carbon Tax - breakeven
var = ['Revenue|government|Tax|Carbon Tax - breakeven','Revenue|government|Tax|Carbon Tax']
df2plot_1 = df_data.filter( variable='Revenue|government|Tax|Carbon Tax', scenario='Lump Sum Transfers')
df2plot_2 = df_data.filter( variable='Revenue|government|Tax|Carbon Tax - breakeven', scenario='Lump Sum Transfers')
df2plot_2 = df2plot_2.rename( {'scenario': {'Lump Sum Transfers':'Lump Sum Transfers - breakeven'}})

df2plot = pyam.concat([df2plot_1,df2plot_2])

#fig_annex_simple(df2plot, "scenario", "Figure_Annex_9__consumption_elasticity", dict_ymin=dict_ymin_fig1, dict_ymax=dict_ymax_fig1, title_fig=r"CO2 emissions / GDP ($\%$)")
fig_annex_simple(df2plot, "scenario", "Figure_Annex_16__breakeven_co2_revenues", title_fig=r"CO2 emissions / GDP ($\%$)")


##########################################
# Figure A.17 : (Cons. Losses) Breakeven carbon revenues

def assign_baseline( df, sc, sc_base, var):
    df_out = df.filter( variable=var, scenario=sc_base)
    df_out = df_out.rename( {"variable":{var:var + ' - baseline'}})
    df_out = df_out.rename( {"scenario":{sc_base:sc}})
    return df_out

var = 'Expenditure|Household'
df_cons_baseline = pyam.concat( [ assign_baseline( df_data, sc, "SUP_NPi_Default", var) for sc in df_data.scenario if not 'SUP_NPi_Default' in sc])
df = pyam.concat( [ df_cons_baseline, df_data.filter(variable=[var,'Revenue|government|Tax|Carbon Tax'])])

df.subtract( var+" - baseline", var, 'Revenue|government|Tax|Carbon Tax - breakeven', append=True, ignore_units=True)

df2plot_1 = df.filter( variable='Revenue|government|Tax|Carbon Tax', scenario='Lump Sum Transfers')
df2plot_2 = df.filter( variable='Revenue|government|Tax|Carbon Tax - breakeven', scenario='Lump Sum Transfers')
df2plot_2 = df2plot_2.rename( {'scenario': {'Lump Sum Transfers':'Lump Sum Transfers - breakeven'}})

df2plot = pyam.concat([df2plot_1,df2plot_2])

#fig_annex_simple(df2plot, "scenario", "Figure_Annex_9__consumption_elasticity", dict_ymin=dict_ymin_fig1, dict_ymax=dict_ymax_fig1, title_fig=r"CO2 emissions / GDP ($\%$)")
fig_annex_simple(df2plot, "scenario", "Figure_Annex_17__breakeven_co2_revenues__for_cons", title_fig=r"CO2 emissions / GDP ($\%$)")


##########################################
# Figure A.10 : Price Carbon

# consumption elasticity
df2plot = df_data.filter( variable=["Price|Carbon","GDP|MER"], scenario=sc_selection, region=[r for r in df_data.region if r !='Africa'])
df2plot = df2plot.aggregate_region("Price|Carbon", weight="GDP|MER")
fig_annex_simple_log(df2plot, "scenario", "Figure_Annex_10__carbon_price_log", dict_ymin={'World':1}, title_fig=r"CO2 emissions / GDP ($\%$)", list_year = [2025,2030,2035,2040,2045,2050])

##########################################
# Figure A.11 : Share of carbon price in carbon revenues evolution

# consumption elasticity
df = df_data.filter( variable=["Price|Carbon","Emissions|CO2"], scenario=sc_selection, region=[r for r in df_data.region if r !='Africa'])

df.multiply("Price|Carbon","Emissions|CO2","CO2 revenus", append=True, ignore_units=True)

df_previous = df.timeseries()
dict_col_rename = {k:k+5 for k in df_previous.columns}
df_previous = df_previous.rename( dict_col_rename, axis=1)
df_previous = df_previous.reset_index()
df_previous['variable'] += '_prev'

df = pyam.concat( [df, pyam.IamDataFrame(df_previous)])

for v in [v for v in df.variable if not '_prev' in v]:
    df.subtract( v, v+"_prev", "delta_" + v, append=True, ignore_units=True)

df.multiply( "Emissions|CO2", "delta_" +"Price|Carbon", "share_Price_Carbon_numerator", append=True, ignore_units=True)

df.multiply( "Price|Carbon", "delta_" +"Emissions|CO2", "share_Emission_numerator", append=True, ignore_units=True)
# take the absolute
df.multiply( "share_Emission_numerator", -1, "share_Emission_numerator - abs", append=True, ignore_units=True)
df.add( "share_Price_Carbon_numerator", "share_Emission_numerator - abs", "share denominator", append=True, ignore_units=True)

df.divide(  "share_Price_Carbon_numerator", "share denominator", "share_Price_Carbon", append=True, ignore_units=True)
df.multiply(  "share_Price_Carbon", 100, "share_Price_Carbon_percent", append=True, ignore_units=True)

df.divide(  "share_Emission_numerator - abs", "share denominator", "share_Emission", append=True, ignore_units=True)
df.multiply(  "share_Emission", 100, "share_Emission_percent", append=True, ignore_units=True)


df2plot = df.filter( variable = "share_Price_Carbon_percent")
fig_annex_simple(df2plot, "scenario", "Figure_Annex_11.1__carbon_price_contribution", title_fig=r"CO2 emissions / GDP ($\%$)", list_year=[2035,2040,2045])

df2plot = df.filter( variable = "share_Emission_percent")
fig_annex_simple(df2plot, "scenario", "Figure_Annex_11.2__emission_contribution", title_fig=r"CO2 emissions / GDP ($\%$)", list_year=[2035,2040,2045])


##########################################
# Figure A.5: Labour Share variation - point variations

results_folder = "outputs/all/"
list_file = [elt for elt in os.listdir(results_folder) if ".xlsx" in elt]
df_data_all = pyam.concat( [pyam.IamDataFrame(results_folder+x) for x in list_file])

# rename regions
reg_dict = {"BRA":"Brazil","CHN":"China", "IND":"India","Kenya":"Africa", "KEN":"Africa", "AFR":"Africa"}

df_data_all = df_data_all.rename( {"model":dict_rename_model, "scenario":dict_scenario_rename})
df_data_all = df_data_all.rename(region = reg_dict)

df_lab_compensatin_gross = df_data_all.filter(variable=["Value Added|Labor Compensation|Gross", "Value Added|Labor Compensation|Net"])
# compute tax rate
df_labour_tax_rate_base = df_lab_compensatin_gross.divide( "Value Added|Labor Compensation|Gross", "Value Added|Labor Compensation|Net", "labour_tax_rate_base", ignore_units=True).rename(unit={"unknown": ""})
df_labour_tax_rate = df_labour_tax_rate_base.copy()
# apply baseline tax rate for each scenario
df_labour_tax_rate_base = pyam.concat( [ df_labour_tax_rate_base.filter(scenario='SUP_NPi_Default').rename(scenario={"SUP_NPi_Default": sc}) for sc in df_labour_tax_rate_base.scenario])
#df_labour_tax_rate_base = df_labour_tax_rate_base.add("labour_tax_rate_base", 1, "labour_tax_rate_base factor to apply")
df_labour_share = pyam.concat( [df_data_all.filter(variable=["Value Added|Labor Compensation|Net","GDP|MER"]), df_labour_tax_rate_base] ).rename(unit={"": "yr","billion US$2010/yr":"billion/yr"})

df_labour_share = fix_Imaclim_unit(df_labour_share)

df_labour_share.multiply( "Value Added|Labor Compensation|Net", "labour_tax_rate_base", "Labour Compensation-baseline tax", ignore_units=True, append=True)
df_labour_share = df_labour_share.rename( {"unit":{"unknown":""}})

df_labour_share = df_labour_share.divide( "Labour Compensation-baseline tax", "GDP|MER", "Labour share", ignore_units=True)
#df_labour_share = df_labour_share.multiply( "Labour share", 100, "Labour share * 100", ignore_units=True)

df_labour_share = normalize_data(df_labour_share, sc_norm='SUP_NPi_Default', type_norm="ginipoint")

sc_selection = ['Labor Tax Cuts', 'Lump Sum Transfers']
var='Labour share'
df2plot = df_labour_share.filter( variable=var, scenario=sc_selection)

low_chnindbra = 3.5
low_usaeur = 5
dict_ymax_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}
low_chnindbra = -27
low_usaeur = -10
dict_ymin_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}

fig_annex_simple(df2plot, "scenario", "Figure_Annex_5", dict_ymin=dict_ymin_fig1, dict_ymax=dict_ymax_fig1)


##########################################
#Figure A.12 - World GDP PPP - NPi
#Figure A.13 - World GDP MER - NPi
#Figure A.14 - World Population- NPi

dict_var_n_num = {'GDP|PPP':12,'GDP|MER':13,'Population':14}
dict_var_titles = {'GDP|PPP':'GDP PPP (billion US\$2010/yr)','GDP|MER':'GDP MER (billion US\$2010/yr)','Population':'Population (million)'}
dict_unit_rename = {'billion US$2010/yr':'billion US\$2010/yr'}
for var in dict_var_n_num.keys():
    df2plot = df_data_all.filter(variable=var, region='World', scenario='SUP_NPi_Default', year=[y for y in df_data_all.year if y<=2050])
    df2plot = df2plot.rename( {"unit":dict_unit_rename})
    df2plot.plot(color="model", title=dict_var_titles[var])
    plt.savefig(output_fig + "Figure_Annex_"+str(dict_var_n_num[var])+"__"+var.replace('|','_')+".pdf", dpi=dpi, bbox_inches='tight')

##########################################
# Figure A.7 - wage real

# real wage IMACLIM

low_chnindbra = 0
low_usaeur = 0
dict_ymax_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}
low_chnindbra = -75
low_usaeur = -30
dict_ymin_fig1 = {'China':low_chnindbra, 'India':low_chnindbra, 'USA':low_usaeur,'Europe':low_usaeur, 'Brazil':low_usaeur}

# carbon revenues
var = 'Wage|Real [Average]'
sc_selection = ['Labor Tax Cuts', 'Lump Sum Transfers']
df2plot = normalize_data(df_data_all.filter( variable=var, scenario= ['Labor Tax Cuts', 'Lump Sum Transfers', 'SUP_NPi_Default']), sc_norm='SUP_NPi_Default', type_norm="percent")
df2plot = df2plot.rename( region = {'EUR':'Europe'})

fig_annex_simple(df2plot.filter(scenario=sc_selection), "scenario", "Figure_Annex_7", dict_ymin=dict_ymin_fig1, dict_ymax=dict_ymax_fig1)

##########################################
# Initial labour share - consol print

df_lab_compensatin_gross = df_data_all.filter(variable=["Value Added|Labor Compensation|Gross", "Value Added|Labor Compensation|Net"])
# compute tax rate
df_labour_tax_rate_base = df_lab_compensatin_gross.divide( "Value Added|Labor Compensation|Gross", "Value Added|Labor Compensation|Net", "labour_tax_rate_base", ignore_units=True).rename(unit={"unknown": ""})
# apply baseline tax rate for each scenario
df_labour_tax_rate_base = pyam.concat( [ df_labour_tax_rate_base.filter(scenario='SUP_NPi_Default').rename(scenario={"SUP_NPi_Default": sc}) for sc in df_labour_tax_rate_base.scenario])
#df_labour_tax_rate_base = df_labour_tax_rate_base.add("labour_tax_rate_base", 1, "labour_tax_rate_base factor to apply")
df_labour_share = pyam.concat( [df_data_all.filter(variable=["Value Added|Labor Compensation|Net","GDP|MER"]), df_labour_tax_rate_base] ).rename(unit={"": "yr","billion US$2010/yr":"billion/yr"})

df_labour_share = fix_Imaclim_unit(df_labour_share)

df_labour_share.multiply( "Value Added|Labor Compensation|Net", "labour_tax_rate_base", "Labour Compensation-baseline tax", ignore_units=True, append=True)
df_labour_share = df_labour_share.rename( {"unit":{"unknown":""}})

df_labour_share = df_labour_share.divide( "Labour Compensation-baseline tax", "GDP|MER", "Labour share", ignore_units=True)
#df_labour_share = df_labour_share.multiply( "Labour share", 100, "Labour share * 100", ignore_units=True)

sc_selection = ['Labor Tax Cuts', 'Lump Sum Transfers']

dd = df_labour_share.filter( scenario="SUP_NPi_Default", variable="Labour share", region = ['China', 'India', 'USA', 'Europe', 'Brazil'], year=2020)

for reg in dd.region:
    for mod in dd.model:
        val = np.around(dd.filter(region=reg, model=mod).timeseries().values[0][0]*100, 2)
        print( "{:<10}".format(reg), "{:<15}".format(mod), val)

# Open a file to write the LaTeX code
with open(output_fig+'Table_Annex_initial_labor_share.tex', 'w') as f:
    # Write the LaTeX preamble and begin the document
    f.write("\\documentclass{article}\n")
    f.write("\\begin{document}\n")

    # Begin the table environment
    f.write("\\begin{tabular}{|l|l|l|}\n")
    f.write("\\hline\n")
    f.write("Region & Model & Value \\\\ \n")
    f.write("\\hline\n")

    # Loop through the data and write each row
    for reg in dd.region:
        for mod in dd.model:
            val = np.around(dd.filter(region=reg, model=mod).timeseries().values[0][0]*100, 2)
            f.write(f"{reg} & {mod} & {val} \\\\ \n")
            f.write("\\hline\n")

    # End the table environment
    f.write("\\end{tabular}\n")

    # End the document
    f.write("\\end{document}\n")

print("LaTeX table has been written to output_table.tex")

##########################################
# Carbon budget
##########################################
df_ar6_main = pyam.IamDataFrame( "/data/public_data/IIASA_scenario_explorer_public/download/ar6-public__world.csv")

df = df_data_all.filter( region='World', variable=["Emissions|CO2"], scenario=sc_selection)
df.filter(year=2050).timeseries()

def compute_cum(df, yr1, yr2, name, step):
    df_t = df.timeseries()
    df_t['B_'+name+'_1'] = df.filter( year=[y for y in df.year if y>=yr1 and y<=yr2-step]).timeseries().values.sum(axis=1) * step
    df_t['B_'+name+'_2'] = df.filter( year=[y for y in df.year if y>=yr1+step and y<=yr2]).timeseries().values.sum(axis=1) * step
    #df_t['B_'+name] = df_t['B_'+name+'_1']  #df_t['B_'+name+'_1'] /2 + df_t['B_'+name+'_2'] / 2
    df_t['B_'+name] = df_t['B_'+name+'_1'] /2 + df_t['B_'+name+'_2'] / 2
    return pyam.IamDataFrame(df_t)

df_budget = compute_cum(df, 2020, 2050, '50', 5)

# Open a file to write the LaTeX code
with open(output_fig+'Table_Annex_20-50_carbon budget.tex', 'w') as f:
    # Write the LaTeX preamble and begin the document
    f.write("\\documentclass{article}\n")
    f.write("\\begin{document}\n")

    # Begin the table environment
    f.write("\\begin{tabular}{|l|l|l|}\n")
    f.write("\\hline\n")
    f.write("Scenario & Model & 2020-2050 carbon budget (GtCO2) \\\\ \n")
    f.write("\\hline\n")

    # Loop through the data and write each row
    for sc in df_budget.scenario:
        for mod in df_budget.model:
            val = np.around(df_budget.filter(scenario=sc, model=mod).timeseries().reset_index()['B_50'].values[0] / 1e3, 3)
            f.write(f"{sc} & {mod} & {val} \\\\ \n")
            f.write("\\hline\n")

    # End the table environment
    f.write("\\end{tabular}\n")

    # End the document
    f.write("\\end{document}\n")



df_budget = compute_cum(df_budget, 2020, 2100, '100', 5)

range_error = 0.0
mmax = np.max(df_budget.timeseries().reset_index()['B_50']) * (1 + range_error)
mmin = np.min(df_budget.timeseries().reset_index()['B_50']) * (1 - range_error)

df_ar6 = df_ar6_main.filter( variable='Emissions|CO2', year=[y for y in range(2020, 2100+1, 10)])
df_ar6 = compute_cum(df_ar6, 2020, 2050, '50', 10)
df_ar6 = compute_cum(df_ar6, 2020, 2100, '100', 10)

df_ar6 = df_ar6.timeseries().reset_index()

df_ar6 = df_ar6[df_ar6[2100] >=-2000]
ar6_same = df_ar6[ (df_ar6['B_50'] >= mmin) & (df_ar6['B_50'] <= mmax) ]['B_100']
np.mean(ar6_same)
np.std(ar6_same)

#0.05 -4 722
#0.05 -2 736
#0.01 -2 744

####################
#  Now reverting

budget_target = 600
range_error = 0.10
net_level = -2000

df_ar6 = df_ar6_main.filter( variable='Emissions|CO2', year=[y for y in range(2020, 2100+1, 10)])
df_ar6 = compute_cum(df_ar6, 2020, 2050, '50', 10)
df_ar6 = compute_cum(df_ar6, 2020, 2100, '100', 10)

df_ar6 = df_ar6.timeseries().reset_index()
df_ar6 = df_ar6[df_ar6[2100] >=net_level]

# historical 2020 emissions
hist_20202 = 38.57 * 1e3
df_ar6 = df_ar6[ (df_ar6[2020] >= hist_20202*0.95) & (df_ar6[2020] <= hist_20202*1.05)]

ar6_same = df_ar6[ (df_ar6['B_50'] >= budget_target * 1e3 * (1-range_error)) & (df_ar6['B_50'] <=  budget_target* 1e3 * (1+range_error)) ]

print( np.max(ar6_same['B_50']) / 1e3, np.min(ar6_same['B_50']) / 1e3, np.mean(ar6_same['B_50']) / 1e3)

##################
# plot range of AR6 scenarios, with ours scenarios

df_budget = df_budget.timeseries().reset_index()
df2plot_my_scenarios = pyam.IamDataFrame( df_budget.drop([c for c in df_budget.columns if 'B_' in str(c)], axis=1))
df2plot_my_scenarios = df2plot_my_scenarios.filter( year=[y for y in df2plot_my_scenarios.year if y<=2050 and y>=2020])

ar6_same.loc[:,'scenario'] = 'AR6 database'
# trick to avoid duplicates in model name
for i in ar6_same.index:
    ar6_same.loc[i,'model'] += str(i)
df2plot_ar6 = pyam.IamDataFrame( ar6_same.drop(['B_100','B_100_1','B_100_2'], axis=1))

fig, ax = plt.subplots()
df2plot_ar6.plot(ax=ax, color='scenario', fill_between=dict(alpha=0.15), alpha=0.3)
df2plot_my_scenarios.plot(ax=ax,color='model')

plt.savefig(output_fig + "Figure_Annex_15__AR6_emissions_path.pdf", dpi=dpi, bbox_inches='tight')

###############
# timeseries of variable per capita in India
df_data.filter(model="IMACLIM-R",region="India", variable=["Expenditure|Household /capita"], scenario=["SUP_NPi_Default","Labor Tax Cuts__LaborShareImpact","Lump Sum Transfers__LaborShareImpact","Labor Tax Cuts","Lump Sum Transfers"]).timeseries()
df_data.filter(model="IMACLIM-R",region="India", variable=["GDP/capita"], scenario=["SUP_NPi_Default","Labor Tax Cuts__LaborShareImpact","Lump Sum Transfers__LaborShareImpact","Labor Tax Cuts","Lump Sum Transfers"]).timeseries()
df_data.filter(model="IMACLIM-R",region="India", variable=["Consumption|Household|Q1 /capita"], scenario=["SUP_NPi_Default","Labor Tax Cuts__LaborShareImpact","Lump Sum Transfers__LaborShareImpact","Labor Tax Cuts","Lump Sum Transfers"]).timeseries()

df_2_csv = df_data.filter(model="IMACLIM-R",region="India", variable=["Consumption|Household|Q1 /capita", 'GDP/capita', 'Expenditure|Household /capita'], scenario=["SUP_NPi_Default","Labor Tax Cuts__LaborShareImpact","Lump Sum Transfers__LaborShareImpact","Labor Tax Cuts","Lump Sum Transfers"])
df_2_csv.timeseries().sort_values(by='variable').reset_index().drop(["model","region","unit"],axis=1).to_csv('figures/India_ConsumptionHouseholdQ1_per_capita.csv',index=False)


df_2_csv = df_data.filter(model="IMACLIM-R",region="India", variable=["Consumption|Household|Q1 /capita true", 'GDP/capita', 'Expenditure|Household /capita'], scenario=["SUP_NPi_Default","Labor Tax Cuts__LaborShareImpact","Lump Sum Transfers__LaborShareImpact","Labor Tax Cuts","Lump Sum Transfers"])
df_2_csv.timeseries().sort_values(by='variable').reset_index().drop(["model","region","unit"],axis=1).to_csv('figures/India_ConsumptionHouseholdQ1_per_capitaQ1.csv',index=False)


df_data.filter(model="IMACLIM-R",region=["Europe","USA"], variable=["GDP/capita"], scenario=["SUP_NPi_Default","Labor Tax Cuts__LaborShareImpact","Lump Sum Transfers__LaborShareImpact"]).timeseries()
# difference de perte de PIB LS et LTX très importante pour l'Europe : part du cout du travail dans le cout de production ?
df_labour_tax_rate_base.filter(model="IMACLIM-R", scenario="SUP_NPi_Default").timeseries()
df_labour_tax_rate.filter(model="IMACLIM-R", region=['USA','EUR'],scenario=['Labor Tax Cuts','Lump Sum Transfers','SUP_NPi_Default']).timeseries()
# gros taux de tax


df_data.filter(model="IMACLIM-R",region=["Europe","USA"], variable=["GDP/capita"], scenario=["SUP_NPi_Default","Labor Tax Cuts__LaborShareImpact","Lump Sum Transfers__LaborShareImpact"]).to_csv('figures/gdp_per_cap.csv')
df_labour_tax_rate.filter(model="IMACLIM-R", region=['USA','EUR'],scenario=['Labor Tax Cuts','Lump Sum Transfers','SUP_NPi_Default']).to_csv('figures/labour_tax_rate.csv')
