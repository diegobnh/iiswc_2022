from datetime import datetime
from statistics import mean, median
import sys
import matplotlib.pyplot as plt
import time
import operator
import subprocess
from datetime import datetime
import math
import numpy as np
import pandas as pd
import logging
import pandas.io.common
import threading
import itertools
import os
import glob
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count


'''
Esse plot não requer permissões de sudo.
python3 -W ignore 2_manipulate_mmap_and_perfmem.py /ix/dmosse/dmoura/iiswc_2022/collect_scripts
'''

global g_current_app_dataset

pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', lambda x: '%.2f' % x)
if len(sys.argv) > 1:
    trace_path = sys.argv[1]
else:
    print("You should pass the path of trace!!")
    sys.exit(0)
    
class datasets:
    df_mmap = pd.DataFrame()
    df_munmap = pd.DataFrame()
    df_execution_times = pd.DataFrame()
    df_perfmem = pd.DataFrame()
def read_execution_times():
    '''
    All read function should be execute before any process.
    This function is responsible to read high level information about execution.
    Some informations here are used in another function as for example end_time_monot
    '''
    global g_current_app_dataset
    
    filename = "track_info_" + g_current_app_dataset + ".csv"
    df = pd.read_csv(filename)
    start_time_monot = df['timestamp'].head(1).values[0]
    end_time_monot = df['timestamp'].tail(1).values[0]
    
    data = [[g_current_app_dataset, start_time_monot, end_time_monot]]
    
    datasets.df_execution_times = pd.DataFrame(data, columns = ['apps','start_time_monot','end_time_monot'])
    #remove any empty row
    datasets.df_execution_times.dropna(inplace=True)

    datasets.df_execution_times['start_time_monot'] = pd.to_numeric(datasets.df_execution_times['start_time_monot'])
    datasets.df_execution_times['end_time_monot'] = pd.to_numeric(datasets.df_execution_times['end_time_monot'])
    datasets.df_execution_times['total_exec_time'] = datasets.df_execution_times['end_time_monot'] - datasets.df_execution_times['start_time_monot']
def _convert_call_stack_to_object(call_stack):
    '''
    For this function works we need to compile gapbs with the flag "-g" to create symbols.
    '''
    global g_current_app_dataset
    binary = g_current_app_dataset.split("_")[0]
    #binary = trace_path + "binaries/" + str(binary)
    binary = "/scratch/gapbs/" + str(binary)

    #call_stack="+0xb58b:+0xf67c:+0x3e1c:+0x468e:"
    #offsets=call_stack.split(":")[0:-1]
    offsets=call_stack.split(":")

    object_name=""
    for offset in offsets:
        if offset != ' ':
            cmd="addr2line -e "+binary+" "+offset
            returned_output = subprocess.check_output(cmd,shell=True)
            name=str(returned_output.rstrip(),'utf-8')
            if name != "??:?":
                line_number = returned_output.decode().split(':')[-1]
                line_number = line_number.split(' ')[0]
                temp = returned_output.decode().split(':')[0]
                file_name = temp.split('/')[-1]
                object_name = object_name+str(file_name).rstrip("\n")+":"+str(line_number).rstrip("\n") +"/"

    return object_name
def read_mmap_trace(app_dataset):
    #trace_mmap = trace_path + "/mmap_trace/mmap_trace_" + app_dataset + ".csv"
    trace_mmap = trace_path + "/mmap_trace_" + app_dataset + ".csv"
    headers =  ['ts_event_start','mmap','size_allocation', 'start_addr_hex','call_stack_hash', 'call_stack_hexadecimal']

    #convert execution_times to date and create new column
    datasets.df_mmap = pd.read_csv(trace_mmap, names=headers,low_memory=False)
    #remove any empty row
    datasets.df_mmap.dropna(inplace=True)

    datasets.df_mmap['ts_event_start'] = pd.to_numeric(datasets.df_mmap['ts_event_start'])
    datasets.df_mmap['start_addr_decimal'] = datasets.df_mmap['start_addr_hex'].apply(int, base=16)
    datasets.df_mmap['end_addr_decimal'] = datasets.df_mmap['start_addr_decimal'] + datasets.df_mmap['size_allocation']
    datasets.df_mmap['call_stack_hexadecimal'] = datasets.df_mmap['call_stack_hexadecimal'].astype(str)
    datasets.df_mmap['obj_name'] = datasets.df_mmap['call_stack_hexadecimal'].apply(_convert_call_stack_to_object)
def read_munmap_trace(app_dataset):
    #trace_munmap = trace_path + "/mmap_trace/munmap_trace_" + app_dataset + ".csv"
    trace_munmap = trace_path + "/munmap_trace_" + app_dataset + ".csv"
    headers=  ['ts_event','munmap','start_addr_decimal','size_allocation']

    datasets.df_munmap = pd.read_csv(trace_munmap, names=headers,low_memory=False)
    #remove any empty row
    datasets.df_munmap.dropna(inplace=True)


    datasets.df_munmap['ts_event'] = pd.to_numeric(datasets.df_munmap['ts_event'])
    datasets.df_munmap['start_addr_decimal'] = datasets.df_munmap['start_addr_decimal'].apply(int, base=16)
def mapping_mmap_to_munmap():
    '''
    This function is responsible to identify when an mmap is desalocated. We are assume that the first munmap with the same size and address from an mmap is the match for mmap.
    Some mmaps dosen't have munmap. So, in this case whe should use the end_time of execution as the time to desalocate.
    At the end of execution, we will create three new columns for while.
    '''
    global g_current_app_dataset
    
    list_index_mmap=[]
    list_index_munmap=[]

    life_time_new_column=[]
    ts_end_new_column=[]

    df_mmap_temp = datasets.df_mmap.copy()
    df_munmap_temp = datasets.df_munmap.copy()

    for index_i, row_i in df_mmap_temp.iterrows():
        life_time_new_column.insert(index_i,-1)
        ts_end_new_column.insert(index_i,-1)
        for index_j, row_j in df_munmap_temp.iterrows():
            if((row_i['start_addr_decimal'] == row_j['start_addr_decimal']) and (row_i['size_allocation'] == row_j['size_allocation'])):
                 list_index_mmap.append(index_i+1)
                 list_index_munmap.append(index_j+1)

                 life_time_new_column[index_i]= round(row_j['ts_event'] - row_i['ts_event_start'],4)
                 ts_end_new_column[index_i] = row_j['ts_event']

                 df_mmap_temp.drop(index_i, inplace=True)
                 df_munmap_temp.drop(index_j, inplace=True)
                 break

    #Here we create new columns
    datasets.df_mmap['lifetime'] = life_time_new_column
    datasets.df_mmap['ts_event_end'] = ts_end_new_column

    #For those mmaps that dont have munmap, we calculate the lifetime using the time of application's end
    datasets.df_mmap.loc[datasets.df_mmap['ts_event_end'] == -1, 'ts_event_end'] = datasets.df_execution_times['end_time_monot']
    end_time = datasets.df_execution_times.loc[datasets.df_execution_times['apps'] == g_current_app_dataset, 'end_time_monot'].iloc[0]

    datasets.df_mmap.loc[datasets.df_mmap['lifetime'] == -1, 'lifetime'] = round(end_time - datasets.df_mmap['ts_event_start'],4)

    datasets.df_mmap["ts_event_end"].fillna(end_time, inplace = True)

    #Here we create another column calculating how much this lifetime represent in total execution
    relat_time = 100 * (datasets.df_mmap['lifetime']/datasets.df_execution_times.loc[datasets.df_execution_times['apps'] == g_current_app_dataset, 'total_exec_time'].iloc[0])
    datasets.df_mmap['relative_lifetime'] = round(relat_time,2)

    filename = "mmap_trace_mapped_" + g_current_app_dataset + ".csv"
    datasets.df_mmap.to_csv(filename, index=False)
def read_perfmem_trace(app_dataset):
    '''
    Read the perf-mem trace. As we have different information for load and store we need to use different variables
    '''
    headers=  ['ts_event','virt_addr','mem_level','thread_rank','access_weight', 'phys_addr' ,'tlb', 'access_type']
    #file_name = trace_path + "/perfmem_trace/" + "memory_trace_"+ app_dataset + ".csv"
    file_name = trace_path + "/memory_trace_"+ app_dataset + ".csv"
    datasets.df_perfmem = pd.read_csv(file_name, names=headers,low_memory=False) #nrows=10000)
    #filter
    datasets.df_perfmem = datasets.df_perfmem.loc[datasets.df_perfmem['access_type'] == "r"]
    all_loads = datasets.df_perfmem.shape[0]
    datasets.df_perfmem = datasets.df_perfmem[datasets.df_perfmem.mem_level.str.contains('Ram|PMEM', regex= True, na=False)]
    only_loads_out_of_cache = datasets.df_perfmem.shape[0]
    #remove any empty row
    datasets.df_perfmem.dropna(inplace=True)

    ratio = round((only_loads_out_of_cache/all_loads)*100,2)
    cmd = "echo " + str(ratio) + " > ratio_out_of_cache_" + str(g_current_app_dataset) + ".txt"
    os.system(cmd)
    
    if not datasets.df_perfmem.empty:
        datasets.df_perfmem['virt_addr_decimal'] = datasets.df_perfmem['virt_addr'].apply(int, base=16)
        #datasets.df_perfmem['virt_page_number'] = datasets.df_perfmem['virt_addr'].apply(lambda x: int(x, 16) >> 12)
        datasets.df_perfmem['ts_event'] = pd.to_numeric(datasets.df_perfmem['ts_event'])

    datasets.df_perfmem.sort_values(by=['ts_event'],inplace=True)
def mapping_memory_trace_to_mmap(df_perfmem):
    list_mmap_index = []
    list_mmap_call_stack_id = []
    list_mmap_object_name = []

    #Here we are creating an lists of dictionary
    data = {k:[] for k in df_perfmem.columns}

    total_rows_mapped=0
    for index, row in df_perfmem.iterrows():
        df_mmap_temp = datasets.df_mmap.copy()

        mask = (df_mmap_temp['ts_event_start'] <= row['ts_event']) & (row['ts_event'] <= df_mmap_temp['ts_event_end'])
        df_mmap_temp = df_mmap_temp.loc[mask]

        if not df_mmap_temp.empty:
            mask = (df_mmap_temp['start_addr_decimal'] <= row['virt_addr_decimal']) & (row['virt_addr_decimal'] <= df_mmap_temp['end_addr_decimal'])
            df_mmap_temp = df_mmap_temp.loc[mask]

            if not df_mmap_temp.empty:
                total_rows_mapped+= df_mmap_temp.shape[0]
                mmaps_index_match = df_mmap_temp.index.values  #index on dataframe for those mmap that satisfied time and address range
                for row_index_mmap in mmaps_index_match:
                #if you increase or decrease number of columns during perf-mem you must update here
                    data['ts_event'].append(row['ts_event'])
                    data['virt_addr'].append(row['virt_addr'])
                    data['virt_addr_decimal'].append(row['virt_addr_decimal'])
                    #data['virt_page_number'].append(row['virt_page_number'])
                    data['mem_level'].append(row['mem_level'])
                    data['access_weight'].append(row['access_weight'])
                    data['thread_rank'].append(row['thread_rank'])
                    data['phys_addr'].append(row['phys_addr'])
                    data['tlb'].append(row['tlb'])
                    data['access_type'].append(row['access_type'])

                    list_mmap_index.append(row_index_mmap)
                    list_mmap_call_stack_id.append(datasets.df_mmap.iloc[row_index_mmap]['call_stack_hash'])
                    #list_mmap_object_name.append(datasets.df_mmap.iloc[row_index_mmap]['obj_name'])

    #Here we create an dictionary of dataframes
    df = {}
    for col in df_perfmem.columns:
        df[col] = pd.DataFrame(data[col], columns=[col])

    #concat all dataframes
    df_1 = pd.concat(df,join='inner', axis=1,ignore_index=True)
    df_1.columns = df_perfmem.columns

    df_mmap_index = pd.DataFrame(list_mmap_index, columns = ["mmap_index"])
    df_mmap_callstack = pd.DataFrame(list_mmap_call_stack_id, columns = ["call_stack_hash"])
    #df_mmap_object = pd.DataFrame(list_mmap_object_name, columns = ["obj_name"])
    #df_2 = pd.concat([df_mmap_index,df_mmap_callstack,df_mmap_object],join='inner', axis=1,ignore_index=True)
    df_2 = pd.concat([df_mmap_index,df_mmap_callstack],join='inner', axis=1,ignore_index=True)
    #df_2.columns=['mmap_index','call_stack_hash','obj_name']
    df_2.columns=['mmap_index','call_stack_hash']

    df_perfmem_with_mmap = pd.concat([df_1,df_2], axis=1)

    return df_perfmem_with_mmap
def main():
    global trace_path
    partitions = cpu_count()
    #partitions = 18
    
    files = glob.glob('track_info_*.csv')
        
    application_dataset = []
    for file in files:
        name = file.split('.')[0]
        app_dataset = name.split('_')[-2] + "_" + name.split('_')[-1]
        application_dataset.append(app_dataset)
    
    #application_dataset = application_dataset[:1]
    #sys.exit()
    
    for app_dataset in application_dataset:
        global g_current_app_dataset
        g_current_app_dataset = app_dataset
        
        datasets()
        
        read_execution_times() #this function should be the first executed!
        read_mmap_trace(app_dataset) # this function depends of variable created during perfmem_report function
        read_munmap_trace(app_dataset) # this function depends of variable created during perfmem_report function
        mapping_mmap_to_munmap() #depends to read both traces
        read_perfmem_trace(app_dataset) # this function depends from all other read_* functions .

        df_split = np.array_split(datasets.df_perfmem, partitions)
        pool = Pool(partitions)
        df_list = pool.map(mapping_memory_trace_to_mmap,df_split)
        pool.close()
        pool.join()

        df = pd.concat(df_list,ignore_index=True)
        df.sort_values(by=['ts_event'],inplace=True)
        
        df_DRAM = df[df.mem_level.str.contains('Ram', regex= True, na=False)]
        df_PMEM = df[df.mem_level.str.contains('PMEM', regex= True, na=False)]
        
        out = "perfmem_trace_mapped_DRAM_" + g_current_app_dataset + ".csv"
        df_DRAM.to_csv(out, index=False)
        out = "perfmem_trace_mapped_PMEM_" + g_current_app_dataset + ".csv"
        df_PMEM.to_csv(out, index=False)
    
if __name__ == "__main__":
   main()

