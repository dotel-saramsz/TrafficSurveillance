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

def save_pdf(report,vclass_name,vclass_count,totalcount,rolling_avg_count,congestiondata,rolling_avg_congestion,avg_contrib):

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
    rollcount_plot.set_title('Rolling average of no. of vehicles in road convolved over 5 seconds')
    rollcount_plot.set_ylabel('No.of vehicles')
    rollcount_plot.set_xlabel('Time(sec)')
    rollcount_plot.plot(secs, rolling_avg_count, color='red')

    totcongest_plot.set_title('Congestion index of vehicles in the road')
    totcongest_plot.set_ylabel('Congestion index')
    totcongest_plot.set_xlabel('Time(sec)')
    totcongest_plot.plot(secs, congestiondata)

    # to plot a rolling average of congestion index
    rollcongest_plot.set_title('Rolling average of congestion index convolved over 5 seconds')
    rollcongest_plot.plot(secs, rolling_avg_congestion, color='red')

    figcontrib = plt.figure(3, figsize=(10, 8))
    contrib_plot = figcontrib.add_subplot(111)
    contrib_plot.set_title('Contribution of different vehicle classes to the average congestion over the entire period')
    contrib_plot.pie(avg_contrib, None, vclass_name, autopct='%1.1f%%')

    pdf_filename = os.path.join('reportpdfs','{}.pdf'.format(report.video.video_name))
    reportpdf = PdfPages(os.path.join(settings.BASE_DIR,'static',pdf_filename))
    reportpdf.savefig(figcount)
    reportpdf.savefig(figcongestion)
    reportpdf.savefig(figcontrib)
    reportpdf.close()
    report.report_file = pdf_filename
    report.save()
