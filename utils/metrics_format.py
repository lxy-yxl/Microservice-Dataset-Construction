import os
import shutil
import re
import csv
import json
import threading

import pandas as pd

KPIs = [
    "container_cpu_usage_seconds_total",
    "container_cpu_cfs_throttled_periods_total",
    "container_memory_working_set_bytes",
    "container_network_receive_bytes_total",
    "container_network_transmit_bytes_total",
    "container_network_receive_packets_total",
    "container_network_transmit_packets_total",
    "container_network_receive_packets_dropped_total",
    "container_network_transmit_packets_dropped_total",
    "resource_response_size_query_p50",
    "resource_response_code_requests_query",
    "resource_request_size_query_p50",
    "client_success_rate",
    "client_request_volume",
    "client_request_duration_p50"
]


def parse_json(json_data):
    parsed_data = {}
    for entry in json_data['data']['result']:
        pod_name = entry['metric']['pod']
        timestamps = [value[0] for value in entry['values']]
        cpu_values = [float(value[1]) for value in entry['values']]
        parsed_data[pod_name] = {'timestamps': timestamps, 'values': cpu_values}
    return parsed_data


def extract_name():
    metrics = os.listdir('../Metrics')
    for expt in metrics:
        expt_path = os.path.join('../Metrics', expt)
        # Handle pod-level metrics first
        merge_metrics(expt_path)

        files = os.listdir(expt_path)
        service_pattern = re.compile(r'(.*).train-ticket\.svc\.cluster\.local_(.*)')
        service_list = []
        # Traverse the file and process
        for file in files:
            file_path = os.path.join(expt_path, file)
            if os.path.isfile(file_path):
                match = service_pattern.match(file)
                if match:
                    # Extract the desired part
                    pre_name, post_name = match.groups()
                    service_list.append(pre_name)

                    # Create a folder
                    folder_name = os.path.join(expt_path, pre_name)
                    os.makedirs(folder_name, exist_ok=True)

                    # Move the file to a new directory
                    new_file_name = post_name  # Or keep the extension of the original file
                    shutil.move(file_path, os.path.join(folder_name, new_file_name))


def write_to_csv(directory, service_name, timestamps, kpi_values):
    if not os.path.exists(f"{directory}/metrics_by_pod"):
        os.mkdir(f"{directory}/metrics_by_pod")
    filename = f"{directory}/metrics_by_pod/{service_name}.csv"

    with open(filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write header
        header = ['Timestamp'] + list(kpi_values.keys())
        csv_writer.writerow(header)

        # Transpose values to handle different column lengths
        rows = zip(timestamps, *kpi_values.values())
        for row in rows:
            csv_writer.writerow(row)


def process_pod_data(root, pod_name, parsed_data, KPIs):
    # 初始化空字典
    pod_kpi_values = {}

    # 检查每个pod的指标
    for kpi in KPIs:
        if pod_name in parsed_data[kpi]:
            # 如果Pod有对应指标就存储下来
            pod_kpi_values[kpi] = parsed_data[kpi][pod_name]['values']
        else:
            print(f"Pod {pod_name} is missing KPI: {kpi}. Skipping this KPI for the pod.")

    # 检查Metrics是否存在
    if pod_kpi_values:
        # 获取总的时间戳
        cpu_timestamps = parsed_data["container_cpu_usage_seconds_total"][pod_name]['timestamps']

        # 写入CSV
        write_to_csv(root, pod_name, cpu_timestamps, pod_kpi_values)
    else:
        print(f"Pod {pod_name} is missing all specified KPIs. Skipping.")


def merge_metrics(root):
    kpi_files = {kpi: f"{kpi}.json" for kpi in KPIs}

    # 初始化存储每个Metrics指标的路径
    parsed_data = {kpi: None for kpi in KPIs}

    # 加载每个Metrics的json
    for kpi, filename in kpi_files.items():
        file_path = os.path.join(root, filename)
        with open(file_path, 'r') as json_file:
            json_data = json.load(json_file)
            parsed_data[kpi] = parse_json(json_data)
        # 删除文件
        os.remove(file_path)

    # 将处理完的数据写入CSV
    for pod_name in parsed_data[KPIs[0]]:
        process_pod_data(root, pod_name, parsed_data, KPIs)


def format_pod_csv():
    exps = os.listdir("../Metrics")
    for exp in exps:
        exp_path = os.path.join("../Metrics", exp)
        pod_csv_path = os.path.join(exp_path, "metrics_by_pod")
        pods = os.listdir(pod_csv_path)

        # 用于存储每个 pod 处理后的 DataFrame 的字典
        pod_dfs = {}

        for pod in pods:
            # 先处理pod名字
            base_name = os.path.splitext(pod)[0]

            # ## 提取微服务名
            if base_name[-6] == '-':
                parts = base_name.split("-")

                # 获取不需要删除的部分（最后两个之前的内容）
                base_name = "-".join(parts[:-2])
                print(base_name)
            pod_path = os.path.join(pod_csv_path, pod)
            df = pd.read_csv(pod_path)

            prefix = f"{base_name}_"
            df.columns = [prefix + col if col != 'Timestamp' else col for col in df.columns]

            pod_dfs[pod] = df

        # 合并具有相同 timestamp 的行
        merged_df = pd.concat(pod_dfs.values(), axis=1)

        # 保存合并后的 DataFrame 到文件
        merged_csv_path = os.path.join(exp_path, "all_metrics.csv")
        merged_df.to_csv(merged_csv_path, index=False)


# 定义一个信号量，最多允许15个线程同时运行
max_threads = threading.Semaphore(20)


def process_experiment(exp):
    with max_threads:
        try:
            print(f"{exp} started")
            exp_path = os.path.join("../Metrics", exp)
            total_df = pd.read_csv(os.path.join(exp_path, "all_metrics.csv"))
            pods = os.listdir(exp_path)

            for pod in pods:
                if not os.path.isdir(os.path.join(exp_path, pod)) or pod == "metrics_by_pod":
                    continue

                all_metrics_path = os.path.join(exp_path, pod)
                metrics = os.listdir(all_metrics_path)

                pod_df = pd.DataFrame(data=None, columns=['Timestamp'])
                pod_df['Timestamp'] = total_df['Timestamp']
                # 去除包含 NaN 值的行
                pod_df = pod_df.dropna(subset=['Timestamp'])

                for metric in metrics:
                    metric_name = os.path.splitext(metric)[0]
                    if metric_name not in KPIs:
                        continue
                    metrics_path = os.path.join(all_metrics_path, metric)

                    try:
                        with open(metrics_path) as f:
                            json_data = json.load(f)

                        if "result" in json_data["data"] and json_data["data"]["result"]:
                            for result in json_data["data"]["result"]:
                                values = result["values"]
                                metric_json = result["metric"]
                                if metric_json == {}:
                                    metric_df = pd.DataFrame(values, columns=["Timestamp", f"{pod}_{metric_name}"])
                                    pod_df = pd.merge(pod_df, metric_df, on="Timestamp", how="left")
                                else:
                                    if "response_code" in metric_json:
                                        suffix = f'{metric_json["response_code"]}_{metric_json["source_workload"]}'
                                    else:
                                        suffix = f'{metric_json["source_workload"]}'
                                    metric_df = pd.DataFrame(values, columns=["Timestamp", f"{pod}_{suffix}_{metric_name}"])
                                    pod_df = pd.merge(pod_df, metric_df, on="Timestamp", how="left")
                    except json.JSONDecodeError as json_error:
                        print(f"Error decoding JSON in file {metrics_path}: {json_error}")
                        # 处理 JSON 解析错误的代码

                total_df = pd.merge(total_df, pod_df, on="Timestamp", how="left")

            # 删除所有以 'Timestamp.' 开头的列
            for col in total_df.columns:
                if col.startswith('Timestamp.') and col != 'Timestamp':
                    total_df.drop(columns=[col], inplace=True)

            # 删除所有包含 NaN 的列
            total_df = total_df.dropna(axis=1, how='all')

            output_path = os.path.join("../../tt-pre", exp)
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            merged_csv_path = os.path.join(output_path, "all_metric.csv")
            total_df.to_csv(merged_csv_path, index=False)

        except Exception as e:
            print(f"An error occurred in experiment {exp}: {e}")
            # 处理其他异常的代码


def format_all_csv():
    exps = os.listdir("../Metrics")
    threads = []
    df = pd.read_csv("../exp_results.csv")

    fine_exp = df.columns[(df.iloc[0] == "True") & (df.iloc[2] == "True") & (df.iloc[3] == "True")].tolist()

    for exp in exps:
        if exp not in fine_exp:
            continue
        thread = threading.Thread(target=process_experiment, args=(exp,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


def rename():
    explist = os.listdir("../../tt-pre")
    for exp in explist:
        exp_path = os.path.join("../../tt-pre", exp)
        if os.path.isdir(exp_path):
            metric_path = os.path.join(exp_path, "all_metric.csv")
            if os.path.exists(metric_path):
                df = pd.read_csv(metric_path)
                df.columns = df.columns.str.replace('ts-preserve-other-servi', 'ts-preserve-other-service')
                df.to_csv(metric_path)


if __name__ == "__main__":
    # format_pod_csv()
    format_all_csv()
    # rename()
