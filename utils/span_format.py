import os
import shutil

import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

rel = pd.DataFrame()


def get_InstanceName():
    global rel
    df = pd.read_csv("../Trace/cpu_2024_01_07_05/span_cpu_2024_01_07_05.csv")
    service_list = set(df["service_name"])
    rel = df[["service_name", "segmentId"]]
    rel.loc[:, 'segmentId'] = rel['segmentId'].str.split('.').str[0]
    rel = rel.drop_duplicates().reset_index(drop=True)


def generate_segmentId(row):
    random_number = np.random.randint(0, 200)
    timestamp = pd.to_datetime(row['start_time']).timestamp() * 10000
    timestamp_random = timestamp + np.random.randint(0, 1000)
    return f"{row['segmentId']}.{random_number}.{int(timestamp_random)}"


def process_file(exp, file):
    global rel
    exp_path = os.path.join("../Trace", exp)
    df = pd.read_csv(os.path.join(exp_path, file))
    df = df.drop(df.columns[0], axis=1)

    # Add a new column 'parentServiceName' with all values initially set to None
    df['parentServiceName'] = None

    # Check if 'segmentId' column exists in the dataframe
    if 'segmentId' not in df.columns:
        df = pd.merge(df, rel, how='left', on='service_name')

    prev_segmentId = None
    prev_trace_id = None

    for index, row in df.iterrows():
        if prev_trace_id == row['trace_id']:
            if row['span_id'] > 0:
                df.at[index, 'segmentId'] = prev_segmentId
                df.at[index, 'parentServiceName'] = df.at[index - 1, 'parentServiceName']
            else:
                parent_service_name = df.at[index - 1, 'service_name']
                df.at[index, 'segmentId'] = generate_segmentId(row)
                df.at[index, 'refParentId'] = prev_segmentId
                df.at[index, 'parentServiceName'] = parent_service_name

        else:
            df.at[index, 'segmentId'] = generate_segmentId(row)

        prev_segmentId = df.at[index, 'segmentId']
        prev_trace_id = row['trace_id']

    output_path = os.path.join("../../tt-pre", exp)
    if os.path.exists(output_path):
        df.to_csv(os.path.join(output_path, "all_span.csv"), index=False)
        trace_file_path = os.path.join(exp_path, f"trace_{exp}.csv")
        output_trace_path = os.path.join(output_path, "all_trace.csv")
        shutil.copy(trace_file_path, output_trace_path)
        print(f"{exp} finished")


def add_segment_Id():
    exp_list = os.listdir("../Trace")
    tasks = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        df = pd.read_csv("../exp_results.csv")
        fine_exp = df.columns[df.iloc[0] == True].tolist()

        for exp in exp_list:
            if exp not in fine_exp:
                continue
            exp_path = os.path.join("../Trace", exp)
            file_list = os.listdir(exp_path)
            if len(file_list) == 2:
                for file in file_list:
                    if file[0: 4] == "span":
                        tasks.append(executor.submit(process_file, exp, file))
                        if len(tasks) == 15:
                            # Wait for the current batch of tasks to complete
                            for task in tasks:
                                task.result()
                            tasks = []

    # Wait for the remaining tasks to complete
    for task in tasks:
        task.result()


if __name__ == "__main__":
    get_InstanceName()
    add_segment_Id()
