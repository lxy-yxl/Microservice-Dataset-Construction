import os
import json
from datetime import datetime, timezone, timedelta
import random
from collections import defaultdict
import pandas as pd
import decimal
from tqdm import tqdm


def get_no_span():
    exp_list = os.listdir("../../tt-pre")
    exps_result = defaultdict(dict)

    for exp in exp_list:
        exp_path = os.path.join("../../tt-pre", exp)
        if not os.path.isdir(exp_path):
            continue
        span_path = os.path.join(exp_path, "all_span.csv")
        if not os.path.exists(span_path):
            exps_result[exp]['type'] = "construct"
        else:
            exps_result[exp]['type'] = "full"

    with open("exps_result.json", 'w') as file:
        json.dump(exps_result, file)


## 计算实验之间相差的时间戳的数值,毫秒级别
def get_offset(source, target):
    s_parts = source.split("_")
    s_date = "_".join(s_parts[1:])
    s_timestamp = datetime.strptime(s_date, "%Y_%m_%d_%H").timestamp()

    t_parts = target.split("_")
    t_date = "_".join(t_parts[1:])
    t_timestamp = datetime.strptime(t_date, "%Y_%m_%d_%H").timestamp()
    return int((t_timestamp - s_timestamp) * 1000)


## 处理三个模态缺失的数据，目前先对缺失span的进行处理
# def process_log(exp,offset):
#     print("log")

def generate_span(source, target):
    offset = get_offset(source, target)
    source = os.path.join("../../tt-pre", source)
    target = os.path.join("../../tt-pre", target)
    s_span_path = os.path.join(source, "all_span.csv")
    s_df = pd.read_csv(s_span_path)

    for index, row in s_df.iterrows():
        s_df.loc[index, "trace_id"] = process_id(str(row["trace_id"]), offset)
        s_df.loc[index, "segmentId"] = process_id(str(row["segmentId"]), offset)
        if not pd.isna(row["refParentId"]):
            s_df.loc[index, "refParentId"] = process_id(str(row["refParentId"]), offset)
        s_df.loc[index, "start_time"] = process_time(str(row["start_time"]), offset)
        s_df.loc[index, "end_time"] = process_time(str(row["end_time"]), offset)

    t_span_path = os.path.join(target, "all_span.csv")
    s_df.to_csv(t_span_path)


# def process_metric():
#     print("metric")


def process_id(id, offset):
    parts = id.split(".")
    third_part = parts[-1]
    other = ".".join(parts[:-1])
    timestamp = divmod(int(third_part), 10000)[0] + offset
    random_data = divmod(int(third_part), 10000)[1]
    timestamp = str(decimal.Decimal(timestamp * 10000 + random_data))
    new_id = f"{other}.{timestamp}"
    return new_id


def process_time(date_time_str, offset):
    # 将字符串转换为datetime对象
    old_datetime_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S.%f")
    old_timestamp_in_milliseconds = int(old_datetime_obj.timestamp() * 1000)
    new_time = old_timestamp_in_milliseconds + offset

    mic_time = new_time % 1000 * 1000
    sec_time = new_time // 1000

    # 设置时区为北京
    beijing_tz = timezone(timedelta(hours=8))
    new_datetime_obj = datetime.fromtimestamp(sec_time, tz=beijing_tz)

    # 将日期时间格式化为指定的字符串格式，只保留日期时间部分
    formatted_date_time = new_datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
    result = f"{formatted_date_time}.{str(mic_time)}"
    return result


# def add_pod_name(exp, pod_list):
#     exp_path = os.path.join("../Logs", exp)
#     file_list = os.listdir(exp_path)
#     for file in file_list:
#         file_path = os.path.join(exp_path, file)
#         parts = file.split('-')
#         pod = "-".join(parts[1:-2])
#         df = pd.read_csv(file_path)
#         df["pod"] = pod
#         df.to_csv(file_path, index=False)
#     print(f"{exp}finished")


if __name__ == "__main__":
    with open("exps_result.json", "r") as file:
        exps_result = json.load(file)

    #### pod exps
    # source_list = [
    #     "pod_2024_01_06_11",
    #     "pod_2024_01_06_03",
    #     "pod_2024_01_04_03",
    #     "pod_2023_12_31_03",
    #     "pod_2024_01_01_21"
    # ]
    #
    # target_list = [
    #     'pod_2024_01_02_15',
    #     'pod_2024_01_04_09',
    #     'pod_2024_01_02_21',
    #     'pod_2024_01_03_03',
    #     'pod_2024_01_02_09'
    # ]

    ### network exps
    # source_list = [
    #     "network_2023_12_31_07",
    #     "network_2023_12_31_01",
    #     "network_2024_01_01_01",
    #     "network_2024_01_01_19",
    #     "network_2024_01_04_07",
    #     "network_2024_01_06_01"
    # ]
    #
    # target_list = [
    #     'network_2024_01_02_07',
    #     'network_2024_01_02_13',
    #     'network_2024_01_02_19',
    #     'network_2024_01_03_01',
    #     'network_2024_01_04_01',
    # ]

    ## memory exps
    # source_list = [
    #     "memory_2024_01_06_15"
    # ]
    # target_list = [
    #     'memory_2024_01_06_07',
    #     'memory_2024_01_05_23'
    # ]

    ## cpu exps

    # source_list = [
    #     "cpu_2024_01_01_23",
    #     "cpu_2024_01_04_05",
    #     "cpu_2024_01_05_21",
    #     "cpu_2024_01_06_05",
    #     "cpu_2024_01_06_13"
    # ]
    #
    # target_list = [
    #     'cpu_2023_12_31_05',
    #     'pod_2024_01_02_03',
    #     'cpu_2024_01_02_23',
    #     'cpu_2024_01_02_11',
    # ]

    ## normal  exps
    source_list = [
        "normal_2024_01_14_07",
        "normal_2024_01_14_06",
        "normal_2024_01_14_06",
        "normal_2024_01_14_06",
    ]

    target_list = [
        "normal_2024_01_15_13",
    ]

    for target in tqdm(target_list, desc="Processing targets", unit="target"):
        source = random.choice(source_list)
        exps_result[target]["source"] = source
        generate_span(source, target)
    with open("exps_result.json", "w") as file:
        json.dump(exps_result, file)
