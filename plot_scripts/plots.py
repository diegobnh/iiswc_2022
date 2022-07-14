from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import glob
import sys
import math
import os

'''
So two types of plots we have:
(1) specific plots of each app/dataset (single_application)
(2) plots including info of all app/dataset (multi_application)

The second type of plot can only be executed after having executed the first one before at least once.

'''

if len(sys.argv) > 1:
    type_of_plot = sys.argv[1]
else:
    print("You should pass the type of plots: single_application or multi_application!")
    sys.exit(0)
    

g_labelpad_value = 8
g_fontsize_value = 8
g_virt_page_number_list = []
g_df_last_event_group = pd.DataFrame()


#Theses plots requires only the file track_info.csv
def plot_counters_and_cpu_and_memory_usage():
    #files = glob.glob('track_info/track_info_*.csv')
    files = glob.glob('track_info_*.csv')
    application_dataset = []
    for file in files:
        name = file.split('.')[0]
        app_dataset = name.split('_')[-2] + "_" + name.split('_')[-1]
       
        df = pd.read_csv(file)
        df.set_index('timestamp', inplace=True)

        df['dram_page_cache'] = df['dram_page_cache_active'] + df['dram_page_cache_inactive']
        df['pmem_page_cache'] = df['pmem_page_cache_active'] + df['pmem_page_cache_inactive']

        df['dram_page_cache']  = df['dram_page_cache']/1000000
        df['pmem_page_cache']  = df['pmem_page_cache']/1000000

        df['dram_page_cache'] = df['dram_page_cache'].round(2)
        df['pmem_page_cache'] = df['pmem_page_cache'].round(2)

        df['dram_app'] = df['dram_app']/1000
        df['pmem_app'] = df['pmem_app']/1000

        df['pgdemote_kswapd'] = df['pgdemote_kswapd'].diff().fillna(0)
        df['pgpromote_success'] = df['pgpromote_success'].diff().fillna(0)
        df['pgpromote_candidate'] = df['pgpromote_candidate'].diff().fillna(0)
        df['promote_threshold'] = df['promote_threshold'].diff().fillna(0)
        df['pgpromote_demoted'] = df['pgpromote_demoted'].diff().fillna(0)

        df['cpu_usage'] = df['cpu_usage'].clip(upper=100)
        
        fig = plt.figure()
        fig, axes = plt.subplots(figsize= (4,6),nrows=4,sharex=True, gridspec_kw = {'wspace':0.1, 'hspace':0.1})
    
        df[["dram_app","pmem_app"]].plot(ax=axes[0], linewidth=0.5)
        df[["dram_page_cache"]].plot(style='--', linewidth=0.5, ax=axes[0], color = 'Red')#linewidth=1.5,
        df[["pmem_page_cache"]].plot(style=':', linewidth=0.5, ax=axes[0], color = 'Black')#linewidth=1.5,
        axes[0].legend(['DRAM (App)','NVM (App)','DRAM (OS page cache)','NVM (OS page cache)'], prop={'size': 6}, fancybox=True, framealpha=0.5)

        #axes[0].set_ylabel('Memory Usage (GB)')

        df[["pgdemote_kswapd"]].plot(ax=axes[1],linewidth=0.5, marker = 'o', ms = 0.75, linestyle='none')
        axes[1].legend(prop={'size': 6})
        #axes[1].set_ylabel('pgdemote_kswapd')

        df[["pgpromote_success"]].plot(ax=axes[2],linewidth=0.5,marker = 'o', ms = 0.75, linestyle='none')
        axes[2].legend(prop={'size': 6})
        #axes[2].set_ylabel('pgpromote_success')
        
        #df2[['DRAM_access']].plot(ax=axes[3],marker = 'o', ms = 0.75, linestyle='none') #color='tab:orange')
        #axes[3].legend(['DRAM accessed'],prop={'size': 6})
        
        df[['cpu_usage']].plot(ax=axes[3],linewidth=0.5,marker = 'o', ms = 0.75, linestyle='none')
        axes[3].get_legend().remove()
        #axes[3].yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=None, symbol='%', is_latex=False))
        axes[3].legend(prop={'size': 6})
        #axes[3].set_ylabel('CPU Usage')
        
        #axes[5].set_xticks([])
        axes[3].tick_params(axis='x', rotation=45)
        axes[3].set_xlabel('Timestamp(seconds)')
        
        filename = "memory_and_cpu_usage_and_counters_" + app_dataset + ".pdf"

        plt.savefig(filename, bbox_inches="tight")
        plt.clf()
#Theses plots requires only the file memory_trace_app_name.csv. In this file we have all samples for example , L1, L2, PMEM, DRAM..
def plot_distribution_access_on_different_mem_levels(app_dataset):
    filename = "memory_trace_" + app_dataset + ".csv"

    headers=  ['timestamp','virt_addr','mem_level','access_weight','thread_rank','phy_addr', 'tlb', 'access_type']

    df_mem_samples = pd.read_csv(filename, names=headers,low_memory=False)

    #remove any empty row
    df_mem_samples.dropna(inplace=True)
    
    df = df_mem_samples.mem_level.value_counts(normalize=True).mul(100).round(2).rename_axis('Memory Level').reset_index(name='Number of Samples')
    #print(df)
    df2 = df[df['Memory Level'].str.contains("hit")]
    df2.sort_values(by=['Memory Level'], ascending=True, inplace=True)
    
    df2['Memory Level'] = df2['Memory Level'].str.replace('_hit','')
    df2['Memory Level'] = df2['Memory Level'].str.replace('Ram','RAM')
    
    df_DRAM_PMEM = df2[df2['Memory Level'].str.contains('RAM|PMEM', regex= True, na=False)]
    filename = "perc_access_pmem_dram_" + app_dataset + ".csv"
    df_DRAM_PMEM.to_csv(filename,index=False)
    
    df2.set_index('Memory Level', inplace=True)
    
    NUM_COLORS = df2.shape[0]
    cmap = plt.get_cmap('nipy_spectral')
    colors = [cmap(i) for i in np.linspace(0, 1, NUM_COLORS)]
    
    
    ax = df2.plot.bar(color=[colors],legend=False, figsize=(3,2))
    vals = ax.get_yticks()
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=None, symbol='%', is_latex=False))
    
    for p in ax.patches:
        ax.annotate(format(p.get_height(), '.1f'), (p.get_x() + p.get_width() / 2., p.get_height()), rotation=90,ha = 'center', va = 'center',size=6,xytext = (0, 10), textcoords = 'offset points')
        ax.spines['top'].set_visible(False)
    
    plt.tick_params(axis='x', which='major', labelsize=8)
    plt.tick_params(axis='y', which='major', labelsize=8)
    plt.xticks(rotation=45,ha='right', fontsize=8)
    plt.xlabel('Memory Level', fontsize=8)
    plt.ylabel('Percentage of Samples', fontsize=8)
    plt.tight_layout(pad=1.0)
    plt.tick_params(axis='both', which='minor', labelsize=8)
    filename = "distribution_access_" + app_dataset +".pdf"
    plt.savefig(filename)
    plt.clf()
#Theses plots requires the outputs (perfmem_trace_mapped_DRAM_ap_name.csv AND perfmem_trace_mapped_PMEM_ap_name.csv) from mapping.py
def generate_access_frequency_per_object(app_dataset, df_DRAM, df_PMEM):
    df = df_DRAM.append(df_PMEM, ignore_index = True)
    df_normalized = df['call_stack_hash'].value_counts(normalize=True).mul(100).round(2).rename_axis('call_stack_hash').reset_index(name='perc_access')
    filename = "access_frequency_per_obj_"+ app_dataset + ".csv"
    df_normalized.to_csv(filename, index=False)

    dram_normalized = df_DRAM['call_stack_hash'].value_counts(normalize=True).mul(100).round(2).rename_axis('call_stack_hash').reset_index(name='perc_access')
    dram_real = df_DRAM['call_stack_hash'].value_counts(normalize=False).rename_axis('call_stack_hash').reset_index(name='num_access')
    dram = pd.merge(dram_normalized, dram_real, how="inner", on=["call_stack_hash"])
    filename = "access_frequency_per_obj_in_DRAM_"+ app_dataset + ".csv"
    dram.to_csv(filename, index=False)
    
    pmem_normalized = df_PMEM['call_stack_hash'].value_counts(normalize=True).mul(100).round(2).rename_axis('call_stack_hash').reset_index(name='perc_access')
    pmem_real = df_PMEM['call_stack_hash'].value_counts(normalize=False).rename_axis('call_stack_hash').reset_index(name='num_access')
    pmem = pd.merge(pmem_normalized, pmem_real, how="inner", on=["call_stack_hash"])
    filename = "access_frequency_per_obj_in_PMEM_"+ app_dataset + ".csv"
    pmem.to_csv(filename, index=False)
def plot_touches_per_page(app_dataset, df_DRAM, df_PMEM):
    df = df_DRAM.append(df_PMEM, ignore_index = True)
    
    df['virt_page_number'] = df['virt_addr'].apply(lambda x: int(x, 16) >> 12)
    df_touches_per_pages = df['virt_page_number'].value_counts().rename_axis('pages').reset_index(name='touches')
    #print(df_touches_per_pages)

    labels = ['1 touch', '2 touches', '3-6 touches', '6-10 touches','+10 touches']
    max = df_touches_per_pages['touches'].max() + 1
    df['category'] = pd.cut(x=df_touches_per_pages['touches'], bins=[1,2,3,6,10,max],labels=labels, right=False)
    #sort_index avoid to sort based on value_counts
    df_group_of_touches = df['category'].value_counts(normalize=True).sort_index().mul(100).round(1).rename_axis('category').reset_index(name='percentual of samples')
    
    
    df_touch_per_page = df_group_of_touches[df_group_of_touches['category'].str.contains('1|2', regex= True, na=False)]
    filename = "df_touch_per_page_" + app_dataset + ".csv"
    df_touch_per_page.to_csv(filename,index=False)

    df_group_of_touches.set_index('category', inplace=True)
    #print(df_group_of_touches)

    ax = df_group_of_touches.plot(kind="bar", figsize=(4,2), legend=False)
    for p in ax.patches:
        ax.annotate(format(p.get_height(), '.1f'), (p.get_x() + p.get_width() / 2., p.get_height()), rotation=90,ha = 'center', va = 'center',size=8,xytext = (0, 10), textcoords = 'offset points')

    # Hide the right and top spines
    ax.tick_params(top=False)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=None, symbol='%', is_latex=False))
    output = "touches_per_page_outside_from_cache_" + app_dataset + ".pdf"
    plt.ylabel("Percentage of Samples")
    plt.xlabel("Distribution of Page Groups")
    plt.xticks(rotation=45, ha='center')
    plt.savefig(output,dpi=300, bbox_inches="tight")
    plt.clf()
def analysis_outside_from_cache(app_dataset, df_DRAM, df_PMEM):
    original_stdout = sys.stdout
    with open('analysis_samples_outside_from_cache.txt', 'w') as f:
        sys.stdout = f
    
        print("#########")
        print(app_dataset)
        print("#########")
        
        df_DRAM['virt_page_number'] = df_DRAM['virt_addr'].apply(lambda x: int(x, 16) >> 12)
        df_DRAM['physical_page_number'] = df_DRAM['phys_addr'].apply(lambda x: int(x, 16) >> 12)
        
        df_PMEM['virt_page_number'] = df_PMEM['virt_addr'].apply(lambda x: int(x, 16) >> 12)
        df_PMEM['physical_page_number'] = df_PMEM['phys_addr'].apply(lambda x: int(x, 16) >> 12)
        
        print("DRAM_samples:", round(df_DRAM.shape[0]/(df_DRAM.shape[0]  + df_PMEM.shape[0] ) * 100 ,2),"%")
        print("PMEM_samples:", round(df_PMEM.shape[0]/(df_DRAM.shape[0]  + df_PMEM.shape[0] ) * 100 ,2),"%")

        total_external_access_cost = df_DRAM["access_weight"].sum() + df_PMEM["access_weight"].sum()
        dram_access_cost = 100 * (df_DRAM.access_weight.sum()/total_external_access_cost)
        pmem_access_cost = 100 * (df_PMEM.access_weight.sum()/total_external_access_cost)

        print("\nTotal DRAM cost (sum weight latency):", round(dram_access_cost,2),"%")
        print("Total PMEM cost (sum weight latency):", round(pmem_access_cost,2),"%")
        
        pd.set_option('display.float_format', lambda x: '%.2f' % x)
        df_dram_tlb_hit = df_DRAM.loc[df_DRAM.tlb == "TLB_hit"]
        df_dram_tlb_miss = df_DRAM.loc[df_DRAM.tlb == "TLB_miss"]
        print("\nDRAM ratio TLB hit:", round((df_dram_tlb_hit.shape[0]/df_DRAM.shape[0])*100,2),"%")
        print("DRAM ratio TLB miss:", round((df_dram_tlb_miss.shape[0]/df_DRAM.shape[0])*100,2),"%")
        print("\nDRAM TLB hit mean cost:",round(df_dram_tlb_hit.access_weight.mean(),2))
        print("DRAM TLB miss mean cost:",round(df_dram_tlb_miss.access_weight.mean(),2))
        
        df_pmem_tlb_hit = df_PMEM.loc[df_PMEM.tlb == "TLB_hit"]
        df_pmem_tlb_miss = df_PMEM.loc[df_PMEM.tlb == "TLB_miss"]
        print("\nPMEM ratio TLB hit:", round((df_pmem_tlb_hit.shape[0]/df_PMEM.shape[0])*100,2),"%")
        print("PMEM ratio TLB miss:", round((df_pmem_tlb_miss.shape[0]/df_PMEM.shape[0])*100,2),"%")
        print("\nPMEM TLB hit mean cost:",round(df_pmem_tlb_hit.access_weight.mean(),2))
        print("PMEM TLB miss mean cost:",round(df_pmem_tlb_miss.access_weight.mean(),2))
        
        page_number_types = ["virt_page_number", "physical_page_number"]
        for page_number in page_number_types:
            print("\nType of page number:", page_number)
            
            #count how many access per page
            df_DRAM_and_PMEM = pd.concat([df_DRAM, df_PMEM], ignore_index=True)
            df_access_per_page = df_DRAM_and_PMEM[page_number].value_counts().reset_index()
            df_access_per_page.columns = [page_number, 'total_access']

            #filter pages with access at least two access
            df_at_least_two_access = df_access_per_page.loc[df_access_per_page.total_access > 1]
            print("Ratio (DRAM and PMEM):", round((df_at_least_two_access.shape[0]/df_access_per_page.shape[0])*100,2), "% outside from cache with more than one touch")
            
            df_access_per_page = df_DRAM[page_number].value_counts().reset_index()
            df_access_per_page.columns = [page_number, 'total_access']
            df_at_least_two_access = df_access_per_page.loc[df_access_per_page.total_access > 1]
            print("Ratio (DRAM):", round((df_at_least_two_access.shape[0]/df_access_per_page.shape[0])*100,2), "% outside from cache with more than one touch")

            df_access_per_page = df_PMEM[page_number].value_counts().reset_index()
            df_access_per_page.columns = [page_number, 'total_access']
            df_at_least_two_access = df_access_per_page.loc[df_access_per_page.total_access > 1]
            print("Ratio (PMEM):", round((df_at_least_two_access.shape[0]/df_access_per_page.shape[0])*100,2), "% outside from cache with more than one touch")

        print("-------------------------------------------------------------------------------------")
        sys.stdout = original_stdout
def decide_static_mapping_between_DRAM_and_PMEM(app_dataset, df_DRAM, df_PMEM):
    original_stdout = sys.stdout # Save a reference to the original standard output
    with open('static_mapping.txt', 'w') as f:
        sys.stdout = f
        
        df = df_DRAM.append(df_PMEM, ignore_index = True)

        df_access = df['call_stack_hash'].value_counts(normalize=True).mul(100).round(2).reset_index()
        df_access.columns = ['call_stack_hash', 'perc_access']

        filename = "mmap_trace_mapped_" + app_dataset + ".csv"
        df_mmap = pd.read_csv(filename)

        df_num_alloc = df_mmap.groupby("call_stack_hash")['size_allocation'].count().to_frame(name="num_alloc").reset_index()

        df_size = df_mmap.groupby("call_stack_hash")['size_allocation'].first().to_frame(name="size").reset_index()
        df_size['size'] = df_size['size']/1e9

        df = pd.merge(df_access, df_size, on="call_stack_hash")
        df = pd.merge(df, df_num_alloc, on="call_stack_hash")

        df['metric'] = df['perc_access']/df['size']
        df.sort_values(by='metric', ascending=False, inplace=True)

        #print(df)

        dram_list=[]
        pmem_list=[]
        dram_capacity = 190
        for index, row in df.iterrows():
            if (dram_capacity - row['size']) > 0:
                dram_capacity = dram_capacity - row['size']
                dram_list.append(row['call_stack_hash'])
            else:
                pmem_list.append(row['call_stack_hash'])
        print("Algoritmo do Paper:")
        print("-------------------")
        print("Objects to DRAM:")
        print(dram_list)
        print("Objects to PMEM:")
        print(pmem_list)
        
        
        dram_list=[]
        pmem_list=[]
        for index, row in df.iterrows():
            if (row['size']) < 100:
                dram_list.append(row['call_stack_hash'])
            else:
                pmem_list.append(row['call_stack_hash'])
        print("\nShared Library Mapping:")
        print("-------------------------")
        print("Objects to DRAM:")
        print(dram_list)
        print("Objects to PMEM:")
        print(pmem_list)
        sys.stdout = original_stdout ## Reset the standard output to its original value

def _plot_objects(app_dataset):
    memory_types = ["dram", "pmem"]
    for mem in memory_types:
        filename = mem + "_obj_index_to_freq_" + app_dataset + ".csv"
        df = pd.read_csv(filename)
        ax0 = df['perc_access'].plot(kind="bar",figsize=(4, 2))
        ax1 = ax0.twinx()
        df['num_access'].plot(kind= 'line', color= 'black', ax=ax1,style='.-',linestyle='dashed')
        ax1.set_xticks(range(df.ID.count())). #to force xticks keep unordered
        _ = ax1.set_xticklabels(df.ID)

        ax0.legend(['% of accesses'], prop={'size': 8})
        ax1.legend(['# of accesses'], prop={'size': 8}, loc='upper left', bbox_to_anchor=(0.59, 0.8))
        ax0.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0, symbol='%', is_latex=False))
        
        if mem == "pmem":
            ax0.annotate('19.8 milions', xy=(0.3, 65),xytext=(2, 60),arrowprops=dict(arrowstyle='->',lw=0.75), fontsize=7)
        else:
            ax0.annotate('16.4 milions', xy=(0.42, 25),xytext=(1.3, 24),arrowprops=dict(arrowstyle='->',lw=0.75), fontsize=7)


        ax0.tick_params(axis='x', rotation=45)
        ax0.set_xlabel('Object ID')
        filename = "access_frequency_per_obj_in_" + mem + "_"+ app_dataset + ".pdf"
        plt.savefig(filename,dpi=300, bbox_inches='tight', format='pdf')
        plt.clf()
        
def plot_number_of_access_per_object_outside_from_cache(app_dataset):
    filename = "access_frequency_per_obj_in_DRAM_"+ app_dataset + ".csv"
    df_dram = pd.read_csv(filename)
    filename = "access_frequency_per_obj_in_PMEM_"+ app_dataset + ".csv"
    df_pmem = pd.read_csv(filename)
    df_dram['type'] = "dram"
    df_pmem['type'] = "pmem"

    df = df_dram.append(df_pmem,ignore_index = True)
    df['ID']=pd.factorize(df.call_stack_hash)[0]
    df_dram = df.loc[df.type == "dram"]
    df_pmem = df.loc[df.type == "pmem"]

    df_dram.set_index('ID', inplace=True)
    df_dram.drop('call_stack_hash', axis=1, inplace=True)
    df_dram.drop('type', axis=1, inplace=True)
    df_dram = df_dram.head(10)
    filename = "dram_obj_index_to_freq_" + app_dataset + ".csv"
    df_dram.to_csv(filename, index=True)

    df_pmem.drop('call_stack_hash', axis=1, inplace=True)
    df_pmem.drop('type', axis=1, inplace=True)
    df_pmem.set_index('ID', inplace=True)
    df_pmem = df_pmem.head(10)
    filename = "pmem_obj_index_to_freq_" + app_dataset + ".csv"
    df_pmem.to_csv(filename, index=True)

    _plot_objects(app_dataset)

def analysis_only_two_touches_per_page(app_dataset, df_PMEM):

    filename = "access_frequency_per_obj_in_PMEM_" + app_dataset + ".csv"
    df = pd.read_csv(filename)
    call_stack_hash = df['call_stack_hash'].values[0]  #get top 1 from PMEM
        
    filename = "mmap_trace_mapped_" + app_dataset + ".csv"
    df_mmap = pd.read_csv(filename)
    df_mmap = df_mmap.loc[df_mmap.call_stack_hash == call_stack_hash]
    df_mmap['size_allocation'] = df_mmap['size_allocation']/1e9
    df_mmap['size_allocation'] = df_mmap['size_allocation'].round(2)
    #print("#----------------------------------------------------------------------------------------------#")
    #print("Size(GB):", df_mmap['size_allocation'].values[0]," Lifetime(mean):", round(df_mmap['lifetime'].mean(),2),"(sec) Relative Lifetime(%):", df_mmap['relative_lifetime'].values[0], " Num Allocations", df_mmap.shape[0])
    
    #Here we are iterating each allocation from the same callstack
    for index, row in df_mmap.iterrows():
        star_timestamp = row['ts_event_start']
        end_timestamp = row['ts_event_end']
        
        #page_number_types = ["virt_page_number", "physical_page_number"]
        page_number_types = ["virt_page_number"]
        for page_number in page_number_types:
            df = df_PMEM
            
            mask = (df['ts_event'] >= star_timestamp) & (df['ts_event'] <= end_timestamp) & (df['call_stack_hash'] == call_stack_hash)
            df = df.loc[mask]

            if page_number == "virt_page_number":
                df['virt_page_number'] = df['virt_addr'].apply(lambda x: int(x, 16) >> 12)
                df1 = df.groupby('virt_page_number').apply(lambda x: x['ts_event'].count()).to_frame(name="number_of_reaccess").reset_index()
                df2 = df.groupby('virt_page_number').apply(lambda x: x['ts_event'].max() - x['ts_event'].min()).to_frame(name = "diff_max_and_min_ts_event").reset_index()
                df = pd.merge(df1, df2, on="virt_page_number")

            else:
                df['physical_page_number'] = df['phys_addr'].apply(lambda x: int(x, 16) >> 12)
                df1 = df.groupby('physical_page_number').apply(lambda x: x['ts_event'].count()).to_frame(name="number_of_reaccess").reset_index()
                df2 = df.groupby('physical_page_number').apply(lambda x: x['ts_event'].max() - x['ts_event'].min()).to_frame(name = "diff_max_and_min_ts_event").reset_index()
                df = pd.merge(df1, df2, on="physical_page_number")

            
            #print("Type of Page Number:",page_number, "\nType of Memory:", type_of_mem, "\nCall stack:", call_stack_hash)
            df_touches_per_pages = df['number_of_reaccess'].value_counts(normalize=True).mul(100).round(2).rename_axis('touch_per_pages').reset_index(name='percentage')

            df = df.loc[(df['diff_max_and_min_ts_event'] > 0)]
            df = df.loc[(df['number_of_reaccess'] == 2)]
            df_describe = df['diff_max_and_min_ts_event'].describe().to_frame().reset_index()
            df_describe.columns = ['percentis', 'values']
            
            filename = "percentis_"+ app_dataset + ".csv"
            df_describe.to_csv(filename, index=False)
            
            #print("\nOnly two access per page : Interval between theses two access")
            #category = ['until-1sec', '1-5sec', '5-10sec', '10-30sec','30-max'] #bc_kron
            #category = ['until-1sec', '1-2sec', '2-3sec', '3-max'] #cc_kron
            #max = df['diff_max_and_min_ts_event'].max() + 1
            #df['category'] = pd.cut(x=df['diff_max_and_min_ts_event'], bins=[0,1,2,3,max],labels=category)
            #df['category'] = pd.cut(x=df['diff_max_and_min_ts_event'], bins=10)
            #print(df['category'].value_counts(normalize=True).mul(100).round(1))
            
            #output = "box_plot_two_access_distance_" +  app_dataset  +".pdf"
            #plt.savefig(output,dpi=300, bbox_inches="tight")
            #plt.clf()
        break
def plot_statistics_to_pages_with_two_touches(app_dataset):
    files = glob.glob('track_info_*.csv')
    application_dataset = []
    for file in files:
        name = file.split('.')[0]
        app_dataset = name.split('_')[-2] + "_" + name.split('_')[-1]
     
        filename = "percentis_" + app_dataset + ".csv"
        df = pd.read_csv(filename)
        df = df[df["percentis"].str.contains("count")==False]
        #df.plot.scatter(x='percentis', y='values', figsize=(2,2), rot=60)
        df.set_index('percentis', inplace=True)
        df['values'].plot(kind='bar', rot=60, figsize=(2,2))
        output = "two_access_distance_" +  app_dataset  +".pdf"
        plt.ylabel("Distance (sec)")
        plt.xlabel("25%-ile")
        plt.savefig(output,dpi=300, bbox_inches="tight")
        plt.clf()

def plot_promotion_vs_dram_usage():
    files = glob.glob('track_info_*.csv')
    
    application_dataset = []
    for file in files:
       name = file.split('.')[0]
       app_dataset = name.split('_')[-2] + "_" + name.split('_')[-1]
       application_dataset.append(app_dataset)
    
    files.sort()
    application_dataset.sort()
    
    for filename,app_dataset in zip(files, application_dataset):
        file = "track_info_" + app_dataset  + ".csv"
        df_track = pd.read_csv(file) # nrows=1000)
        df_track['pgpromote_success'] = df_track['pgpromote_success'].diff().fillna(0)
        df_track['timestamp'] = df_track['timestamp'].astype(int)
        df1 = df_track.groupby('timestamp')['pgpromote_success'].sum().reset_index(name='pgpromote_success')
        #df_track.timestamp = pd.to_datetime(df_track.timestamp, unit='s')
        #df1 = df_track.resample('T', on='timestamp').pgpromote_success.sum().to_frame()
        
        file = "perfmem_trace_mapped_DRAM_" + app_dataset + ".csv"
        df_DRAM = pd.read_csv(file, low_memory=False) #nrows=1000)
        #print(df_DRAM.head(20))
        df_DRAM.columns = df_DRAM.columns.str.replace('ts_event', 'timestamp')
        df_DRAM['timestamp'] = df_DRAM['timestamp'].astype(int)
        df2 = df_DRAM.groupby(['timestamp']).size().reset_index(name='DRAM_access')
        #df_DRAM.timestamp = pd.to_datetime(df_DRAM.timestamp, unit='s')
        #df2 = df_DRAM.resample('T', on='timestamp').mem_level.count().to_frame() #.reset_index()
        #print(df2.head(20))

        df_merged = pd.merge(df1, df2, how="left", on=["timestamp"])
        #df_merge = pd.merge(df1, df2, how="left", on=["timestamp"])
        df_merged = df_merged.fillna(0)
        df_merged = df_merged.reset_index(drop=True)
        df_merged.set_index('timestamp', inplace=True)
            
        fig = plt.figure()
        fig, axes = plt.subplots(figsize= (6,4),nrows=2,sharex=True, gridspec_kw = {'wspace':0.1, 'hspace':0.1})

        df_merged[['DRAM_access']].plot(ax=axes[0],marker = 'o', ms = 0.75, linestyle='none', color='tab:orange')
        axes[0].legend(['DRAM samples accessed'])
        df_merged[['pgpromote_success']].plot(ax=axes[1],marker = 'o', ms = 0.75, linestyle='none')
        axes[1].legend(['pgpromote_success'])
        
        #axes[0].tick_params(axis='x', rotation=45)
        plt.xticks(rotation=45,ha='right')
        '''
        ax = df_merge.plot()
        ax.legend(["pgpromote_success", "Hits_on_DRAM"])
        ax.set_xticks([])
        plt.xlabel("Timestamp")
        plt.xticks([])
        '''
        output = "promoted_vs_access_" + app_dataset + ".pdf"
        plt.savefig(output,dpi=300, bbox_inches="tight")
        plt.clf()
def plot_access_pattern_top_object():
    '''
    We need to get before the info about top 1 acces in PMEM. So , run before the function plot_distribution_access_to_objects_outside_from_cache()
    '''
    flag_1_sec = True
    #files = glob.glob('mmap_trace_mapped/mmap_trace_mapped_*.csv')
    files = glob.glob('mmap_trace_mapped_*.csv')

    for file in files:
        call_stack_hash = 2117290442
        name = file.split('.')[0]
        
        app_dataset = name.split('_')[-2] + "_" + name.split('_')[-1]
        #filename = "mmap_trace_mapped/mmap_trace_mapped_" + app_dataset + ".csv"
        filename = "mmap_trace_mapped_" + app_dataset + ".csv"
        df_mmap = pd.read_csv(filename)
        df_mmap = df_mmap.loc[df_mmap.call_stack_hash == call_stack_hash]
        
        #Here we are iterating each allocation from the same callstack
        for index, row in df_mmap.iterrows():
            star_timestamp = row['ts_event_start']
            end_timestamp = row['ts_event_end']
            
            #filename = "perfmem_trace_mapped/perfmem_trace_mapped_PMEM_" + app_dataset + ".csv"
            filename = "perfmem_trace_mapped_PMEM_" + app_dataset + ".csv"
            df_pmem = pd.read_csv(filename)
            
            #filter specific call stack
            df_pmem = df_pmem.loc[df_pmem.call_stack_hash == call_stack_hash]
            #filter specific mmap because sevral allocations exist
            mask = (df_pmem['ts_event'] >= star_timestamp) & (df_pmem['ts_event'] <= end_timestamp)
            df_pmem = df_pmem.loc[mask]

            df_pmem['virt_page_number'] = df_pmem['virt_addr'].apply(lambda x: int(x, 16) >> 12)
            
            if flag_1_sec == True:
                time_range_to_plot = 1
                start_row_point = int(df_pmem.shape[0] * 0.20) #get position of 20% from execution time. Could be any values
                start_time = df_pmem.ts_event.values[start_row_point] #could be 0

                mask = ((df_pmem['ts_event'] >= start_time) & (df_pmem['ts_event']<= start_time + time_range_to_plot))
                df = df_pmem.loc[mask]
                ax = df.plot.scatter(x = 'ts_event', y = 'virt_page_number',marker='.', s=0.2)
                
                plt.xlabel("Timestamp",fontsize = 14, labelpad = 12)
                plt.ylabel("Page Number",fontsize = 14, labelpad = 14)
                plt.xticks(fontsize=14)
                plt.yticks(fontsize=14)
                filename = "top1_access_pattern_in_PMEM_" + app_dataset + "_1sec.pdf"
                plt.savefig(filename,dpi=300, bbox_inches='tight', format='pdf')
                plt.clf()
            else:
                #plot during all lifetime
                ax = df_pmem.plot.scatter(x = 'ts_event', y = 'virt_page_number',marker='.', s=0.2)
                #plt.ticklabel_format(axis="x", style="sci", scilimits=(0,0))
                #plt.locator_params(axis='x', nbins=2)
                #ax.xaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))
                plt.xlabel("Timestamp",fontsize = 14, labelpad = 12)
                plt.ylabel("Page Number",fontsize = 14, labelpad = 14)
                plt.xticks(fontsize=14)
                plt.yticks(fontsize=14)
                #just to delimited which region we zoom in
                start_row_point = int(df_pmem.shape[0] * 0.20)
                start_time = int(df_pmem.ts_event.values[start_row_point])
                plt.axvline(x=start_time, color='r', linestyle='--', linewidth=0.5)
                plt.axvline(x=start_time+1, color='r', linestyle='--', linewidth=0.5)
                #huge plot around 12MB
                #filename = "top1_access_pattern_in_PMEM_" + app_dataset + "_all_lifetime.pdf"
                #plt.savefig(filename,format='pdf', bbox_inches="tight")

                filename = "top1_access_pattern_in_PMEM_" + app_dataset + "_all_lifetime.png"
                plt.savefig(filename,dpi=900, format='png', bbox_inches="tight")
                plt.clf()

            sys.exit() #check only the first allocation
def analysis_over_two_touches_per_page(call_stack_hash, type_of_mem):
    #files = glob.glob('mmap_trace_mapped/mmap_trace_mapped_*.csv')
    files = glob.glob('mmap_trace_mapped_*.csv')
    
    for file in files:
        name = file.split('.')[0]
        
        app_dataset = name.split('_')[-2] + "_" + name.split('_')[-1]
        #filename = "mmap_trace_mapped/mmap_trace_mapped_" + app_dataset + ".csv"
        filename = "mmap_trace_mapped_" + app_dataset + ".csv"
        
        df_mmap = pd.read_csv(filename)
        df_mmap = df_mmap.loc[df_mmap.call_stack_hash == call_stack_hash]
        df_mmap['size_allocation'] = df_mmap['size_allocation']/1e9
        df_mmap['size_allocation'] = df_mmap['size_allocation'].round(2)
        print("#----------------------------------------------------------------------------------------------#")
        print("Size(GB):", df_mmap['size_allocation'].values[0]," Lifetime(mean):", round(df_mmap['lifetime'].mean(),2),"(sec) Relative Lifetime(%):", df_mmap['relative_lifetime'].values[0], " Num Allocations", df_mmap.shape[0])
        
        #Here we are iterating each allocation from the same callstack
        for index, row in df_mmap.iterrows():
            star_timestamp = row['ts_event_start']
            end_timestamp = row['ts_event_end']
            
            #page_number_types = ["virt_page_number", "physical_page_number"]
            page_number_types = ["virt_page_number"]
            for page_number in page_number_types:
                name = file.split('.')[0]
                app_dataset = name.split('_')[-2] + "_" + name.split('_')[-1]
                #filename = "perfmem_trace_mapped/perfmem_trace_mapped_DRAM_" + app_dataset + ".csv"
                filename = "perfmem_trace_mapped_" + type_of_mem + "_" + app_dataset + ".csv"
            
                df = pd.read_csv(filename)
                mask = (df['ts_event'] >= star_timestamp) & (df['ts_event'] <= end_timestamp) & (df['call_stack_hash'] == call_stack_hash)
                df = df.loc[mask]

                if page_number == "virt_page_number":
                    df['virt_page_number'] = df['virt_addr'].apply(lambda x: int(x, 16) >> 12)
                    df = df.groupby('virt_page_number').apply(lambda x: x['ts_event'].count()).to_frame(name="number_of_reaccess").reset_index()
                else:
                    df['physical_page_number'] = df['phys_addr'].apply(lambda x: int(x, 16) >> 12)
                    df = df.groupby('physical_page_number').apply(lambda x: x['ts_event'].count()).to_frame(name="number_of_reaccess").reset_index()
                
                print("Type of Page Number:",page_number, "\nType of Memory:", type_of_mem, "\nCall stack:", call_stack_hash)

                df = df.loc[(df['number_of_reaccess'] >= 2)]
                df_touches_per_pages = df['number_of_reaccess'].value_counts().rename_axis('touch_per_pages').reset_index(name='num_pages')
                print(df_touches_per_pages)

            break
def _check_intersection_between_dram_pmem_in_parallel(df_dram):
    count_pmem_and_dram=0
    count_only_pmem=0
    promoted=0
    demoted=0
    num_access=0
    global g_df_last_event_group
    
    for virt_page_number in g_virt_page_number_list:
        df_temp = df_dram.loc[df_dram.virt_page_number == virt_page_number]
        if not df_temp.empty:
            #print(df_temp.shape[0])
            #print(df_temp)
            count_pmem_and_dram+=1
            '''
            df_pmem = g_df_last_event_group.loc[g_df_last_event_group.virt_page_number == virt_page_number]
            ts_last_event_pmem = df_pmem['ts_event'].values[0]
            ts_first_event_dram = df_temp['ts_event'].values[0]
            if ts_first_event_dram > ts_last_event_pmem:
                promoted+=1
                #num_access = df.shape[0]
            else:
                demoted+=1
            '''
        else:
            count_only_pmem+=1

    #print("PMEM e DRAM:",count_pmem_and_dram, " Only PMEM:",count_only_pmem)
    data = [{'count_access_pmem_and_dram': count_pmem_and_dram, 'count_access_only_pmem': count_only_pmem}] #, 'count_promoted': promoted, 'count_demoted': demoted}]
    df_count = pd.DataFrame(data)
    
    return df_count
def analysis_intersection_between_dram_pmem_in_parallel():
    global g_virt_page_number_list
    
    #files = glob.glob('mmap_trace_mapped/mmap_trace_mapped_*.csv')
    files = glob.glob('mmap_trace_mapped_*.csv')

    for file in files:
        name = file.split('.')[0]
        app_dataset = name.split('_')[-2] + "_" + name.split('_')[-1]
        #filename = "mmap_trace_mapped/mmap_trace_mapped_" + app_dataset + ".csv"
        filename = "access_frequency_per_obj_in_PMEM_"+ app_dataset + ".csv"
        df = pd.read_csv(filename)
        call_stack_hash = df['call_stack_hash'].values[0]  #get top 1 from PMEM
        
        filename = "mmap_trace_mapped_" + app_dataset + ".csv"
        df_mmap = pd.read_csv(filename)
        df_mmap = df_mmap.loc[df_mmap.call_stack_hash == call_stack_hash]
        
        
        #Here we are iterating each allocation from the same callstack
        for index, row in df_mmap.iterrows():
            #lifetime from this allocation
            star_timestamp = row['ts_event_start']
            end_timestamp = row['ts_event_end']
        
            #read all samples from PMEM
            #-------------------------------------------------------------------------------------------------------
            #filename = "perfmem_trace_mapped/perfmem_trace_mapped_PMEM_" + app_dataset + ".csv"
            filename = "perfmem_trace_mapped_PMEM_" + app_dataset + ".csv"
            df_pmem = pd.read_csv(filename)
            
            #filter only samples ocurred during the mmap lifetime and with the same callstack
            mask = (df_pmem['ts_event'] >= star_timestamp) & (df_pmem['ts_event'] <= end_timestamp) & (df_pmem['call_stack_hash'] == call_stack_hash)
            df_pmem = df_pmem.loc[mask]

            df_pmem['virt_page_number'] = df_pmem['virt_addr'].apply(lambda x: int(x, 16) >> 12)
            g_df_last_event_group = df_pmem.groupby("virt_page_number")['ts_event'].last().to_frame(name="last_ts_event").reset_index()
            #df_pmem['physical_page_number'] = df_pmem['phys_addr'].apply(lambda x: int(x, 16) >> 12)

            #get all page number that have more than one accesss
            df_access_per_page = df_pmem.virt_page_number.value_counts().reset_index()
            df_access_per_page.columns = ['virt_page_number', 'total_access']
            
            #df_at_least_two_access = df_access_per_page.loc[df_access_per_page.total_access >= 2]
            df_two_access = df_access_per_page.loc[df_access_per_page.total_access > 2]
            
            #df = pd.DataFrame({'value': df_at_least_two_access['total_access'].describe()})
            df = pd.DataFrame({'value': df_two_access['total_access'].describe()})
            df = df.reset_index()
            #print("Number of Access per Page (Call_stack_hash:", call_stack_hash, ")")
            
            #g_virt_page_number_list = df_at_least_two_access.virt_page_number.to_list()
            g_virt_page_number_list = df_two_access.virt_page_number.to_list()
            
            #read all samples from DRAM
            #-------------------------------------------------------------------------------------------------------
            #filename = "perfmem_trace_mapped/perfmem_trace_mapped_DRAM_" + app_dataset + ".csv"
            filename = "perfmem_trace_mapped_DRAM_" + app_dataset + ".csv"
            df_dram = pd.read_csv(filename)
            
            #filter only samples ocurred during the mmap lifetime and with the same callstack
            mask = (df_dram['ts_event'] >= star_timestamp) & (df_dram['ts_event'] <= end_timestamp) & (df_dram['call_stack_hash'] == call_stack_hash)
            df_dram = df_dram.loc[mask]
            
            df_dram['virt_page_number'] = df_dram['virt_addr'].apply(lambda x: int(x, 16) >> 12)
            #df_dram['physical_page_number'] = df_dram['phys_addr'].apply(lambda x: int(x, 16) >> 12)
            
            partitions=18
            df_split = np.array_split(df_dram, partitions)
            pool = Pool(partitions)
            df_list = pool.map(_check_intersection_between_dram_pmem_in_parallel,df_split)
            pool.close()
            pool.join()
            
            df = pd.concat(df_list,ignore_index=True)
            total = df['count_access_pmem_and_dram'].sum() + df['count_access_only_pmem'].sum()
            print("Intersection of Top 1 in PMEM with DRAM")
            print(round(df['count_access_pmem_and_dram'].sum()/total,4)*100, "%")
            '''
            total = df['promoted'].sum() + df['demoted'].sum()
            print("Promoted/Demoted")
            print(round(df['promoted'].sum()/total,4))
            '''
            print("----------------------")
            sys.exit() #with this we analyse only the first allocation

def plot_allocations_top1_object():
    files = glob.glob('track_info_*.csv')
    application_dataset = []
    for file in files:
        name = file.split('.')[0]
        app_dataset = name.split('_')[-2] + "_" + name.split('_')[-1]
       
        df = pd.read_csv(file)
        df.set_index('timestamp', inplace=True)

        df['dram_page_cache'] = df['dram_page_cache_active'] + df['dram_page_cache_inactive']
        df['pmem_page_cache'] = df['pmem_page_cache_active'] + df['pmem_page_cache_inactive']

        df['dram_page_cache']  = df['dram_page_cache']/1000000
        df['pmem_page_cache']  = df['pmem_page_cache']/1000000

        df['dram_page_cache'] = df['dram_page_cache'].round(2)
        df['pmem_page_cache'] = df['pmem_page_cache'].round(2)

        df['dram_app'] = df['dram_app']/1000
        df['pmem_app'] = df['pmem_app']/1000

        df['pgdemote_kswapd'] = df['pgdemote_kswapd'].diff().fillna(0)
        df['pgpromote_success'] = df['pgpromote_success'].diff().fillna(0)
        df['pgpromote_candidate'] = df['pgpromote_candidate'].diff().fillna(0)
        df['promote_threshold'] = df['promote_threshold'].diff().fillna(0)
        df['pgpromote_demoted'] = df['pgpromote_demoted'].diff().fillna(0)

        df['cpu_usage'] = df['cpu_usage'].clip(upper=100)


        fig = plt.figure()
        fig, axes = plt.subplots(figsize= (3,2),nrows=1,sharex=True, gridspec_kw = {'wspace':0.1, 'hspace':0.1})
      
        #axes.annotate('annotate', xy=(67986,159.5), xytext=(67965,155.5),arrowprops=dict(facecolor='black', shrink=0.1, width=0.1, lw=0.1))

    
        df[["dram_app","pmem_app"]].plot(ax=axes, linewidth=0.25)
        axes.legend(['DRAM (App)','NVM (App)'], prop={'size': 6}, fancybox=True, framealpha=0.5)

        axes.plot(67987.5,159.5, 'o', markersize=1, c='blue')
        axes.plot(67987.5,159.5, 'o', markersize=1, mec='red', mfc='none', mew=8)

        axes.annotate('t0', xy=(67987, 160),xytext=(67945, 150),arrowprops=dict(arrowstyle='->',lw=0.5), fontsize=6)
        axes.annotate('t1', xy=(67987, 75),xytext=(67945, 60),arrowprops=dict(arrowstyle='->',lw=0.5), fontsize=6)
        axes.annotate('t2', xy=(68000, 75),xytext=(68028, 60),arrowprops=dict(arrowstyle='->',lw=0.5, color="red"), fontsize=6)

        axes.plot(68245,159.2, 'o', markersize=1, c='blue')
        axes.plot(68245,159.2, 'o', markersize=1, mec='red', mfc='none', mew=8)

        top_obj_call_stack = 2117290442
        df_mmap = pd.read_csv("mmap_trace_mapped_bc_kron.csv")
        df_mmap = df_mmap.loc[df_mmap['call_stack_hash'] == top_obj_call_stack]
        timestamps = df_mmap['ts_event_start'].tolist()
        #filter by callstack and convert each ts_event to an list

        for ts in timestamps:
            axes.axvline(ts, color='red', linewidth = 0.75,linestyle ="--")
        top_obj_call_stack = 534250972
        df_mmap = pd.read_csv("mmap_trace_mapped_bc_kron.csv")
        df_mmap = df_mmap.loc[df_mmap['call_stack_hash'] == top_obj_call_stack]
        timestamps = df_mmap['ts_event_start'].tolist()
        #filter by callstack and convert each ts_event to an list
        for ts in timestamps:
            axes.axvline(ts, color='black', linewidth = 0.75, linestyle="--") #linestyle ="--",

        #axes.axhline(200, color='black', linewidth = 0.25)

        filename = "start_allocations_top1_" + app_dataset + ".pdf"
        plt.xlim([67900, 68300])
        plt.xticks(rotation = 45, fontsize=8)
        plt.yticks(fontsize=8)
        plt.xlabel("Timestamp(seconds)", fontsize=8)
        plt.savefig(filename, bbox_inches="tight")
        plt.clf()
def plot_percentage_access_on_PMEM_and_DRAM():
    df = pd.read_csv("input_perc_access_DRAM_and_PMEM.csv", names=["app_name","DRAM","NVM"])
    df['Total'] = df['DRAM'] + df['NVM']
        
    df.set_index('app_name', inplace=True)
    ax = df.plot(kind='bar', rot=60, figsize= (3,2))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0, symbol='%', is_latex=False))
    #this is responsible to put hatches for each bar plot    
    bars = ax.patches
    hatches = ''.join(h*len(df) for h in 'x/O.')
    for bar, hatch in zip(bars, hatches):
      bar.set_hatch(hatch)
   
    ax.legend(loc='center', ncol=3, bbox_to_anchor=(0.5, 1.2), prop={'size': 8})
    
    plt.ylabel("Percentage of Samples", fontsize=g_fontsize_value)
    plt.xlabel("Workloads", fontsize=g_fontsize_value)
    plt.grid()
    plt.yticks(fontsize=g_fontsize_value)
    plt.xticks(fontsize=g_fontsize_value)
    filename = "percentage_access_on_PMEM_and_DRAM.pdf"
    plt.savefig(filename, bbox_inches="tight")
    plt.clf()
def plot_one_and_two_touches_per_pages():
    df = pd.read_csv("input_touches_per_pages.csv", names=["app_name","1 touch","2 touches"])
    
    df.set_index('app_name', inplace=True)
    ax = df.plot(kind='bar', rot=60, figsize= (3,2))
    ax.legend(loc='center', ncol=2, bbox_to_anchor=(0.5, 1.2), prop={'size': 8})

    # Hide the right and top spines
    ax.tick_params(top=False)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=None, symbol='%', is_latex=False))
    
    plt.ylabel("Percentage of Samples",fontsize=g_fontsize_value)
    plt.xlabel("Workloads",fontsize=g_fontsize_value)
    plt.grid()
    plt.yticks(fontsize=g_fontsize_value)
    plt.xticks(fontsize=g_fontsize_value)
    output = "one_and_two_touches_per_page_outside_from_cache.pdf"
    plt.savefig(output,dpi=300, bbox_inches="tight")
    plt.clf()
def plot_gains_and_lost_execution_time():
    df = pd.read_csv("input_to_plot_exec_time.csv", names=["app_name","autonuma","static mapping", "gain_or_lost"])
    
    df.set_index('app_name', inplace=True)
    df.sort_values(by='gain_or_lost', inplace=True)
    colors = tuple(np.where(df["gain_or_lost"]>0, 'tab:blue', 'tab:orange'))
    ax = df[['gain_or_lost']].plot(kind='bar', rot=60, figsize= (3,2), color=[colors])
    for p in ax.patches:
      ax.annotate(format(p.get_height(), '.1f'), (p.get_x() + p.get_width() / 2., p.get_height()), rotation=0,ha = 'center', va = 'center',size=6,xytext = (0, 3), textcoords = 'offset points')
   
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=None, symbol='%', is_latex=False))
    ax.get_legend().remove()
    plt.axhline(y = 0, color ="black", linestyle ="--", lw = 0.5)
    plt.xlabel("Workloads")
    plt.ylabel("Exec. Time Performance")
    min = df['gain_or_lost'].min() + (-1)
    max = df['gain_or_lost'].max() + (1)
    ax.set_ylim(ymin=min, ymax=max)
    ax.set_yticks(pd.np.linspace(-20, 60, 5))

    output = "gain_or_lost_exec_time.pdf"
    plt.savefig(output,dpi=300, bbox_inches="tight")
    plt.clf()

def main():
    
    if type_of_plot == "single_application":
        files_dram = glob.glob('perfmem_trace_mapped_DRAM_*.csv')
        files_pmem = glob.glob('perfmem_trace_mapped_PMEM_*.csv')

        application_dataset = []
        for file in files_dram:
           name = file.split('.')[0]
           app = name.split('_')[-2] + "_" + name.split('_')[-1]
           application_dataset.append(app)

        for file_dram,file_pmem,app_dataset in zip(files_dram,files_pmem, application_dataset):
            df_DRAM = pd.read_csv(file_dram)
            df_PMEM = pd.read_csv(file_pmem)

            generate_access_frequency_per_object(app_dataset, df_DRAM, df_PMEM)
            plot_touches_per_page(app_dataset, df_DRAM, df_PMEM)
            analysis_outside_from_cache(app_dataset, df_DRAM, df_PMEM)
            decide_static_mapping_between_DRAM_and_PMEM(app_dataset, df_DRAM, df_PMEM)
            plot_number_of_access_per_object_outside_from_cache(app_dataset)
            analysis_only_two_touches_per_page(app_dataset, df_PMEM)
            plot_statistics_to_pages_with_two_touches(app_dataset)
            plot_distribution_access_on_different_mem_levels(app_dataset)

        plot_counters_and_cpu_and_memory_usage()
        
    elif type_of_plot == "multi_application":
        os.system("./generate_inputs_to_plot.sh")
        plot_gains_and_lost_execution_time()
        plot_one_and_two_touches_per_pages()
        plot_percentage_access_on_PMEM_and_DRAM()
if __name__ == "__main__":
   main()
