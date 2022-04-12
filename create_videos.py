import numpy as np
from PIL import Image
import ffmpeg
import os
from os import listdir
from os.path import isfile, join


def create_video_section(folder_path, output_path, x, y, width, height):
    png_files = [f for f in listdir(folder_path) if isfile(join(folder_path, f))]
    png_files = sorted(png_files)

    actual_width = width
    actual_height = height if height % 2 == 0 else height + 1

    size = '{0}x{1}'.format(actual_width, actual_height)

    process = (
        ffmpeg.input('pipe:', format="rawvideo", pix_fmt='rgb24', s=size, framerate=30)
              .output(output_path, pix_fmt='yuv420p')
              .overwrite_output()
              .run_async(pipe_stdin=True)
    )

    def next_file():
        for f in png_files:
            img = Image.open(os.path.join(folder_path, f))
            rgbimg = img.convert('RGB')
            rgb_array = np.asarray(rgbimg)
            sub_array = rgb_array[y:y+height, x:x+width]

            # pad with black if required
            if height % 2 != 0:
                sub_array = np.pad(sub_array, ((0, 1), (0, 0), (0, 0)), 'constant', constant_values=0)

            yield sub_array

    for i in next_file():
        process.stdin.write(i.astype(np.uint8).tobytes())

    process.stdin.close()
    process.wait()


def create_video(folder_path, output_path):
    """
    Create video from PNG files in folder_path
    :param folder_path:
    :param output_path:
    :return:
    """
    png_files = [f for f in listdir(folder_path) if isfile(join(folder_path, f))]
    png_files = sorted(png_files)

    process = (
        ffmpeg.input('pipe:', format="rawvideo", pix_fmt='rgb24', s='2000x2000', framerate=30)
              .output(output_path, pix_fmt='yuv420p')
              .overwrite_output()
              .run_async(pipe_stdin=True)
    )

    def next_file():
        for f in png_files:
            img = Image.open(os.path.join(folder_path, f))
            rgbimg = img.convert('RGB')
            yield np.asarray(rgbimg)

    for i in next_file():
        process.stdin.write(i.astype(np.uint8).tobytes())

    process.stdin.close()
    process.wait()


if __name__ == '__main__':
    path = r'D:\Coding\amongi\data\output\png_5m'
    output = r'D:\Coding\amongi\data\output\video\test_star_wars_2.mp4'

    # create_video(path, output)
    create_video_section(path, output, 571, 699, 100, 145)
