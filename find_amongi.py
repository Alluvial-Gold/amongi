from PIL import Image
import numpy as np
import csv
import math

import os
from os import listdir
from os.path import isfile, join

import multiprocessing

import save_png


def find_big_amongus(middle_array, pixel_array, middle_mask_list, mask_list):
    for i in range(len(middle_mask_list)):
        valid = check_center_pixels_big_amongus(middle_array, middle_mask_list[i])
        if valid:
            # check associated masks for the 3 types
            for j in range(3):
                found, found_pixels, main_colour, visor_colour = check_amongus_pixels(pixel_array, mask_list[j * 8 + i])
                if found:
                    amongus_type = ('b' + str(j * 8 + i), main_colour, visor_colour)
                    return found, found_pixels, amongus_type
            return False, None, None
    return False, None, None


def find_small_amongus(middle_array, pixel_array, middle_mask_list, mask_list):
    for i in range(len(middle_mask_list)):
        valid = check_middle_pixels_small_amongus(middle_array, middle_mask_list[i])
        if valid:
            # check associated masks for the 2 types
            for j in range(2):
                found, found_pixels, main_colour, visor_colour = check_amongus_pixels(pixel_array, mask_list[j * 8 + i])
                if found:
                    amongus_type = ('s' + str(j * 8 + i), main_colour, visor_colour)
                    return found, found_pixels, amongus_type
            return False, None, None
    return False, None, None


def check_center_pixels_big_amongus(middle_array, middle_mask_tuple):
    # only need to check visor pixels - already checked that there are 7 main colour pixels
    visor_colour = middle_array[middle_mask_tuple[7], middle_mask_tuple[6]]
    pixel_visor_mask = middle_array == visor_colour
    check_visor = (pixel_visor_mask == middle_mask_tuple[5]).all()

    return check_visor


def check_middle_pixels_small_amongus(middle_array, middle_mask_tuple):
    # ignore 'okay' mask - no 'okay' pixels in center
    pixel_main_mask = middle_array == middle_array[1, 1]
    check_main = (pixel_main_mask == middle_mask_tuple[0]).all()

    if ~check_main:
        return False

    visor_colour = middle_array[middle_mask_tuple[7], middle_mask_tuple[6]]
    pixel_visor_mask = middle_array == visor_colour
    check_visor = ((pixel_visor_mask | middle_mask_tuple[4]) == middle_mask_tuple[5]).all()

    return check_visor


def check_amongus_pixels(pixel_array, mask_tuple):
    main_colour = pixel_array[3, 3]
    visor_colour = pixel_array[mask_tuple[7], mask_tuple[6]]

    pixel_main_mask = pixel_array == main_colour
    pixel_visor_mask = pixel_array == visor_colour

    # combine actual colours & places where colours can be...
    check_main = ((pixel_main_mask | mask_tuple[1]) == mask_tuple[2]).all()
    check_visor = ((pixel_visor_mask | mask_tuple[4]) == mask_tuple[5]).all()

    if check_main & check_visor:
        # pixels to copy
        return_array = np.where(mask_tuple[8], pixel_array, 99)
        return True, return_array, main_colour, visor_colour

    return False, None, None, None


def flip_rotate(orig_array, rot_idx, flip_idx):
    array = np.asarray(orig_array)
    array = np.rot90(array, rot_idx)
    if flip_idx == 1:
        array = np.fliplr(array)
    return array


def search_image(image_path, output_image_path, search_type=2):
    # Load data
    img = Image.open(image_path)
    pixel_array = np.asarray(img)

    # Create array for output - fill with 0 (black)
    final_array = np.zeros(pixel_array.shape, dtype=np.uint8)
    output_list = []

    # Add 'empty' rows around the edge
    pad_amount = 2
    pixel_array = np.pad(pixel_array, ((pad_amount, pad_amount), (pad_amount, pad_amount)),
                         'constant', constant_values=32)

    # Amongus masks - 7x7
    search_height = 7
    search_width = 7
    mask_list = get_masks()
    mask_list_big = mask_list[0:16] + mask_list[24:32]
    mask_list_small = mask_list[16:24] + mask_list[32:40]

    middle_mask_list = get_middle_masks()
    middle_mask_list_big = middle_mask_list[0:8]
    middle_mask_list_small = middle_mask_list[8:16]

    # search range based on type...
    row_range = pixel_array.shape[0] - (search_height - 1)
    column_range = pixel_array.shape[1] - (search_width - 1)

    if search_type == 0:
        # only search top left
        row_range = math.ceil(pixel_array.shape[0] / 2) + pad_amount - (search_height - 1)
        column_range = math.ceil(pixel_array.shape[1] / 2) + pad_amount - (search_width - 1)
    elif search_type == 1:
        # only search top
        row_range = math.ceil(pixel_array.shape[0] / 2) + pad_amount - (search_height - 1)

    for row_idx in range(row_range):
        for col_idx in range(column_range):
            sub_array = pixel_array[row_idx:row_idx + search_height, col_idx:col_idx + search_width]
            middle_array = sub_array[2:5, 2:5]

            # Skip frames without enough 'main'-colour pixels in the center
            theoretical_main_colour_pixels = np.count_nonzero(middle_array == middle_array[1, 1])

            if theoretical_main_colour_pixels == 7:
                found, found_pixels, amongus_type = find_big_amongus(middle_array, sub_array, middle_mask_list_big,
                                                                     mask_list_big)
            elif theoretical_main_colour_pixels == 6:
                found, found_pixels, amongus_type = find_small_amongus(middle_array, sub_array, middle_mask_list_small,
                                                                       mask_list_small)
            else:
                continue

            if found:
                # Update image
                add_to_image(col_idx, final_array, found_pixels, pad_amount, row_idx, search_height, search_width)

                # Update array - type, main colour, visor colour
                output_list.append(amongus_type)

    # Save image
    save_png.save_png(final_array, output_image_path)

    # Save array
    output_data_path = output_image_path + '.txt'
    with open(output_data_path, 'w') as fp:
        fp.write('\n'.join('%s %s %s' % x for x in output_list))


def add_to_image(col_idx, final_array, found_pixels, pad_amount, row_idx, search_height, search_width):
    for type_idx in range(search_height):
        for j in range(search_width):
            if found_pixels[type_idx][j] != 99:
                # todo find better way to do this
                final_array[row_idx + type_idx - pad_amount][col_idx + j - pad_amount] = \
                    found_pixels[type_idx][j]


def get_masks():
    mask_path = r'.\data\scratch\amongi_masks.png'
    mask_img = Image.open(mask_path)
    mask_array = np.asarray(mask_img).astype(np.bool)
    mask_array = np.invert(mask_array)

    tuple_list = []

    for type_idx in range(5):
        j = 7 * type_idx

        for rot_idx in range(4):
            for flip_idx in range(2):
                main_mask = flip_rotate(mask_array[0:7, j:j + 7], rot_idx, flip_idx)
                main_okay_mask = flip_rotate(mask_array[7:14, j:j + 7], rot_idx, flip_idx)
                main_combo_mask = np.logical_or(main_mask, main_okay_mask)

                visor_mask = flip_rotate(mask_array[14:21, j:j + 7], rot_idx, flip_idx)
                visor_okay_mask = flip_rotate(mask_array[21:28, j:j + 7], rot_idx, flip_idx)
                visor_combo_mask = np.logical_or(visor_mask, visor_okay_mask)

                combined_amongi_mask = np.logical_or(main_mask, visor_mask)

                visor_x = (3 if rot_idx % 2 == 0 else 1 + rot_idx) \
                    if flip_idx == 0 \
                    else (3 if rot_idx % 2 == 0 else 5 - rot_idx)
                visor_y = (3 if rot_idx % 2 == 1 else 2 + rot_idx) \
                    if flip_idx == 0 \
                    else (3 if rot_idx % 2 == 1 else 2 + rot_idx)

                t = (main_mask, main_okay_mask, main_combo_mask,
                     visor_mask, visor_okay_mask, visor_combo_mask,
                     visor_x, visor_y, combined_amongi_mask)
                tuple_list.append(t)

    return tuple_list


def get_middle_masks():
    mask_path = r'.\data\scratch\amongi_masks.png'
    mask_img = Image.open(mask_path)
    mask_array = np.asarray(mask_img).astype(np.bool)
    mask_array = np.invert(mask_array)

    tuple_list = []

    # for middle masks, only need 1st (7 main / 2 visor) & 3rd (6 main / 2 visor / 1 other)

    for type_idx in [0, 2]:
        j = 7 * type_idx

        for rot_idx in range(4):
            for flip_idx in range(2):
                main_mask = flip_rotate(mask_array[0:7, j:j + 7], rot_idx, flip_idx)
                main_okay_mask = flip_rotate(mask_array[7:14, j:j + 7], rot_idx, flip_idx)
                main_combo_mask = np.logical_or(main_mask, main_okay_mask)

                visor_mask = flip_rotate(mask_array[14:21, j:j + 7], rot_idx, flip_idx)
                visor_okay_mask = flip_rotate(mask_array[21:28, j:j + 7], rot_idx, flip_idx)
                visor_combo_mask = np.logical_or(visor_mask, visor_okay_mask)

                combined_amongi_mask = np.logical_or(main_mask, visor_mask)

                main_mask = main_mask[2:5, 2:5]
                main_okay_mask = main_okay_mask[2:5, 2:5]
                main_combo_mask = main_combo_mask[2:5, 2:5]

                visor_mask = visor_mask[2:5, 2:5]
                visor_okay_mask = visor_okay_mask[2:5, 2:5]
                visor_combo_mask = visor_combo_mask[2:5, 2:5]

                combined_amongi_mask = combined_amongi_mask[2:5, 2:5]

                visor_x = (3 if rot_idx % 2 == 0 else 1 + rot_idx) \
                    if flip_idx == 0 \
                    else (3 if rot_idx % 2 == 0 else 5 - rot_idx)
                visor_y = (3 if rot_idx % 2 == 1 else 2 + rot_idx) \
                    if flip_idx == 0 \
                    else (3 if rot_idx % 2 == 1 else 2 + rot_idx)

                visor_x -= 2
                visor_y -= 2

                t = (main_mask, main_okay_mask, main_combo_mask,
                     visor_mask, visor_okay_mask, visor_combo_mask,
                     visor_x, visor_y, combined_amongi_mask)
                tuple_list.append(t)

    return tuple_list


def test_1(image_path, output_image_path, search_type=2):
    print(image_path)
    print(output_image_path)
    print(search_type)
    print('---------')


def go_through_all_images(folder_path, output_folder_path, first_break, second_break):
    """

    :param folder_path:
    :param output_folder_path:
    :param first_break: frame number when second part starts
    :param second_break: frame number when bottom part starts
    :return:
    """
    png_files = [f for f in listdir(folder_path) if isfile(join(folder_path, f))]
    png_files = sorted(png_files)

    full_file_thing = [(
        os.path.join(folder_path, png_file),
        os.path.join(output_folder_path, os.path.splitext(png_file)[0] + "_found.png"),
        0 if idx < first_break else (1 if idx < second_break else 2)
    ) for idx, png_file in enumerate(png_files)]

    # Create a multiprocessing Pool
    pool = multiprocessing.Pool()

    # process data_inputs iterable with pool
    pool.starmap(search_image, full_file_thing)


if __name__ == '__main__':
    # search_image(r'.\data\scratch\test_canvas_5.png', r'.\data\output\test\test_canvas_5_out.png')
    # search_image(r"D:\Coding\amongi\data\output\png_1m\png_1649112370315000000.png", r'.\data\output\test\big_test_1.png')

    go_through_all_images(r'.\data\output\png_1m', r'.\data\output\found_png_1m', 1600, 3200)



