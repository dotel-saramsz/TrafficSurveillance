import cv2
import numpy as np
import os
from django.conf import settings
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def overlap_play(img1):
    img2 = cv2.imread(os.path.join(settings.BASE_DIR, 'static', 'img/play.png'))
    start_row = int((img1.shape[0] - img2.shape[0]) / 2)
    start_col = int((img1.shape[1] - img2.shape[1]) / 2)
    cv2.addWeighted(src1=img1[start_row:start_row + img2.shape[0], start_col:start_col + img2.shape[1]],
                    alpha=0.5,
                    src2=img2,
                    beta=0.5,
                    gamma=0,
                    dst=img1[start_row:start_row + img2.shape[0], start_col:start_col + img2.shape[1]])
    return img1

def save_pdf(report,vclass_name,vclass_count,totalcount,rolling_avg_count,congestiondata,rolling_avg_congestion,avg_contrib,interval):

    figcount = plt.figure(1, figsize=(20, 10))
    vclass_plots = [figcount.add_subplot(3, 3, i + 1) for i in range(len(vclass_name))]
    secs = [i for i in range(len(totalcount))]
    for i, vplot in enumerate(vclass_plots):
        vplot.set_ylabel('No.of {}'.format(vclass_name[i]))
        vplot.set_xlabel('Time(sec)')
        vplot.plot(secs, vclass_count[i])

    figcongestion = plt.figure(2, figsize=(20, 10))

    totcount_plot = figcongestion.add_subplot(221)
    totcongest_plot = figcongestion.add_subplot(222)
    rollcount_plot = figcongestion.add_subplot(223)
    rollcongest_plot = figcongestion.add_subplot(224)

    totcount_plot.set_title('No.of vehicles in the road over time')
    totcount_plot.set_ylabel('No.of vehicles')
    totcount_plot.set_xlabel('Time(sec)')
    totcount_plot.plot(secs, totalcount)

    # to plot a rolling average of total vehicles
    rollcount_plot.set_title('Rolling average of no. of vehicles in road convolved over {} seconds'.format(interval))
    rollcount_plot.set_ylabel('No.of vehicles')
    rollcount_plot.set_xlabel('Time(sec)')
    rollcount_plot.plot(secs, rolling_avg_count, color='red')

    totcongest_plot.set_title('Congestion index of vehicles in the road')
    totcongest_plot.set_ylabel('Congestion index')
    totcongest_plot.set_xlabel('Time(sec)')
    totcongest_plot.plot(secs, congestiondata)

    # to plot a rolling average of congestion index
    rollcongest_plot.set_title('Rolling average of congestion index convolved over {} seconds'.format(interval))
    rollcongest_plot.plot(secs, rolling_avg_congestion, color='red')

    figcontrib = plt.figure(3, figsize=(10, 8))
    contrib_plot = figcontrib.add_subplot(111)
    contrib_plot.set_title('Contribution of different vehicle classes to the average congestion over the entire period')
    contrib_plot.pie(avg_contrib, None, vclass_name, autopct='%1.1f%%')

    figtable = plt.figure(4, figsize=(10, 8))
    outgoing_vehicle_table = figtable.add_subplot(211)
    overall_summary_table = figtable.add_subplot(212)

    outgoing_count = [[report.outgoing_tempo_count,
                       report.outgoing_bike_count,
                       report.outgoing_car_count,
                       report.outgoing_taxi_count,
                       report.outgoing_micro_count,
                       report.outgoing_pickup_count,
                       report.outgoing_bus_count,
                       report.outgoing_truck_count]]
    outgoing_vehicle_table.set_title('Total no. of outgoing vehicles from the road in the analysed time interval')
    outgoing_vehicle_table.axis('off')
    tb1 = outgoing_vehicle_table.table(cellText=outgoing_count, colLabels=tuple(vclass_name), loc='center')

    overall_summary = [[report.avg_congestion_index, report.avg_count_index]]
    overall_summary_table.set_title('Average summary of traffic mobility in the analysed interval')
    overall_summary_table.axis('off')
    tb2 = overall_summary_table.table(cellText=overall_summary, colLabels=('Average Congestion Index','Average number of vehicles in road at a time'), loc='center')

    pdf_filename = os.path.join('reportpdfs','{}.pdf'.format(report.video.video_name))
    reportpdf = PdfPages(os.path.join(settings.BASE_DIR,'static',pdf_filename))
    reportpdf.savefig(figcount)
    reportpdf.savefig(figcongestion)
    reportpdf.savefig(figcontrib)
    reportpdf.savefig(figtable)
    reportpdf.close()
    report.report_file = pdf_filename
    report.save()

    plt.close('all')
