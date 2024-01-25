import pandas as pd
import os
import numpy as np
from tqdm import tqdm

all_service_list = [
    "ts-admin-basic-info-service",
    "ts-admin-order-service",
    "ts-admin-route-service",
    "ts-admin-travel-service",
    "ts-admin-user-service",
    "ts-assurance-service",
    "ts-auth-service",
    "ts-avatar-service",
    "ts-basic-service",
    "ts-cancel-service",
    "ts-config-service",
    "ts-consign-price-service",
    "ts-consign-service",
    "ts-contacts-service",
    "ts-delivery-service",
    "ts-execute-service",
    "ts-food-delivery-service",
    "ts-food-service",
    "ts-gateway-service",
    "ts-inside-payment-service",
    "ts-news-service",
    "ts-notification-service",
    "ts-order-other-service",
    "ts-order-service",
    "ts-payment-service",
    "ts-preserve-other-service",
    "ts-preserve-service",
    "ts-price-service",
    "ts-rebook-service",
    "ts-route-plan-service",
    "ts-route-service",
    "ts-seat-service",
    "ts-security-service",
    "ts-station-food-service",
    "ts-station-service",
    "ts-ticket-office-service",
    "ts-train-food-service",
    "ts-train-service",
    "ts-travel-plan-service",
    "ts-travel-service",
    "ts-travel2-service",
    "ts-ui-dashboard-service",
    "ts-user-service",
    "ts-verification-code-service",
    "ts-voucher-service",
    "ts-wait-order-service"
]


## 获取时间戳数量
def generate_labels(rows, selected_service_list, exp_name):
    # 生成1800行 * 服务数量 的矩阵，初始值为0
    matrix = np.zeros((rows, len(all_service_list)), dtype=int)

    if rows > 1200:
        # 要设置为1的服务范围（600到1200行）
        start_row = 600
        end_row = 1200

        # 遍历需要修改的服务列表，设置对应行的值为1
        for col, service in enumerate(all_service_list):
            if service in selected_service_list:
                matrix[start_row:end_row + 1, col] = 1

    if rows > 600 and rows < 1200:
        # 要设置为1的服务范围（600到1200行）
        start_row = 600
        end_row = rows
        # 遍历需要修改的服务列表，设置对应行的值为1
        for col, service in enumerate(all_service_list):
            if service in selected_service_list:
                matrix[start_row:end_row + 1, col] = 1

    # 转换为 Pandas DataFrame
    df = pd.DataFrame(matrix, columns=all_service_list)

    # 保存为 CSV 文件
    csv_filename = os.path.join(f"../../tt-pre/{exp_name}", "label.csv")
    df.to_csv(csv_filename, index=False)

    # print(f"Matrix saved to {csv_filename}")


def generate_pods(exp_name):
    exp_metric_path = os.path.join("../Metrics", exp_name)
    exp_type = exp_name.split("_")[0]
    if exp_type == "cpu":
        return cal_cpu(exp_metric_path)
    if exp_type == "memory":
        return cal_memory(exp_metric_path)
    if exp_type == "pod":
        return cal_pod(exp_metric_path)
    if exp_type == "network":
        return cal_network(exp_metric_path)
    else:
        return cal_normal(exp_metric_path)


def cal_cpu(exp_metric_path):
    metric_by_pod_path = os.path.join(exp_metric_path, "metrics_by_pod")
    pods = os.listdir(metric_by_pod_path)
    rows_count = 0
    all_service_list = []
    for pod in pods:
        if (pod[0:3] != "ts-"):
            continue
        pod_metrics = pd.read_csv(os.path.join(metric_by_pod_path, pod))
        rows_count = len(pod_metrics)
        metric = pod_metrics["container_cpu_cfs_throttled_periods_total"]
        if rows_count <= 1200:
            # print(f"{exp_metric_path}<=1200")
            continue
        # 获取索引为500到600的子序列
        subset1 = metric[500:551]
        subset2 = metric[650:751]

        # 计算平均值
        average1 = sum(subset1) / len(subset1)
        average2 = sum(subset2) / len(subset2)

        difference = abs(average2 - average1)
        if difference > 1:
            pod = get_pod_name(pod)
            all_service_list.append(pod)

    return rows_count, all_service_list


def cal_memory(exp_metric_path):
    metric_by_pod_path = os.path.join(exp_metric_path, "metrics_by_pod")
    pods = os.listdir(metric_by_pod_path)
    rows_count = 0
    all_service_list = []
    for pod in pods:
        if (pod[0:3] != "ts-"):
            continue
        pod_metrics = pd.read_csv(os.path.join(metric_by_pod_path, pod))
        rows_count = len(pod_metrics)
        ##修改这个参考的指标
        metric = pod_metrics["container_memory_working_set_bytes"]
        if rows_count <= 1200:
            # print(f"{exp_metric_path}<=1200")
            continue
        # 获取索引为500到600的子序列
        subset1 = metric[400:601]
        subset2 = metric[601:801]

        # 计算平均值
        average1 = sum(subset1) / len(subset1)
        average2 = sum(subset2) / len(subset2)

        difference = abs(average2 - average1)
        if difference > 2000000:
            if rows_count > 1400:
                subset3 = metric[1200:1401]
                average3 = sum(subset3) / len(subset3)
                if average2 - average3 > 1000000:
                    pod = get_pod_name(pod)
                    all_service_list.append(pod)
            else:
                pod = get_pod_name(pod)
                all_service_list.append(pod)

    return rows_count, all_service_list


def cal_pod(exp_metric_path):
    metric_by_pod_path = os.path.join(exp_metric_path, "metrics_by_pod")
    pods = os.listdir(metric_by_pod_path)
    rows_count = 0
    all_service_list = []
    for pod in pods:
        if (pod[0:3] != "ts-"):
            continue
        pod_metrics = pd.read_csv(os.path.join(metric_by_pod_path, pod))
        rows_count = len(pod_metrics)
        metric = pod_metrics["container_cpu_usage_seconds_total"]
        subset0 = metric[550:600]
        average0 = sum(subset0) / len(subset0)

        subset1 = metric[599:1200]
        average1 = sum(subset1) / len(subset1)
        subset2 = metric[1199:1299]
        average2 = sum(subset2) / len(subset2)
        if average2 - average1 > 0.2 or average0 - average1 > 0.2:
            pod = get_pod_name(pod)
            all_service_list.append(pod)
    return rows_count, all_service_list


def cal_network(exp_metric_path):
    metric_by_pod_path = os.path.join(exp_metric_path, "metrics_by_pod")
    pods = os.listdir(metric_by_pod_path)
    rows_count = 0
    all_service_list = []
    for pod in pods:
        if (pod[0:3] != "ts-"):
            continue
        pod_metrics = pd.read_csv(os.path.join(metric_by_pod_path, pod))
        rows_count = len(pod_metrics)

        # 修改这个参考的指标
        metric_column = "container_network_transmit_packets_total"

        if metric_column not in pod_metrics.columns:
            continue
        # metric = pod_metrics["container_cpu_usage_seconds_total"]
        metric = pod_metrics[metric_column]
        # 使用滑动窗口平均进行数据平滑
        # smoothed_metric = smooth_data(metric)
        # # 绘制折线图
        # plt.plot(smoothed_metric, label=pod)  # 每个 pod 作为一个线条
        # # 添加图例
        # plt.legend()
        #
        # # 添加标题和标签
        # plt.title(f"{pod}")
        # plt.xlabel("Time")
        # plt.ylabel("Bytes")
        # # 显示图形
        # plt.show()
        # time.sleep(2)

        if rows_count <= 1200:
            # print(f"{exp_metric_path}<=1200")
            continue
        # 获取索引为500到600的子序列
        subset1 = metric[500:551]
        subset2 = metric[600:1200]
        subset3 = metric[1200:1300]

        # 计算平均值
        average1 = sum(subset1) / len(subset1)
        average2 = sum(subset2) / len(subset2)
        average3 = sum(subset3) / len(subset3)

        difference1 = abs(average2 - average1)
        difference2 = abs(average3 - average2)
        if (difference1 + difference2) / 2 > 3:
            pod = get_pod_name(pod)
            all_service_list.append(pod)
    return rows_count, all_service_list


def cal_normal(exp_metric_path):
    metric_by_pod_path = os.path.join(exp_metric_path, "metrics_by_pod")
    rows_count = len(pd.read_csv(os.path.join(metric_by_pod_path, "nacos-1.csv")))
    return rows_count, []


def get_pod_name(pod_name):
    # 先处理pod名字
    pod_name = os.path.splitext(pod_name)[0]

    # ## 提取微服务名
    if pod_name[-6] == '-':
        parts = pod_name.split("-")

        # 获取不需要删除的部分（最后两个之前的内容）
        base_name = "-".join(parts[:-2])
        return base_name
    return pod_name


if __name__ == "__main__":
    exp_list = os.listdir("../../tt-pre/")
    for exp_name in tqdm(exp_list, desc="Processing Experiments"):
        if not os.path.isdir(os.path.join("../../tt-pre/", exp_name)):
            continue
        rows, selected_pods = generate_pods(exp_name)
        generate_labels(rows, selected_pods, exp_name)
