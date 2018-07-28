import os
import datetime
import re

# base_dir = os.getcwd()
# folder_name = 'Jamal'
# search_dir = os.path.join(base_dir, folder_name)
# try:
#     for file in os.scandir(search_dir):
#         stats = os.stat(file.path)
#         access_time = datetime.datetime.fromtimestamp(stats.st_ctime).strftime(
#             '%Y-%m-%d_%H:%M:%S')
#         pattern = r'[a-zA-Z]+_\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}\.\w{3,}'
#         if not re.match(pattern, file.name):
#             print(file.name,' does not match the pattern')
#             unique_name = '{}_{}'.format(folder_name,access_time)
#             os.rename(file.path,os.path.join(search_dir, unique_name+os.path.splitext(file.name)[1]))
#             print(access_time)
#
# except Exception as e:
#     print(str(e))
lane_dimens = '[0,719],[0,352],[478,0],[936,0],[1073,250],[1279,495],[1279,719]'
pattern = r'\[(\d+,\d+)\]'
points = re.finditer(pattern, lane_dimens)
point_list = []
print(points)
for point in points:
    point = point.group()
    point = [int(each) for each in point.lstrip('[').rstrip(']').split(',')]
    print(point)
    point_list.append(point)
print(point_list)
