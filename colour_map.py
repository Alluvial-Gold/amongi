import pandas as pd
import numpy as np
import gzip

colour_map = {
    '#000000': 0,
    '#00756F': 1,
    '#009EAA': 2,
    '#00A368': 3,
    '#00CC78': 4,
    '#00CCC0': 5,
    '#2450A4': 6,
    '#3690EA': 7,
    '#493AC1': 8,
    '#515252': 9,
    '#51E9F4': 10,
    '#6A5CFF': 11,
    '#6D001A': 12,
    '#6D482F': 13,
    '#7EED56': 14,
    '#811E9F': 15,
    '#898D90': 16,
    '#94B3FF': 17,
    '#9C6926': 18,
    '#B44AC0': 19,
    '#BE0039': 20,
    '#D4D7D9': 21,
    '#DE107F': 22,
    '#E4ABFF': 23,
    '#FF3881': 24,
    '#FF4500': 25,
    '#FF99AA': 26,
    '#FFA800': 27,
    '#FFB470': 28,
    '#FFD635': 29,
    '#FFF8B8': 30,
    '#FFFFFF': 31,
}


def get_all_colours():
    """
    Prints list of all colours in .csv files
    """

    colour_list = None
    for i in range(0, 79):
        numstr = str(i).zfill(2)
        print(numstr)
        filestr = r'.\data\zips\2022_place_canvas_history-0000000000' + numstr + '.csv.gzip'
        with gzip.open(filestr) as myzip:
            df = pd.read_csv(myzip, usecols=[2])
            unique_colours = df['pixel_color'].unique()
            if i == 0:
                colour_list = unique_colours
            else:
                colour_list = np.concatenate((colour_list, unique_colours), axis=None)
                colour_list = np.unique(colour_list)

    print(colour_list)


if __name__ == '__main__':
    get_all_colours()
