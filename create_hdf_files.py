import pandas as pd
import numpy as np
import gzip

import colour_map


def find_acts_of_mod():
    """
    Find the rows with mod rectangles (x,y,x2,y2)
    """
    num_rects = 0

    for i in range(0, 2):
        numstr = str(i).zfill(2)
        filestr = r'.\data\zips\2022_place_canvas_history-0000000000' + numstr + '.csv.gzip'
        print('\n')
        print(filestr)

        with gzip.open(filestr) as myzip:
            df = pd.read_csv(myzip, usecols=[3])
            multiple_values = df['coordinate'].str.count(',') > 1
            num_multiple = np.sum(multiple_values)
            print(num_multiple)
            if num_multiple > 0:
                print(df[multiple_values])
                num_rects += num_multiple

    print('\nTotal number of rectangles: ' + str(num_rects))


def create_rectangle_rows(row):
    """
    Create rows for each pixel in rectangle

    :param row: original rectangle row from data, with X, X2, Y, Y2
    :return: new rows to add
    """
    # Convert to data frame
    rect_df = row.to_frame().T

    # Rectangle from X to X2, inclusive; Y to Y2, inclusive
    start_x = int(row['X'])
    end_x = int(row['X2']) + 1
    start_y = int(row['Y'])
    end_y = int(row['Y2']) + 1

    for xValue in range(start_x, end_x):
        for yValue in range(start_y, end_y):
            new_row = pd.DataFrame([[row['timestamp'], row['pixel_color'], xValue, yValue]],
                                   columns=['timestamp', 'pixel_color', 'X', 'Y'])
            rect_df = pd.concat([rect_df, new_row])

    # Drop first row
    rect_df = rect_df.drop(rect_df[~rect_df['X2'].isnull()].index)

    return rect_df


def create_converted_dataframe(filename):
    """
    Create converted dataframe

    :param filename:
    :return: data frame
    """
    with gzip.open(filename) as myzip:
        df = pd.read_csv(myzip, usecols=[0, 2, 3])

        # Get X/Y coordinates, and possible x2/y2 values
        try:
            df[['X', 'Y', 'X2', 'Y2']] = df['coordinate'].str.split(',', expand=True)
        except ValueError:
            df[['X', 'Y']] = df['coordinate'].str.split(',', expand=True)
            df[['X2', 'Y2']] = None

        # Get rectangles
        rectangle_rows = df[~df['X2'].isnull()]

        # For each rectangle, create rows for each pixel
        for index, row in rectangle_rows.iterrows():
            new_rect_rows = create_rectangle_rows(row)
            df = pd.concat([df, new_rect_rows], ignore_index=True)

        # Remove original rectangle rows
        df = df.drop(df[~df['X2'].isnull()].index)

        df[['X', 'Y']] = df[['X', 'Y']].astype(np.uint16)

        # Convert timestamp to dates - some don't have milliseconds
        df['timestamp_temp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S.%f %Z", errors='coerce')
        mask = df['timestamp_temp'].isnull()
        df.loc[mask, 'timestamp_temp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S %Z", errors='coerce')
        df['timestamp'] = df['timestamp_temp']

        # Convert colours to index
        df['pixel_color'] = df['pixel_color'].map(lambda pc: colour_map.colour_map[pc]).astype(np.uint8)

        # Remove extra columns
        df.drop(['coordinate', 'X2', 'Y2', 'timestamp_temp'], axis=1, inplace=True)

    return df


def get_filenames_in_order():
    """
    Returns array of Place data filenames in time order
    """

    time_dict = {}

    for i in range(0, 79):
        numstr = str(i).zfill(2)
        filestr = r'.\data\zips\2022_place_canvas_history-0000000000' + numstr + '.csv.gzip'
        with gzip.open(filestr) as myzip:
            # Find timestamp of first row
            df = pd.read_csv(myzip, usecols=[0], nrows=1)

            df['timestamp_temp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S.%f %Z", errors='coerce')
            mask = df['timestamp_temp'].isnull()
            if np.sum(mask) > 0:
                df.loc[mask, 'timestamp_temp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S %Z")

            ts = df['timestamp_temp'][0]

            time_dict[filestr] = ts

    sorted_dict = {k: v for k, v in sorted(time_dict.items(), key=lambda item: item[1])}

    print(sorted_dict.keys())

    return sorted_dict.keys()


def save_hdf_file(df, output_part):
    """
    Save dataframe as HDF file

    :param df: dataframe
    :param output_part: output number
    """
    print('Output ' + str(output_part))
    output_filename = r'.\data\output\full_output_' + str(output_part) + '.h5'
    df.to_hdf(output_filename, key='t', format='table', data_columns=['timestamp'])


def create_hdf_files():
    """
    Create HDF files from Place data csvs
    """
    filename_list = get_filenames_in_order()

    df = None
    output_part = 0

    for i, filestr in enumerate(filename_list):
        print(filestr)

        df_new = create_converted_dataframe(filestr)

        if df is None:
            df = df_new
        else:
            df = pd.concat([df, df_new])

        # Output to hdf every 10 files
        if (i + 1) % 10 == 0:
            save_hdf_file(df, output_part)
            output_part += 1
            df = None

    # Final output
    save_hdf_file(df, output_part)


if __name__ == '__main__':
    create_hdf_files()
