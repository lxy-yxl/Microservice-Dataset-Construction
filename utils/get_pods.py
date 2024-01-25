import requests
import re
import csv

url = 'http://10.60.38.174:31015/api/events'


csv_file = open('output.csv', 'w', newline='')
csv_writer = csv.writer(csv_file)

# 写入 CSV 文件的标题行
csv_writer.writerow(['Time', 'Pod'])

try:
    # 发送 GET 请求
    response = requests.get(url)

    # 检查响应状态码
    if response.status_code == 200:
        results = response.json()

        for result in results:
            time = result.get('created_at')
            message = result.get('message')
            # print(message)

            match1 = re.search(r'Successfully apply chaos for train-ticket/(.+)/(.*)', message)
            if match1:
                message = match1.group(1)
                print(message)
                csv_writer.writerow([time, message])
                continue

            match2 = re.search(r'Successfully apply chaos for train-ticket/(.+)', message)
            if match2:
                # 打印响应内容
                message = match2.group(1)  # 如果响应是 JSON 格式的话
                print(message)
                csv_writer.writerow([time, message])
            # 写入 CSV 文件

    else:
        print(f"Error: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
finally:
    # 关闭 CSV 文件
    csv_file.close()
