import os
import shutil
import pandas as pd


##删除不正常的文件夹
df = pd.read_csv("../exp_results.csv")

fine_exp = df.columns[(df.iloc[0] == "True") & (df.iloc[2] == "True") & (df.iloc[3] == "True")].tolist()

exps = os.listdir("../../tt-pre")

for exp in exps:
    if exp not in fine_exp:
        exp_path = os.path.join("../../tt-pre",exp)
        try:
            # 删除文件夹及其内容
            shutil.rmtree(exp_path)
            print(f"The folder at {exp_path} has been successfully deleted.")
        except Exception as e:
            print(f"Error deleting the folder: {e}")

