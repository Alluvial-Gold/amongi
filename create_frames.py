import pandas as pd
import numpy as np
import tables as tb

import save_png


def get_pixel_data_frame(start_time, end_time, file_df):
    """
    Create dataframe from data between timestamps

    :param start_time:
    :param end_time:
    :param file_df: file dataframe with min & max times
    :return: dataframe with values between start & end time
    """

    # Figure out which files are in range
    start_mask_1 = file_df['min'] <= start_time
    start_mask_2 = start_time <= file_df['max']
    end_mask_1 = file_df['min'] <= end_time
    end_mask_2 = end_time <= file_df['max']
    full_mask = (start_mask_1 & start_mask_2) | (end_mask_1 & end_mask_2)
    in_range_files = file_df[full_mask]

    num_files = len(in_range_files)
    pixel_df = []

    if num_files == 1:
        filestr = in_range_files.iloc[0]['filename']
        pixel_df = pd.read_hdf(filestr, key='t', where=['timestamp >= start_time', 'timestamp < end_time'])
    elif num_files == 2:
        filestr_1 = in_range_files.iloc[0]['filename']
        pixel_df_1 = pd.read_hdf(filestr_1, key='t', where=['timestamp >= start_time', 'timestamp < end_time'])
        filestr_2 = in_range_files.iloc[1]['filename']
        pixel_df_2 = pd.read_hdf(filestr_2, key='t', where=['timestamp >= start_time', 'timestamp < end_time'])
        if isinstance(pixel_df_1, pd.DataFrame) and isinstance(pixel_df_2, pd.DataFrame):
            pixel_df = pd.concat([pixel_df_1, pixel_df_2])

    # Sort
    pixel_df = pixel_df.sort_values(by=['timestamp'])
    return pixel_df


def get_hdf_file_timestamp_ranges():
    """
    Helper function - get first & last timestamps for each .hdf file

    :return:
    """
    file_names = []
    file_mins = []
    file_maxs = []

    for i in range(0, 8):
        filestr = r'.\data\output\full_output_' + str(i) + '.h5'

        h5f = tb.open_file(filestr, 'r')

        # Read timestamp column & get min/max
        ts = h5f.root.t.table.col('timestamp')
        file_names.append(filestr)
        file_mins.append(pd.Timestamp(ts.min(), unit="ns"))
        file_maxs.append(pd.Timestamp(ts.max(), unit="ns"))

        h5f.close()

    # Create dataframe
    df = pd.DataFrame({'filename': file_names, 'min': file_mins, 'max': file_maxs})
    return df


def create_frames():
    """
    Save snapshots
    """

    # Array of start/end timestamps for each file
    file_df = get_hdf_file_timestamp_ranges()

    start_time = file_df.iloc[0]['min']
    end_time = file_df.iloc[7]['max']
    delta_minutes = 1

    frame_start_time = start_time

    # Start with 2000 x 2000, filled with 31 (white)
    pixel_array = np.full((2000, 2000), 31).astype(np.uint8)

    while frame_start_time < end_time:
        print(frame_start_time)

        pixel_df = get_pixel_data_frame(frame_start_time, frame_start_time + pd.Timedelta(minutes=delta_minutes), file_df)

        # Update pixel array
        if isinstance(pixel_df, pd.DataFrame):
            for index, row in pixel_df.iterrows():
                pixel_array[row['Y'], row['X']] = row['pixel_color']

        # Save PNG
        output_file_str = r'.\data\output\png_1m\png_' + str(frame_start_time.value) + '.png'
        save_png.save_png(pixel_array, output_file_str)

        # Increment
        frame_start_time += pd.Timedelta(minutes=delta_minutes)


if __name__ == '__main__':
    create_frames()


