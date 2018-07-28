import os
import datetime

base_dir = os.getcwd()
folder_name = 'Jamal'
search_dir = os.path.join(base_dir, folder_name)
try:
    for file in os.scandir(search_dir):
        stats = os.stat(file.path)
        access_time = datetime.datetime.fromtimestamp(stats.st_atime).strftime(
            '%Y-%m-%d_%H:%M:%S')
        print(stats)
        print(access_time)
except Exception as e:
    print(str(e))
