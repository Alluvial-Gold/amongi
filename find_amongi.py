from PIL import Image
import numpy as np
import pandas as pd

import create_frames

# place where main colour SHOULD be
amongus_1_main_mask = np.array([
    [0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 0],
    [0, 1, 1, 0, 0, 0],
    [0, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 0],
    [0, 0, 1, 0, 1, 0],
    [0, 0, 0, 0, 0, 0]
]).astype(np.bool)

# places where main colour CAN be
amongus_1_main_mask_2 = np.array([
    [1, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0],
    [1, 1, 0, 1, 0, 1]
]).astype(np.bool)

# places where visor colour SHOULD be
amongus_1_visor_mask = np.array([
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0]
]).astype(np.bool)

# places where visor colour CAN be
amongus_1_visor_mask_2 = np.array([
    [1, 1, 1, 1, 1, 1],
    [1, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 1],
    [1, 1, 0, 0, 0, 1],
    [1, 1, 0, 1, 0, 1],
    [1, 1, 1, 1, 1, 1]
]).astype(np.bool)


def find_amongus_1(pixel_array):
    main_colour = pixel_array[1, 2]
    visor_colour = pixel_array[2, 3]

    main_mask = pixel_array == main_colour
    visor_mask = pixel_array == visor_colour

    # combine actual colours & places where colours can be...
    check_main = np.array_equal(main_mask | amongus_1_main_mask_2, amongus_1_main_mask | amongus_1_main_mask_2)
    check_visor = np.array_equal(visor_mask | amongus_1_visor_mask_2, amongus_1_visor_mask | amongus_1_visor_mask_2)

    if check_main & check_visor:
        # pixels to copy
        full_amongus_mask = amongus_1_main_mask | amongus_1_visor_mask
        return_array = np.full(pixel_array.shape, 99).astype(np.uint8)
        return_array[full_amongus_mask] = pixel_array[full_amongus_mask]
        return True, return_array

    return False, None


def find_amongus_2(pixel_array, mask_series):
    main_colour = pixel_array[3, 3]
    visor_colour = pixel_array[mask_series['visor_y'], mask_series['visor_x']]

    main_mask = pixel_array == main_colour
    visor_mask = pixel_array == visor_colour

    # combine actual colours & places where colours can be...
    check_main = np.array_equal(main_mask | mask_series['main_okay'], mask_series['main'] | mask_series['main_okay'])
    check_visor = np.array_equal(visor_mask | mask_series['visor_okay'], mask_series['visor'] | mask_series['visor_okay'])

    if check_main & check_visor:
        # pixels to copy
        full_amongus_mask = mask_series['main'] | mask_series['visor']
        return_array = np.full(pixel_array.shape, 99).astype(np.uint8)
        return_array[full_amongus_mask] = pixel_array[full_amongus_mask]
        return True, return_array

    return False, None


def find_amongus(pixel_array, mask_df):

    for index, row in mask_df.iterrows():
        found, found_pixels = find_amongus_2(pixel_array, row)
        if found:
            return found, found_pixels

    return False, None


def flip_rotate(orig_array, rot_idx, flip_idx):
    array = np.asarray(orig_array)
    array = np.rot90(array, rot_idx)
    if flip_idx == 1:
        array = np.fliplr(array)
    return array


def search_image(image_path, output_image_path):
    img = Image.open(image_path)
    pixel_array = np.asarray(img)

    # Create array for output - fill with 0 (black)
    final_array = np.zeros(pixel_array.shape, dtype=np.uint8)

    # Add 'empty' rows around the edge
    pad_amount = 2
    pixel_array = np.pad(pixel_array, ((pad_amount, pad_amount), (pad_amount, pad_amount)), 'constant', constant_values=32)

    amongi_count = 0

    # amongus masks - 7x7
    search_height = 7
    search_width = 7

    mask_path = r'.\data\scratch\amongi_masks.png'
    mask_img = Image.open(mask_path)
    mask_array = np.asarray(mask_img).astype(np.bool)
    mask_array = np.invert(mask_array)

    main_masks = []
    main_okay_masks = []
    visor_masks = []
    visor_okay_masks = []

    visor_x = []
    visor_y = []

    for type_idx in range(5):
        j = 7 * type_idx

        for rot_idx in range(4):
            for flip_idx in range(2):
                main_masks.append(flip_rotate(mask_array[0:7, j:j+7], rot_idx, flip_idx))
                main_okay_masks.append(flip_rotate(mask_array[7:14, j:j+7], rot_idx, flip_idx))
                visor_masks.append(flip_rotate(mask_array[14:21, j:j+7], rot_idx, flip_idx))
                visor_okay_masks.append(flip_rotate(mask_array[21:28, j:j+7], rot_idx, flip_idx))

                # TODO make this better
                if flip_idx == 0:
                    visor_x.append(3 if rot_idx % 2 == 0 else 1 + rot_idx)
                    visor_y.append(3 if rot_idx % 2 == 1 else 2 + rot_idx)
                else:
                    visor_x.append(3 if rot_idx % 2 == 0 else 5 - rot_idx)
                    visor_y.append(3 if rot_idx % 2 == 1 else 2 + rot_idx)


    mask_df = pd.DataFrame({'main': main_masks, 'main_okay': main_okay_masks,
                            'visor': visor_masks, 'visor_okay': visor_okay_masks,
                            'visor_x': visor_x, 'visor_y': visor_y})

    for row_idx in range(pixel_array.shape[0] - (search_height - 1)):
        for col_idx in range(pixel_array.shape[1] - (search_width - 1)):
            sub_array = pixel_array[row_idx:row_idx + search_height, col_idx:col_idx + search_width]

            # skip all-white blocks
            if np.all(sub_array == 31):
                continue

            found, found_pixels = find_amongus(sub_array, mask_df)

            if found:
                print('Found at {0}, {1}'.format(row_idx, col_idx))
                amongi_count += 1

                # add to image...
                for type_idx in range(search_height):
                    for j in range(search_width):
                        if found_pixels[type_idx][j] != 99:
                            # todo find better way to do this
                            final_array[row_idx + type_idx - pad_amount][col_idx + j - pad_amount] = found_pixels[type_idx][j]

    print('There are {0} amongi among us'.format(amongi_count))

    # create image...
    create_frames.save_png(final_array, output_image_path)


if __name__ == '__main__':
    # search_image(r'.\data\scratch\test_canvas_5.png', r'.\data\output\test\test_canvas_5_out.png')
    search_image(r"D:\Coding\amongi\data\output\png_1m\png_1649112370315000000.png",
                 r'.\data\output\test\big_test_1.png')
