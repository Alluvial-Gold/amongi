import numpy as np
from PIL import Image

import colour_map


def convert_to_rgb(hex_string):
    """
    Convert hex string to [r, g, b] values

    :param hex_string: #rrggbb
    :return: [r, g, b]
    """
    r = int(hex_string[1:3], 16)
    g = int(hex_string[3:5], 16)
    b = int(hex_string[5:7], 16)

    return [r, g, b]


def palette_from_dict(colour_dict):
    """
    Create a colour palette from dictionary
    https://stackoverflow.com/questions/59313853/image-from-array-with-dictionary-for-colors

    :param colour_dict:
    :return:
    """

    palette = []
    for i in np.arange(256):
        if i in colour_dict:
            rgb_value = convert_to_rgb(colour_dict[i])
            palette.extend(rgb_value)
        else:
            palette.extend([0, 0, 0])
    return palette


def save_png(pixel_array, output_file_str):
    """
    Save pixel array as png

    :param pixel_array: pixel array (integers)
    :param output_file_str: output file name
    """

    img_pil = Image.fromarray(pixel_array, 'P')

    # Set colour palette
    original_colours = colour_map.colour_map
    flipped_colours = {v: k for k, v in original_colours.items()}
    img_pil.putpalette(palette_from_dict(flipped_colours))

    # Save
    img_pil.save(output_file_str)

