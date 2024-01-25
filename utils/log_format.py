import pandas as pd
import os


def merge_log():
    exps = os.listdir("../../tt-pre/")

    df = pd.read_csv("../exp_results.csv")
    fine_exp = df.columns[(df.iloc[0] == "True") & (df.iloc[2] == "True") & (df.iloc[3] == "True")].tolist()


    for exp in exps:

        exp_path = os.path.join("../Logs", exp)
        if not os.path.isdir(exp_path):
            continue

        logs = os.listdir(exp_path)
        length = len(logs)

        # 删除已存在的文件
        output_path = f"../../tt-pre/{exp}/all_logs.csv"
        if os.path.exists(output_path):
            os.remove(output_path)

        # 读取第一个CSV文件并保存
        first_file_path = os.path.join(exp_path, logs[0])
        df = pd.read_csv(first_file_path)
        df["timestamp"] = df['timestamp']+28800000

        if not os.path.exists(f"../../tt-pre/{exp}/"):
            os.mkdir(f"../../tt-pre/{exp}/")

        df.to_csv(output_path, index=False)

        # 循环遍历列表中各个CSV文件名，并完成文件拼接
        for i in range(1, length):  # 注意从第二个文件开始
            file_path = os.path.join(exp_path, logs[i])
            df = pd.read_csv(file_path)
            df["timestamp"] = df['timestamp'] + 28800000
            df.to_csv(output_path, index=False, header=False, mode='a+')
        print(f"{exp}finished")


if __name__ == "__main__":
    merge_log()
