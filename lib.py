# /home/leblanc/bin/anaconda3/envs/MostUpdated/bin/python

import pyam
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from PIL import Image
import pandas as pd
import matplotlib.gridspec as gridspec
import seaborn as sns
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes, mark_inset
import numpy as np
from matplotlib.ticker import LogLocator, FixedFormatter

colors_pyam = pyam.plotting.PYAM_COLORS



# todo: duplicates by model.
def split_drop_model_var(df_simu, var_not_duplicates, m):
    df_simu_m = df_simu.filter(model=m)
    df_simu_no_m = df_simu.filter(model=[k for k in df_simu.model if k!=m])
    df_simu_m = df_simu_m.filter(variable=var_not_duplicates)
    return pyam.concat( [df_simu_m,df_simu_no_m])

def drop_duplicates_model(df_simu, df_data):
    for m in df_simu.model:
        var_not_duplicates = [v for v in df_simu.filter(model=m).variable if not v in df_data.filter(model=m).variable]
        df_simu = split_drop_model_var(df_simu, var_not_duplicates, m)
    return df_simu

def normalize_group_percent(group, sc_norm='SUP_NPi_Default',numerical_columns=None):
    default_scenario_data = group[group['scenario'] == sc_norm][numerical_columns]
    group[numerical_columns] = ((group[numerical_columns] / default_scenario_data.values) -1) * 100
    return group

def normalize_group_ginipoint(group, sc_norm='SUP_NPi_Default',numerical_columns=None):
    default_scenario_data = group[group['scenario'] == sc_norm][numerical_columns]
    group[numerical_columns] = (group[numerical_columns] - default_scenario_data.values) * 100
    return group

def normalize_group_differences(group, sc_norm='SUP_NPi_Default',numerical_columns=None):
    default_scenario_data = group[group['scenario'] == sc_norm][numerical_columns]
    group[numerical_columns] = group[numerical_columns] - default_scenario_data.values
    return group


def normalize_data(df_data, sc_norm, type_norm="percent"):
    df_pandas = df_data.timeseries().reset_index()
    numerical_columns = df_pandas.columns[5:]  # Select columns from 2014 onwards
    if type_norm=="percent":
         df_pandas = df_pandas.groupby(['model', 'region', 'variable']).apply(lambda x: normalize_group_percent(x, sc_norm=sc_norm, numerical_columns=numerical_columns))
         #df_pandas = df_pandas.groupby(['model', 'region', 'variable']).apply(normalize_group_percent)
    elif type_norm=="ginipoint":
         df_pandas = df_pandas.groupby(['model', 'region', 'variable']).apply(lambda x: normalize_group_ginipoint(x, sc_norm=sc_norm, numerical_columns=numerical_columns))
    elif type_norm=="differences":
         df_pandas = df_pandas.groupby(['model', 'region', 'variable']).apply(lambda x: normalize_group_differences(x, sc_norm=sc_norm, numerical_columns=numerical_columns))
    df_pandas = df_pandas.drop( ['model','region','variable'],axis=1)
    df_pandas = df_pandas.reset_index().drop("level_3",axis=1)
    df_data = pyam.IamDataFrame( df_pandas)
    return df_data

def plot_one_figure_allvariant(df, df_normbyx, df_lab, df_normbyx_lab, var, sc_v, styleline="scenario", subtitle="baseline", dict_ymin=None, dict_ymax=None):
    plt.clf()
    plt.cla()

    nb_col = 3
    fig = plt.figure(figsize=(16, 10), dpi=dpi)  # Increase figure size and resolution
    gs = gridspec.GridSpec(4, 13)
    axs = []

    # Ploty first the without labor share effect
    df = df.filter(year=[2025,2035,2045])
    legend_handled = False
    for i, reg in enumerate(order_region):
        j = i // nb_col
        k = i % nb_col
        df2plot = df.filter( region=reg)
        axs.append(fig.add_subplot(gs[2*j:2*j+2, 2*k:2*k+2]))
        df2plot.plot(color="model", marker="o", markersize=3, linestyle=styleline, ax=axs[i], title=None, linewidth=1)
        axs[i].set_xlabel('')
        axs[i].set_ylabel(reg, fontsize=10)
        axs[i].grid(True)  # Add grid for better readability

        if not legend_handled and len(df2plot.model) == len(df.model):
            legend_handled = True
            handles, labels = axs[i].get_legend_handles_labels()
        axs[i].legend().set_visible(False)
        if dict_ymin is not None and dict_ymax is not None:
            if var in dict_ymin.keys() and var in dict_ymax.keys():
                if reg in dict_ymin[var].keys() and reg in dict_ymax[var].keys():
                    axs[i].set_ylim(bottom=dict_ymin[var][reg], top=dict_ymax[var][reg])

    # Ploty first the without labor share effect
    df = df_lab.filter(year=[2025,2035,2045])
    legend_handled = False
    for i, reg in enumerate(order_region):
        j = i // nb_col
        k = i % nb_col
        df2plot = df.filter( region=reg)
        axs.append(fig.add_subplot(gs[2*j:2*j+2, 7+2*k:2*k+2+7]))
        df2plot.plot(color="model", marker="o", markersize=3, linestyle=styleline, ax=axs[i+6], title=None, linewidth=1)
        axs[i+6].set_xlabel('')
        axs[i+6].set_ylabel(reg, fontsize=10)
        axs[i+6].grid(True)  # Add grid for better readability

        if not legend_handled and len(df2plot.model) == len(df.model):
            legend_handled = True
            handles, labels = axs[i+6].get_legend_handles_labels()
            labels = [l.split('__')[0] for l in labels]
        axs[i+6].legend().set_visible(False)
        if dict_ymin is not None and dict_ymax is not None:
            if var in dict_ymin.keys() and var in dict_ymax.keys():
                if reg in dict_ymin[var].keys() and reg in dict_ymax[var].keys():
                    axs[i+6].set_ylim(bottom=dict_ymin[var][reg], top=dict_ymax[var][reg])

    # example
    #axs.append(fig.add_subplot(gs[2, 2:]))

    fig.tight_layout(pad=1.0)
    #fig.legend(handles, labels, loc = (0.57, 0.035), ncol=4, fontsize=10)
    #fig.suptitle(var.replace("|", " - ") + " (% compare to the " + subtitle + ")", fontsize=14)
    fig.subplots_adjust(top=0.99, right=0.85, bottom=0.05)

    # Place the legend in the space below the plot
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.45, -0.02), ncol=4, fontsize=10 )

    fig.text(0.22, 1., '(a)', fontsize=16, ha='center')
    fig.text(0.5+0.18, 1., '(b)', fontsize=16, ha='center')

    plt.savefig(output_fig + var.replace(" ", "_").replace("|", "_") + "__" + sc_v + ".pdf", dpi=dpi, bbox_inches='tight')
    return 0

def figB_plot_one_figure_allvariant(df, var, sc_v, styleline="scenario", subtitle="baseline", dict_ymin=None, dict_ymax=None, year2filter=[2025,2035,2045], ytitle=None):
    plt.clf()
    plt.cla()

    nb_col = 3
    #fig = plt.figure(figsize=(16, 10), dpi=dpi)  # Increase figure size and resolution
    fig = plt.figure(figsize=(8, 10), dpi=dpi)  # Increase figure size and resolution
    #gs = gridspec.GridSpec(4, 13)
    gs = gridspec.GridSpec(4, 6)
    axs = []

    # Plot first the without labor share effect
    df = df.filter(year=year2filter)
    legend_handled = False
    for i, reg in enumerate(order_region):
        j = i // nb_col
        k = i % nb_col
        if reg != 'Africa':
            df2plot = df.filter( region=reg)
            axs.append(fig.add_subplot(gs[2*j:2*j+2, 2*k:2*k+2]))
            df2plot.plot(color="model", marker="model", markersize=3, linestyle=styleline, ax=axs[i], title=None, linewidth=1)
            axs[i].set_xlabel('')
            if k !=0:
                axs[i].set_ylabel(reg, fontsize=10)
            else:
                lab = ytitle + '\n\n' + reg
                axs[i].set_ylabel(lab)
            axs[i].grid(False)  # Add grid for better readability
            # Ensure the axes lines (spines) are visible
            axs[i].axhline(0, color='grey', linewidth=0.5)
            # Customize the y-ticks to ensure they are visible
            axs[i].tick_params(axis='y', which='both', direction='in', length=15, width=10, color='lightgrey')
            """
            ytick_labels = axs[i].get_yticklabels()
            yticks = axs[i].get_yticks()

            current_labels = [label.get_text() for label in ytick_labels]
            axs[i].set_yticks( yticks)
            axs[i].set_yticklabels( current_labels)
            axs[i].tick_params(axis='y', which='both', direction='in', length=5, width=1, color='grey')
            """
            # Set custom x-ticks and labels (for years)
            years = year2filter
            axs[i].set_xticks(years)
            axs[i].set_xticklabels(years)  # Rotate labels for better readability
            #axs[i].set_yticks(axs[i].get_yticks())  # This ensures ticks are set
            #axs[i].tick_params(axis='y', which='both', direction='in', length=15, width=10, color='grey')

            # BEGIN legend
            if not legend_handled and len(df2plot.model) == len(df.model):
                legend_handled = True
                handles, labels = axs[i].get_legend_handles_labels()
                labels = [l.split('__')[0] for l in labels]

                scenario_handles = reduce_legend(df2plot,axs[i],type_legend = "mixed")
                # Update the legend with only scenario labels
                #axs[j,k].legend(scenario_handles.values(), scenario_handles.keys(), loc='lower center', fontsize='small')
                legend_handles = []
                handles, labels = axs[i].get_legend_handles_labels()
                labels = [l.split('__')[0] for l in labels]
                print(labels)
                get_models = list(set([e.split(' - ')[0] for e in labels]))
                get_sc = list(set([e.split(' - ')[-1] for e in labels]))
                dict_linestyle = {'Labor Tax Cuts':'-', 'Lump Sum Transfers':'--'}
                if True: # mode=="color_model": # legend when model are in colors
                    for label in get_models + get_sc:#, handle in scenario_handles.items():
                        if label in ['Labor Tax Cuts', 'Lump Sum Transfers']:
                            legend_handles.append( mlines.Line2D([], [], color='black', marker='None', linestyle=dict_linestyle[label], label=label))
                        else:
                            for km in color_map_model.keys():
                                if km in label:
                                    color = colors_pyam[color_map_model[km]]
                            legend_handles.append( mlines.Line2D([], [], color=color, marker=marker_map_model[label], linestyle='None', label=label))
                            #legend_handles.append(  mpatches.Patch(color=color, label=label, marker=marker_map_model[label] ) )

                    #axs[j,k].legend(handles=legend_handles)
                    #legend = axs[j,k].legend(handles=legend_handles, bbox_to_anchor=(3.2, -0.2), ncol=6, fontsize=14)
                    """
                    i=0
                    for label, handle in scenario_handles.items():
                        if not label in ['Labor Tax Cuts', 'Lump Sum Transfers'']:
                            for km in color_map_model.keys():
                                if km in label:
                                    color = colors_pyam[color_map_model[km]]
                            legend.texts[i].set_color(color)
                        i+=1
                     """
                # END legend


            axs[i].legend().set_visible(False)
            if dict_ymin is not None and dict_ymax is not None:
                if var in dict_ymin.keys() and var in dict_ymax.keys():
                    if reg in dict_ymin[var].keys() and reg in dict_ymax[var].keys():
                        axs[i].set_ylim(bottom=dict_ymin[var][reg], top=dict_ymax[var][reg])
        else:
            axs.append(fig.add_subplot(gs[2*j:2*j+2, 2*k:2*k+2]))
            axs[i].set_visible(False)

    # example
    #axs.append(fig.add_subplot(gs[2, 2:]))

    fig.tight_layout(pad=1.0)
    #fig.legend(handles, labels, loc = (0.57, 0.035), ncol=4, fontsize=10)
    #fig.suptitle(var.replace("|", " - ") + " (% compare to the " + subtitle + ")", fontsize=14)
    fig.subplots_adjust(top=0.99, right=0.85, bottom=0.05)

    # Place the legend in the space below the plot
    legend = fig.legend(handles=legend_handles, loc='upper center', bbox_to_anchor=(0.75, 0.9), ncol=1, fontsize=12 ) # previous version
    i=0
    for label in get_models + get_sc:
        print(i, label)
        if not label in ['Labor Tax Cuts', 'Lump Sum Transfers']:
            for km in color_map_model.keys():
                if km in label:
                    color = colors_pyam[color_map_model[km]]
            legend.texts[i].set_color(color)
        i+=1
    #fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.45, 0.02), ncol=4, fontsize=8 )

    plt.savefig(output_fig + "Figure_"+subtitle+".pdf", dpi=dpi, bbox_inches='tight')
    return 0

def figB_plot_one_figure_allvariant_quartile(df, var, sc_v, styleline="scenario", subtitle="baseline", dict_ymin=None, dict_ymax=None):
    plt.clf()
    plt.cla()

    nb_col = 3
    #fig = plt.figure(figsize=(16, 10), dpi=dpi)  # Increase figure size and resolution
    fig = plt.figure(figsize=(8, 10), dpi=dpi)  # Increase figure size and resolution
    #gs = gridspec.GridSpec(4, 13)
    gs = gridspec.GridSpec(4, 6)
    axs = []

    # Ploty first the without labor share effect
    legend_handled = False
    for i, reg in enumerate(order_region):
        j = i // nb_col
        k = i % nb_col
        if reg != 'Africa':
            df2plot = df.filter( region=reg, year=[2025,2035,2045])
            axs.append(fig.add_subplot(gs[2*j:2*j+2, 2*k:2*k+2]))
            df2plot.plot(color="model", marker="model", markersize=3, linestyle=styleline, ax=axs[i], title=None, linewidth=1)
            axs[i].set_xlabel('')
            axs[i].set_ylabel(reg, fontsize=10)
            axs[i].grid(False)  # Add grid for better readability
            # Ensure the axes lines (spines) are visible
            axs[i].axhline(0, color='grey', linewidth=0.5)
            # Customize the y-ticks to ensure they are visible
            axs[i].tick_params(axis='y', which='both', direction='in', length=15, width=10, color='lightgrey')
            """
            ytick_labels = axs[i].get_yticklabels()
            yticks = axs[i].get_yticks()

            current_labels = [label.get_text() for label in ytick_labels]
            axs[i].set_yticks( yticks)
            axs[i].set_yticklabels( current_labels)
            axs[i].tick_params(axis='y', which='both', direction='in', length=5, width=1, color='grey')
            """
            # Set custom x-ticks and labels (for years)
            years = [2025, 2035, 2045]
            axs[i].set_xticks(years)
            axs[i].set_xticklabels(years)  # Rotate labels for better readability
            #axs[i].set_yticks(axs[i].get_yticks())  # This ensures ticks are set
            #axs[i].tick_params(axis='y', which='both', direction='in', length=15, width=10, color='grey')

            # BEGIN legend
            if not legend_handled and len(df2plot.model) == len(df.model):
                #legend_handled = True
                #handles, labels = axs[i].get_legend_handles_labels()
                #labels = [l.split('__')[0] for l in labels]

                scenario_handles = reduce_legend(df2plot,axs[i],type_legend = "mixed")
                legend_handles = []
                handles, labels = axs[i].get_legend_handles_labels()
                #labels = [l.split('__')[0] for l in labels]
                print(labels)
                get_models = list(set([e.split(' - ')[0] for e in labels]))
                get_sc = list(set([e.split(' - ')[-1] for e in labels]))
                dict_linestyle = {}
                for sc in get_sc:
                    if 'sensit_first_decile0.8' in sc:
                        dict_linestyle[sc] = ':'
                    elif 'sensit_first_decile1.2' in sc:
                        dict_linestyle[sc] = '--'
                    else:
                        dict_linestyle[sc] = '-'
                #dict_linestyle = {'Labor Tax Cuts':'-', 'Lump Sum Transfers':'--'}
                if True: # mode=="color_model": # legend when model are in colors
                    for label in get_models + get_sc:#, handle in scenario_handles.items():
                        if label in get_sc:
                            legend_handles.append( mlines.Line2D([], [], color='black', marker='None', linestyle=dict_linestyle[label], label=label))
                        else:
                            for km in color_map_model.keys():
                                if km in label:
                                    color = colors_pyam[color_map_model[km]]
                            legend_handles.append( mlines.Line2D([], [], color=color, marker=marker_map_model[label], linestyle='None', label=label))
                            #legend_handles.append(  mpatches.Patch(color=color, label=label, marker=marker_map_model[label] ) )

                    #axs[j,k].legend(handles=legend_handles)
                    #legend = axs[j,k].legend(handles=legend_handles, bbox_to_anchor=(3.2, -0.2), ncol=6, fontsize=14)
                    """
                    i=0
                    for label, handle in scenario_handles.items():
                        if not label in ['Labor Tax Cuts', 'Lump Sum Transfers'']:
                            for km in color_map_model.keys():
                                if km in label:
                                    color = colors_pyam[color_map_model[km]]
                            legend.texts[i].set_color(color)
                        i+=1
                     """
                # END legend


            axs[i].legend().set_visible(False)
            if dict_ymin is not None and dict_ymax is not None:
                if var in dict_ymin.keys() and var in dict_ymax.keys():
                    if reg in dict_ymin[var].keys() and reg in dict_ymax[var].keys():
                        axs[i].set_ylim(bottom=dict_ymin[var][reg], top=dict_ymax[var][reg])
        else:
            axs.append(fig.add_subplot(gs[2*j:2*j+2, 2*k:2*k+2]))
            axs[i].set_visible(False)

    # example
    #axs.append(fig.add_subplot(gs[2, 2:]))

    fig.tight_layout(pad=1.0)
    #fig.legend(handles, labels, loc = (0.57, 0.035), ncol=4, fontsize=10)
    #fig.suptitle(var.replace("|", " - ") + " (% compare to the " + subtitle + ")", fontsize=14)
    fig.subplots_adjust(top=0.99, right=0.85, bottom=0.05)

    # Place the legend in the space below the plot
    legend = fig.legend(handles=legend_handles, loc='upper center', bbox_to_anchor=(0.75, 0.9), ncol=1, fontsize=12 ) # previous version
    i=0
    for label in get_models + get_sc:
        print(i, label)
        if not label in ['Labor Tax Cuts', 'Lump Sum Transfers']:
            for km in color_map_model.keys():
                if km in label:
                    color = colors_pyam[color_map_model[km]]
            legend.texts[i].set_color(color)
        i+=1
    #fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.45, 0.02), ncol=4, fontsize=8 )

    plt.savefig(output_fig + "Figure_"+subtitle+".pdf", dpi=dpi, bbox_inches='tight')
    return 0

def fig_annex_simple(df, styleline="scenario", title_file=None, dict_ymin=None, dict_ymax=None, title_fig=None, list_year=None):
    plt.clf()
    plt.cla()

    nb_col = 3
    fig = plt.figure(figsize=(16, 8), dpi=dpi)  # Increase figure size and resolution
    gs = gridspec.GridSpec(4, 6)
    axs = []

    if list_year is None:
        list_year = [2025,2035,2045]
    df = df.filter(year=list_year)

    # Ploty first the without labor share effect
    legend_handled = False
    for i, reg in enumerate(order_region):
        j = i // nb_col
        k = i % nb_col
        if reg != 'Africa':
            df2plot = df.filter( region=reg)
            axs.append(fig.add_subplot(gs[2*j:2*j+2, 2*k:2*k+2]))
            df2plot.plot(color="model", marker="o", markersize=3, linestyle=styleline, ax=axs[i], title=None, linewidth=1)
            axs[i].set_xlabel('')
            axs[i].set_ylabel(reg, fontsize=10)
            axs[i].grid(True)  # Add grid for better readability

            if not legend_handled and len(df2plot.model) == len(df.model):
                legend_handled = True
                handles, labels = axs[i].get_legend_handles_labels()
                labels = [l.split('__')[0] for l in labels]
            axs[i].legend().set_visible(False)
            if dict_ymin is not None and dict_ymax is not None:
                if reg in dict_ymin.keys() and reg in dict_ymax.keys():
                        axs[i].set_ylim(bottom=dict_ymin[reg], top=dict_ymax[reg])
        else:
            axs.append(fig.add_subplot(gs[2*j:2*j+2, 2*k:2*k+2]))
            axs[i].set_visible(False)
        axs[i].set_xticks(list_year)

    fig.tight_layout(pad=1.0)
    fig.subplots_adjust(top=0.99, right=0.85, bottom=0.05)

    # Place the legend in the space below the plot

    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.8, 1), ncol=1, fontsize=10 )
    #fig.suptitle(title_fig, fontsize=16)
    # Adjust layout to make room for the title
    #plt.tight_layout(rect=[0, 0, 1, 0.99])  # Adjust the top to make room for the title


    plt.savefig(output_fig + title_file+".pdf", dpi=dpi, bbox_inches='tight')
    return 0

def fig_annex_simple_log(df, styleline="scenario", title_file=None, dict_ymin=None, dict_ymax=None, title_fig=None, list_year = [2025,2035,2045]):
    plt.clf()
    plt.cla()

    nb_col = 2
    fig = plt.figure(figsize=(8, 8), dpi=dpi)  # Increase figure size and resolution
    gs = gridspec.GridSpec(4, 2)
    axs = []

    df = df.filter(year=list_year)

    # Ploty first the without labor share effect
    legend_handled = False
    for i, reg in enumerate(['World']):
        j = i // nb_col
        k = i % nb_col
        if reg != 'Africa':
            df2plot = df.filter( region=reg)
            axs.append(fig.add_subplot(gs[2*j:2*j+2, 2*k:2*k+2]))
            df2plot.plot(color="model", marker="o", markersize=3, linestyle=styleline, ax=axs[i], title=None, linewidth=1)
            axs[i].set_xlabel('')
            axs[i].set_ylabel(reg, fontsize=10)
            axs[i].set_yscale('log')  # linthresh is the linear threshold around zero
            axs[i].grid(True)  # Add grid for better readability

            if not legend_handled and len(df2plot.model) == len(df.model):
                legend_handled = True
                handles, labels = axs[i].get_legend_handles_labels()
                labels = [l.split('__')[0] for l in labels]
            axs[i].legend().set_visible(False)
            axs[i].set_ylim(bottom=1)
            if dict_ymin is not None:
                if reg in dict_ymin.keys():
                        axs[i].set_ylim(bottom=dict_ymin[reg])
        else:
            axs.append(fig.add_subplot(gs[2*j:2*j+2, 2*k:2*k+2]))
            axs[i].set_visible(False)
        axs[i].set_xticks(list_year)


    fig.tight_layout(pad=1.0)
    fig.subplots_adjust(top=0.99, right=0.85, bottom=0.05)

    # Place the legend in the space below the plot

    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(1.1, 1), ncol=1, fontsize=10 )
    #fig.suptitle(title_fig, fontsize=16)
    # Adjust layout to make room for the title
    #plt.tight_layout(rect=[0, 0, 1, 0.99])  # Adjust the top to make room for the title

    plt.savefig(output_fig + title_file+".pdf", dpi=dpi, bbox_inches='tight')
    return 0


def norm_1_scenario(group, sc_norm, numerical_columns):
    default_scenario_data = group[group['scenario'] == sc_norm][numerical_columns]
    group[numerical_columns] = ((group[numerical_columns] / default_scenario_data.values) -1) * 100
    return group

def select_n_2_pandas(df, sc_sel, sc_norm):
    df = df.filter( scenario = sc_sel)
    df_pandas = df.timeseries().reset_index()
    numerical_columns = df_pandas.columns[5:]  # Select columns from 2014 onwards

    df_pandas = df_pandas.groupby(['model', 'region', 'variable']).apply(
        lambda group: norm_1_scenario(group, sc_norm, numerical_columns)
    )
    df_pandas = df_pandas.drop( ['model','region','variable'],axis=1)
    df_pandas = df_pandas.reset_index().drop("level_3",axis=1)
    df_data = pyam.IamDataFrame( df_pandas)

    return pyam.IamDataFrame( df_pandas)

def normalize_data_by_x(df, sc_sel, sc_norm):
    df1 = select_n_2_pandas(df, sc_sel=sc_sel, sc_norm=sc_norm)
    return df1

def plot_diff(df_normbyx, df_normbyx_noLSimpact, df_normbyx_norm, var, sc_v, styleline="scenario", subtitle="baseline", dict_ymin=None):

    plt.clf()
    plt.cla()
    #plt.style.use('seaborn')  # Use a clean style

    fig = plt.figure(figsize=(8, 10), dpi=dpi)  # Increase figure size and resolution

    gs = gridspec.GridSpec(3, 1)
    axs = []

    titles = [r"\textbf{Labor Tax Cuts} VS \textbf{Lump Sum Transfers} (\%)", r"\textbf{Labor Tax Cuts} VS \textbf{Lump Sum Transfers} (\%)\\    with Income effect", r"Pure Income effect on \textbf{Labor Tax Cuts} ($\Delta$)"]

    for i, df in enumerate( [df_normbyx_noLSimpact, df_normbyx, df_normbyx_norm]):
        axs.append(fig.add_subplot(gs[i, 0]))

        df = df.filter(year=2040)
        df.plot(x="region", order={'region':order_region}, color="model", marker="model", markersize=5,linestyle='None', ax=axs[i], title=None, linewidth=0.6)
        axs[i].legend().set_visible(False)
        axs[i].set_xticklabels(['']+order_region+[''], rotation=45, ha='right')
        axs[i].set_title( titles[i])

        fig.tight_layout(pad=1.0)
        #fig.legend(handles, labels, loc = (0.57, 0.035), ncol=1, fontsize=10)

        plt.savefig(output_fig + var.replace(" ", "_").replace("|", "_") + "__evolution.pdf", dpi=dpi, bbox_inches='tight')
    return 0


def figC_plot_diff(df_normbyx_norm, df_normbyx_norm_noLSimpact, var, sc_v, styleline="scenario", subtitle="baseline", dict_ymin=None, y1min=0):

    plt.clf()
    plt.cla()
    #plt.style.use('seaborn')  # Use a clean style

    fig = plt.figure(figsize=(10, 10), dpi=dpi)  # Increase figure size and resolution

    nb_row = 20
    row_break = 6
    y1, y2, y3, y4 = y1min, 0.6, 0.65, 6
    gs = gridspec.GridSpec(nb_row,2)
    axs = []

    titles = [r"Pure Income effect on \textbf{Lump Sum Transfers}", r"Pure Income effect on \textbf{Labor Tax Cut"]
 
    j=0
    list_order_region = ['USA', 'Europe', 'China', 'Brazil', 'India'] 

    for i, df in enumerate( [df_normbyx_norm_noLSimpact, df_normbyx_norm]):
            df = df.filter(year=2040, region = list_order_region)
            # upper part
            axs.append(fig.add_subplot(gs[0:row_break, i]))

            df.plot(x="region", order={'region':list_order_region}, color="model", marker="model", markersize=8,linestyle='None', ax=axs[j], title=None, linewidth=0.6)
            axs[j].legend().set_visible(False)
            axs[j].set_title( titles[i])
            axs[j].set_ylim(y3, y4)
            #axs[j].spines['bottom'].set_visible(False)
            #axs[j].xaxis.tick_top()
            #axs[j].tick_params(label=False)
            #axs[j].set_xticks([])
            axs[j].set_xlabel('')
            axs[j].set_ylabel('')
            axs[j].set_xticklabels([]) 
            axs[j].grid(True) 
            # lower part
            
            j+=1
            axs.append(fig.add_subplot(gs[row_break:, i]))
            df.plot(x="region", order={'region':list_order_region}, color="model", marker="model", markersize=8,linestyle='None', ax=axs[j], title=None, linewidth=0.6)
            axs[j].legend().set_visible(False)
            axs[j].set_xticklabels(['']+list_order_region+[''], rotation=45, ha='right')
            axs[j].set_ylim(y1, y2)
            axs[j].set_ylabel('Gini scenario - Gini baseline')
            #axs[j].spines['bottom'].set_visible(False)
            #axs[j].xaxis.tick_bottom()
            if i ==0:
                handles, labels = axs[j].get_legend_handles_labels()
                labels = [l.split(' - ')[0] for l in labels]
            axs[j].legend().set_visible(False)
            j+=1
    #fig.legend(handles, labels, loc = (0.15, -0.011), ncol=4, fontsize=10)
    #fig.subplots_adjust( bottom=0.05)
    fig.tight_layout(pad=1.0)

    fig.subplots_adjust(top=0.99, right=0.85, bottom=0.05)

    # Place the legend in the space below the plot
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.45, -0.05), ncol=4, fontsize=10 )

    #fig.legend(handles, labels, loc = (0.57, 0.035), ncol=1, fontsize=10)

    plt.savefig(output_fig + "Figure_4_nonlog_split.pdf", dpi=dpi, bbox_inches='tight')
    return 0

def figC_plot_diff_nonlog(df_normbyx_norm, df_normbyx_norm_noLSimpact, var, sc_v, styleline="scenario", subtitle="baseline", dict_ymin=None, y1min=0, xbiais=0):

    plt.clf()
    plt.cla()
    #plt.style.use('seaborn')  # Use a clean style

    fig = plt.figure(figsize=(10, 6), dpi=dpi)  # Increase figure size and resolution

    nb_row = 20
    row_break = 6
    y1, y2, y3, y4 = 0, 2.2, 0.65, 6
    y1, y2, y3, y4 = -1.8, 6.3, 0.65, 6
    gs = gridspec.GridSpec(nb_row,2)
    axs = []

    titles = [r"Pure Income effect on \textbf{Lump Sum Transfers}", r"Pure Income effect on \textbf{Labor Tax Cuts}"]
 
    j=0
    #list_order_region = ['USA', 'Europe', 'China', 'Brazil', 'India'] 
    list_order_region = ['India', 'China', 'Brazil', 'USA', 'Europe'] 

    for i, df in enumerate( [df_normbyx_norm_noLSimpact, df_normbyx_norm]):
            df = df.filter(year=2040, region = list_order_region)

            # lower part
            #j+=1
            axs.append(fig.add_subplot(gs[:, i]))
            df.plot(x="region", order={'region':list_order_region}, color="model", marker="model", markersize=8,linestyle='None', ax=axs[j], title=None, linewidth=0.6)
            axs[j].legend().set_visible(False)
            axs[j].set_xticklabels(['']+list_order_region+[''], rotation=45, ha='right')
            axs[j].set_title( titles[i])
            axs[j].set_ylim(y1, y2)
            axs[j].set_ylabel('Gini scenario - Gini baseline')
            axs[j].set_xlabel("")
            axs[j].axhline(y= 0, color='black', linestyle='-')
            #axs[j].axhline(y= 0.5, color='black', linestyle='--', linewidth=0.7)
            #axs[j].axhline(y= -0.5, color='black', linestyle='--', linewidth=0.7)
            # Set the y-axis to log scale
            #axs[j].set_yscale('log')
            tt=0.01
            #axs[j].set_yscale('symlog', linthresh=tt, linscale=tt)  # linthresh is the linear threshold around zero
            # Add grid lines
            axs[j].grid(which="both", linestyle='-', linewidth=0.5)
            axs[j].yaxis.set_minor_locator(plt.LogLocator(base=10, subs=np.arange(-10, 10) * 0.1))
            axs[j].grid(which="minor", linestyle=':', linewidth=0.5)

            # Define major and minor ticks
            major_ticks = [-1, 0, 1, 2, 5]
            minor_ticks = [ 2, 5]

            # Set major and minor ticks
            axs[j].set_yticks(major_ticks)
            axs[j].set_yticks(minor_ticks, minor=True)

            # Format major tick labels
            axs[j].set_yticklabels(major_ticks)

            # Optionally, format minor tick labels
            axs[j].yaxis.set_minor_formatter(FixedFormatter([f'{tick}' for tick in minor_ticks]))

            # Add grid lines for both major and minor ticks
            axs[j].grid(which="both", linestyle='-', linewidth=0.5)
            axs[j].grid(which="minor", linestyle=':', linewidth=0.5, alpha=0.7)

            if i ==0:
                handles, labels = axs[j].get_legend_handles_labels()
                labels = [l.split(' - ')[0] for l in labels]
            axs[j].legend().set_visible(False)
            j+=1
    #fig.legend(handles, labels, loc = (0.15, -0.011), ncol=4, fontsize=10)
    #fig.subplots_adjust( bottom=0.05)
    fig.tight_layout(pad=1.0)

    fig.subplots_adjust(top=0.99, right=0.85, bottom=0.05)

    # Place the legend in the space below the plot
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.45, -0.05), ncol=4, fontsize=10 )

    #fig.legend(handles, labels, loc = (0.57, 0.035), ncol=1, fontsize=10)

    plt.savefig(output_fig + "Figure_4_nonlog.pdf", dpi=dpi, bbox_inches='tight')
    return 0

def figC_plot_diff_log(df_normbyx_norm, df_normbyx_norm_noLSimpact, var, sc_v, styleline="scenario", subtitle="baseline", dict_ymin=None, y1min=0, xbiais=0):

    plt.clf()
    plt.cla()
    #plt.style.use('seaborn')  # Use a clean style

    fig = plt.figure(figsize=(10, 6), dpi=dpi)  # Increase figure size and resolution

    nb_row = 20
    row_break = 6
    y1, y2, y3, y4 = 0, 2.2, 0.65, 6
    y1, y2, y3, y4 = -1.8, 7, 0.65, 6
    gs = gridspec.GridSpec(nb_row,2)
    axs = []

    titles = [r"Pure Income effect on \textbf{Lump Sum Transfers}", r"Pure Income effect on \textbf{Labor Tax Cuts}"]
    y_label = r"$\frac{Cons. scenario - Cons. baseline}{Cons. baseline}$ (\%)"

    j=0
    #list_order_region = ['USA', 'Europe', 'China', 'Brazil', 'India'] 
    list_order_region = ['India', 'China', 'Brazil', 'USA', 'Europe'] 

    for i, df in enumerate( [df_normbyx_norm_noLSimpact, df_normbyx_norm]):
            df = df.filter(year=2040, region = list_order_region)

            # lower part
            #j+=1
            axs.append(fig.add_subplot(gs[:, i]))
            df.plot(x="region", order={'region':list_order_region}, color="model", marker="model", markersize=8,linestyle='None', ax=axs[j], title=None, linewidth=0.6)
            axs[j].legend().set_visible(False)
            axs[j].set_xticklabels(['']+list_order_region+[''], rotation=45, ha='right')
            axs[j].set_title( titles[i])
            axs[j].set_ylim(y1, y2)
            axs[j].set_ylabel('Gini scenario - Gini baseline')
            axs[j].set_xlabel("")
            axs[j].axhline(y= 0, color='black', linestyle='-')
            #axs[j].axhline(y= 0.5, color='black', linestyle='--', linewidth=0.7)
            #axs[j].axhline(y= -0.5, color='black', linestyle='--', linewidth=0.7)
            # Set the y-axis to log scale
            #axs[j].set_yscale('log')
            tt=0.01
            axs[j].set_yscale('symlog', linthresh=tt, linscale=tt)  # linthresh is the linear threshold around zero
            # Add grid lines
            axs[j].grid(which="both", linestyle='-', linewidth=0.5)
            axs[j].yaxis.set_minor_locator(plt.LogLocator(base=10, subs=np.arange(-10, 10) * 0.1))
            axs[j].grid(which="minor", linestyle=':', linewidth=0.5)

            # Define major and minor ticks
            major_ticks = [-1, 0, 1, 10]
            minor_ticks = [-0.1, 0.1,  2, 5]

            # Set major and minor ticks
            axs[j].set_yticks(major_ticks)
            axs[j].set_yticks(minor_ticks, minor=True)

            # Format major tick labels
            axs[j].set_yticklabels(major_ticks)

            # Optionally, format minor tick labels
            axs[j].yaxis.set_minor_formatter(FixedFormatter([f'{tick}' for tick in minor_ticks]))

            # Add grid lines for both major and minor ticks
            axs[j].grid(which="both", linestyle='-', linewidth=0.5)
            axs[j].grid(which="minor", linestyle=':', linewidth=0.5, alpha=0.7)

            if i ==0:
                handles, labels = axs[j].get_legend_handles_labels()
                labels = [l.split(' - ')[0] for l in labels]
            axs[j].legend().set_visible(False)
            j+=1
    #fig.legend(handles, labels, loc = (0.15, -0.011), ncol=4, fontsize=10)
    #fig.subplots_adjust( bottom=0.05)
    fig.tight_layout(pad=1.0)

    fig.subplots_adjust(top=0.99, right=0.85, bottom=0.05)

    # Place the legend in the space below the plot
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.45, -0.05), ncol=4, fontsize=10 )

    #fig.legend(handles, labels, loc = (0.57, 0.035), ncol=1, fontsize=10)

    plt.savefig(output_fig + "Figure_4.pdf", dpi=dpi, bbox_inches='tight')
    return 0

def reduce_legend(df, ax, type_legend, marker="+"):
    # Filter legend to display only by scenario
    handles, labels = ax.get_legend_handles_labels()
    unique_scenarios = df.scenario

    if type_legend == "scenario":
        index=-1
    elif type_legend == "model":
        index=0
    if type_legend == "scenario" or type_legend == "model":
        scenario_handles = {}
        for i, ilab in enumerate(labels):
            # Create a dictionary to map scenarios to their handles
            sc = ' '.join(ilab.split(' ')[1:])
            if not sc in scenario_handles.keys():
                scenario_handles[sc.split('__')[0]] = handles[i]
    if type_legend == "mixed":
        scenario_handles = {}
        index=-1
        for i, ilab in enumerate(labels):
            # Create a dictionary to map scenarios to their handles
            sc = ' '.join(ilab.split(' ')[1:])
            if not sc in scenario_handles.keys():
                scenario_handles[sc.split('__')[0]] = handles[i]
        index=0
        for i, ilab in enumerate(labels):
            # Create a dictionary to map scenarios to their handles
            sc = ilab.split(' ')[index]
            if not sc in scenario_handles.keys():
                scenario_handles[sc.split('__')[0]] = handles[i]

    return scenario_handles


def plot_all_nuage(df, title, color, show_legend=False, marker=None, zoom=True, rename_dict=None, x_label=True, y_label=True):
    df = df.rename(rename_dict)
    df = df.filter(year=[y for y in df.year if y >= 2025])
    plt.clf()
    plt.cla()
    ax = df.plot.scatter( x=rename_dict['variable']["-Inequality index|Consumption Gini"], y=rename_dict['variable']["Expenditure|Household"], color=color,  marker=marker)
    ax.legend( loc='lower right', fontsize='small')
    # Highlight the x=0 and y=0 axes
    ax.axhline(0, color='midnightblue', linewidth=1.2)  # Highlight y=0
    ax.axvline(0, color='midnightblue', linewidth=1.2)  # Highlight x=0
    if marker=="+":
        ax.set_ylim(-55, 20)

    if show_legend:
        scenario_handles = reduce_legend(df,ax,type_legend= ["mixed",color][marker=="+"])
        # Update the legend with only scenario labels
        ax.legend(scenario_handles.values(), scenario_handles.keys(), loc='lower left', fontsize='small')
    else:
        ax.legend().set_visible(False)

    if not x_label:
        plt.xlabel('')
    if not y_label:
        plt.ylabel('')

    if zoom:
        # create a zoom
        # Create an inset axes that zooms in on a specific region
        axins = zoomed_inset_axes(ax, zoom=4, loc='upper right')  # zoom factor and location
        df.plot.scatter(x=rename_dict['variable']["-Inequality index|Consumption Gini"], y=rename_dict['variable']["Expenditure|Household"], color=color,  marker=marker, ax=axins)

        # Specify the limits of the zoomed area
        x1, x2, y1, y2 = -1, 0.5, -5, 2  # Adjust these values as needed
        axins.set_xlim(x2, x1)
        axins.set_ylim(y1, y2)
        axins.legend().set_visible(False)
        axins.set_xticklabels([])
        axins.set_yticklabels([])
        axins.set_xlabel('')
        axins.set_ylabel('')
        axins.axhline(0, color='midnightblue', linewidth=1.2)  # Highlight y=0
        axins.axvline(0, color='midnightblue', linewidth=1.2)  # Highlight x=0

        mark_inset(ax, axins, loc1=2, loc2=4, fc="none", ec="0.5", linestyle='--')

    plt.savefig(output_fig + "Equity_efficiency_nuage_"+title+".png")
    return 0


def figA_plot_all_nuage_subplot(df, var_x, var_y, title, rename_dict=None, mode="color_model", ymax=None, ymin=None, do_zoom=True, year2filter=None):

    df = df.rename(rename_dict)
    df = df.filter(year=[y for y in df.year if y >= 2025])
    if year2filter is not None:
        df = df.filter(year=year2filter)

    plt.clf()
    plt.cla()

    # subplots All and by regions
    nb_col = 3
    nb_row = 2

    fig, axs = plt.subplots(nb_row, nb_col)

    plt.subplots_adjust(top=0.9, bottom=0.1, right=0.9,left=0.1)

    fig.set_dpi(dpi)
    #fig.set_figheight(12)
    #fig.set_figwidth(12)
    fig.set_figheight(8)
    fig.set_figwidth(16)


    #for i, reg in enumerate(["All regions","Brazil","China","India","Europe","USA"]):
    #for i, reg in enumerate(["All regions","USA","Europe","China","Brazil","India"]):
    for i, reg in enumerate(["All regions","India","China","Brazil","USA","Europe"]):
        j = i // nb_col # rest
        k = i % nb_col # dividende
        axs[j,k].set_title( reg, fontsize=18)
        y_label = [True,False, False][k]
        if j == nb_row-1:
            x_label = True
        else:
            x_label = False
        if reg=="All regions":
            df2plot = df
        else:
            df2plot = df.filter( region=reg)

        #print("HERE", df2plot.variable
        if mode=="color_model":
            df2plot.plot.scatter( x=rename_dict['variable'][var_x], y=rename_dict['variable'][var_y], ax=axs[j,k], color="model", marker="scenario")
        if mode=="color_scenario":
            df2plot.plot.scatter( x=rename_dict['variable'][var_x], y=rename_dict['variable'][var_y], ax=axs[j,k], color="scenario", marker="model")
        
        if reg != "All regions":
            if ymin is not None and ymax is not None:
                axs[j,k].set_ylim(ymin[reg], ymax[reg])
            elif ymin is not None:
                axs[j,k].set_ylim(ymin[reg])
            elif ymax is not None:
                axs[j,k].set_ylim( ymax[reg])

        if x_label==True:
             axs[j, k].xaxis.label.set_size(18)
        if y_label==True:
             axs[j, k].yaxis.label.set_size(22)

        # cutom legend
        axs[j,k].legend( loc='lower right', fontsize='small')
        # Highlight the x=0 and y=0 axes
        axs[j,k].axhline(0, color='midnightblue', linewidth=1.2)  # Highlight y=0
        axs[j,k].axvline(0, color='midnightblue', linewidth=1.2)  # Highlight x=0

        #if reg=="All regions":
        if reg=="Brazil":
            scenario_handles = reduce_legend(df2plot,axs[j,k],type_legend = "mixed")
            # Update the legend with only scenario labels
            axs[j,k].legend(scenario_handles.values(), scenario_handles.keys(), loc='lower center', fontsize='small')
            legend_handles = []
            handles, labels = axs[j,k].get_legend_handles_labels()
            if mode=="color_model": # legend when model are in colors
                for label, handle in scenario_handles.items():
                    if label in ['Labor Tax Cuts', 'Lump Sum Transfers']:  
                        legend_handles.append( mlines.Line2D([], [], color='black', marker=marker_map_scenario[label], linestyle='None', label=label))
                    else:
                        for km in color_map_model.keys():
                            if km in label:
                                color = colors_pyam[color_map_model[km]]
                        legend_handles.append(  mpatches.Patch(color='none', label=label) )

                axs[j,k].legend(handles=legend_handles)
                legend = axs[j,k].legend(handles=legend_handles, bbox_to_anchor=(3.2, -0.2), ncol=6, fontsize=16)
                i=0
                for label, handle in scenario_handles.items():
                    if not label in ['Labor Tax Cuts', 'Lump Sum Transfers']:
                        for km in color_map_model.keys():
                            if km in label:
                                color = colors_pyam[color_map_model[km]]
                        legend.texts[i].set_color(color)
                    i+=1

            if mode=="color_scenario": # legend when scenarios are in colors
                for label, handle in scenario_handles.items():
                    if label in ['Labor Tax Cuts', 'Lump Sum Transfers']:  
                        for km in color_map_scenario.keys():
                            if km in label:
                                color = colors_pyam[color_map_scenario[km]]
                        legend_handles.append(  mpatches.Patch(color='none', label=label) )
                    else:
                        legend_handles.append( mlines.Line2D([], [], color='black', marker=marker_map_model[label], linestyle='None', label=label))

                #axs[j,k].legend(handles=legend_handles)
                axs[j,k].legend(handles=legend_handles)
                legend = axs[j,k].legend(handles=legend_handles, bbox_to_anchor=(3.4, -0.2), ncol=6, fontsize=16)
                i=0
                for label, handle in scenario_handles.items():
                    if label in ['Labor Tax Cuts', 'Lump Sum Transfers']:
                        for km in color_map_scenario.keys():
                            if km in label:
                                color = colors_pyam[color_map_scenario[km]]
                        legend.texts[i].set_color(color)
                    i+=1

        else:
            axs[j,k].legend().set_visible(False)

        if not x_label:
            axs[j,k].set_xlabel('')
        if not y_label:
            axs[j,k].set_ylabel('')

        if reg=="All regions" and do_zoom==True:# or reg=="India":
            # create a zoom
            # Create an inset axes that zooms in on a specific region
            axins = zoomed_inset_axes(axs[j,k], zoom=3, loc='upper right')  # zoom factor and location
            if mode=="color_model": # legend when scenarios are in colors
                df2plot.plot.scatter(x=rename_dict['variable'][var_x], y=rename_dict['variable'][var_y], color="model", marker="scenario", ax=axins, s=14)
            if mode=="color_scenario": # legend when scenarios are in colors
                df2plot.plot.scatter(x=rename_dict['variable'][var_x], y=rename_dict['variable'][var_y], color="scenario", marker="model", ax=axins, s=14)

            # Specify the limits of the zoomed area
            if reg=="All regions":
                x1, x2, y1, y2 = -0.5, 0.5, -4, 2  # Adjust these values as needed
            if reg=="India":
                x1, x2, y1, y2 = 2, 4, -2, 0.5  # Adjust these values as needed
            #axins.set_xlim(x2, x1)
            axins.set_xlim(x1, x2)
            axins.set_ylim(y1, y2)
            axins.legend().set_visible(False)
            axins.set_xticklabels([])
            axins.set_yticklabels([])
            axins.set_xlabel('')
            axins.set_ylabel('')
            axins.axhline(0, color='midnightblue', linewidth=1.2)  # Highlight y=0
            axins.axvline(0, color='midnightblue', linewidth=1.2)  # Highlight x=0

            mark_inset(axs[j,k], axins, loc1=2, loc2=4, fc="none", ec="0.5", linestyle='--')

    plt.savefig(output_fig + title + ".pdf", dpi=dpi, bbox_inches='tight')
    return 0


def plot_losses_emi(df2plot, df2plot_y, var, sc_v, rename_dict=None):

    plt.clf()
    plt.cla()
    #plt.style.use('seaborn')  # Use a clean style

    fig = plt.figure(figsize=(10, 10), dpi=dpi)  # Increase figure size and resolution

    gs = gridspec.GridSpec(2, 2)
    axs = []

    nb_col = 2
   
    df2plot = pyam.concat( [df2plot, df2plot_y])
    df2plot = df2plot.rename({'variable':rename_dict})
    list_model = [m for m in df2plot.model if m != 'IMACLIM-R']
    list_model = [m for m in df2plot.model]
    for i, model in enumerate( list_model):
        print(model)
        j = i // nb_col
        k = i % nb_col
        axs.append(fig.add_subplot(gs[j,k]))

        df = df2plot.filter(model=model)
        x_window = np.max(df.filter(variable=rename_dict["Emissions_Capita"]).timeseries().values) - np.min(df.filter(variable=rename_dict["Emissions_Capita"]).timeseries().values)
        y_window = np.max(df.filter(variable=rename_dict["Expenditure|Household"]).timeseries().values) - np.min(df.filter(variable=rename_dict["Expenditure|Household"]).timeseries().values)
        fact = 1/20
        x_f = fact * x_window
        y_f = fact * y_window
        #df.plot.scatter(x='Emissions_Capita', y='Expenditure|Household', color="region", ax=axs[i], title=None, linewidth=0.6)
        print(model, fact, x_f, y_f, x_window, y_window)
        for r in df.region:
            df_r = df.filter(region=r)
            df_r.plot.scatter(x=rename_dict['Emissions_Capita'], y=rename_dict['Expenditure|Household'], color=color_map_region[r], ax=axs[i], title=None, linewidth=0.6, with_lines=True)
            #xmin = np.min( df_r.filter(variable="Emissions_Capita").timeseries().values)
            #ymin = np.min( df_r.filter(variable="Expenditure|Household").timeseries().values)
            xmin = df_r.filter(variable=rename_dict["Emissions_Capita"]).timeseries().values[0,-1]
            ymin = df_r.filter(variable=rename_dict["Expenditure|Household"]).timeseries().values[0,-1]
            plt.text( xmin-x_f, ymin-y_f, r, fontsize=8, color=color_map_region[r])
            #df_r.plot(x='Emissions_Capita', y='Expenditure|Household', color=color_map_region[r], ax=axs[i], title=None, linewidth=0.6)
        #df.plot.scatter(x='Emissions_Capita', y='Expenditure|Household', ax=axs[i], title=None, linewidth=0.6)
        if i <=-1:
            axs[i].legend().set_visible(False)
        #axs[i].set_xticklabels(['']+order_region+[''], rotation=45, ha='right')
        #axs[i].set_title( titles[i])

    fig.tight_layout(pad=1.0)
    plt.savefig(output_fig + var.replace(" ", "_").replace("|", "_") + sc_v + ".pdf", dpi=dpi, bbox_inches='tight')
    return 0

def compute_max_min(df_pyam,a,b):
    frame_a = df_pyam.filter(variable=a).timeseries().values
    frame_b = df_pyam.filter(variable=b).timeseries().values
    y_max = np.max(np.max(np.concatenate( (frame_a + frame_b, frame_a), axis=1), axis=1))
    y_min = np.min(np.min(np.concatenate( (frame_a + frame_b, frame_a), axis=1), axis=1))
    return y_min, y_max

def fig_C_plotting(df_in, year, scenario, figname, ymin_arg=None, ymax_arg=None):
    list_var = [v for v in df_in.variable if 'only' in v]
    a = list_var[1]
    b = list_var[0]
    data = df_in.filter( region=[s for s in df_in.region if not 'Africa'==s], year=year, variable=list_var, scenario=scenario)        
    # compute min and max
    ymin, ymax = compute_max_min(data,a,b)
    if ymin_arg is not None:
        ymin = ymin_arg
        ymax = ymax_arg
    # continue formating
    data = data.timeseries()
    data = pd.pivot_table(data, values=2040, index=['model', 'region'], columns='variable').reset_index()
    # Sample data
    """
    data = {
        'region': ['Region1', 'Region1', 'Region2', 'Region2'],
        'model': ['ModelA', 'ModelB', 'ModelA', 'ModelB'],
        'a': [10, 20, 15, 25],
        'b': [5, 10, 10, 15]
    }
    """
    # Create a DataFrame
    df = pd.DataFrame(data)

    # Pivot the DataFrame to have 'region' and 'model' as multi-index columns
    pivot_df = df.melt(id_vars=['region', 'model'], value_vars=list_var, var_name='variable', value_name='value')

    # Pivot again to get the desired structure for plotting
    pivot_df = pivot_df.pivot_table(index=['region', 'model'], columns='variable', values='value', aggfunc='sum').reset_index()

    # Sort the DataFrame by 'region' and 'model'
    pivot_df = pivot_df.sort_values(by=['region', 'model'])

    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))

    # Get unique regions and models
    regions = pivot_df['region'].unique()
    models = pivot_df['model'].unique()

    # Number of models
    n_models = len(models)

    # Define the width of each bar and the space between bars
    # One region lays within 1 units. We take 80% of this, with space between bars being alpha the width of bars
    alpha = 1 / 3.5
    x = 0.7 / (n_models + (n_models-1) * alpha)
   
    bar_width = x
    space = x * alpha  # Space between bars of different models

    bar_width_b = x / 2 
    space_b = x * alpha + x / 2  # Space between bars of different models

    # Create an array for the x-axis positions
    index = np.arange(len(regions))

    # Plot the stacked bar plot for each model
    for i, model in enumerate(models):
        model_data = pivot_df[pivot_df['model'] == model]
        bars_a = ax.bar(index + i * (bar_width + space), model_data[a], bar_width, color='skyblue', hatch='\\', edgecolor='black', label=a if i == 0 else "")
        #bars_b = ax.bar(index + i * (bar_width + space), model_data[b], bar_width, bottom=model_data[a], color='skyblue', hatch='\\', edgecolor='black', label=f'{model} - b' if i == 0 else "")
        bars_b = ax.bar(index + i * (bar_width_b + space_b) + x/4, model_data[b], bar_width_b, bottom=model_data[a], color='lightcoral', hatch='//', edgecolor='black', label=b if i == 0 else "")

    # Set the x-axis labels to show region only once
    if False:
        x_ticks = np.arange(len(regions)) + (n_models - 1) * (bar_width + space) / 2
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(regions)
    else:
        ax.set_xticks([])
        ax.set_xticklabels([])

    # Add model labels above each region label
    plt.subplots_adjust(bottom=0.2) 
    for i, region in enumerate(regions):
        region_data = pivot_df[pivot_df['region'] == region]
        for j, model in enumerate(region_data['model']):
            ax.text(i + j * (bar_width + space) -x , ymin -20, model, ha='center', va='top', rotation=45, fontsize=8)

    # Add region labels lower to avoid overlap
    if True:
        for i, region in enumerate(regions):
            ax.text(i + (n_models - 1) * (bar_width + space) / 2, ymin - 35 -20, region, ha='center', va='top')

    # Add labels and title
    #ax.set_xlabel('Region')
    ax.set_ylabel(r'Gini scenario - Gini baseline (\% of effect)')
    ax.set_ylim(bottom = ymin -15, top = ymax * 1.1)
    #ax.set_title('Stacked Bar Plot by Region and Model')

    # Add a legend
    ax.legend(loc='lower right')

    plt.savefig(output_fig+figname+".pdf")
