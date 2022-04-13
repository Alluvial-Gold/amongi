from PIL import Image
import numpy as np

import save_png


def find_amongus_2(pixel_array, mask_tuple):
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
        return True, return_array

    return False, None


def find_amongus(pixel_array, mask_list):

    for i in range(len(mask_list)):
        found, found_pixels = find_amongus_2(pixel_array, mask_list[i])
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
    pixel_array = np.pad(pixel_array, ((pad_amount, pad_amount), (pad_amount, pad_amount)),
                         'constant', constant_values=32)

    amongi_count = 0

    # Amongus masks - 7x7
    search_height = 7
    search_width = 7
    mask_list = get_masks()

    for row_idx in range(pixel_array.shape[0] - (search_height - 1)):
        for col_idx in range(pixel_array.shape[1] - (search_width - 1)):
            sub_array = pixel_array[row_idx:row_idx + search_height, col_idx:col_idx + search_width]

            # skip all-white blocks
            # if np.all(sub_array == 31):
            #     continue

            found, found_pixels = find_amongus(sub_array, mask_list)

            if found:
                amongi_count += 1

                # add to image...
                for type_idx in range(search_height):
                    for j in range(search_width):
                        if found_pixels[type_idx][j] != 99:
                            # todo find better way to do this
                            final_array[row_idx + type_idx - pad_amount][col_idx + j - pad_amount] = \
                                found_pixels[type_idx][j]

    print('There are {0} amongi among us'.format(amongi_count))

    # create image...
    save_png.save_png(final_array, output_image_path)


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


if __name__ == '__main__':
    search_image(r'.\data\scratch\test_canvas_5.png', r'.\data\output\test\test_canvas_5_out.png')
    # search_image(r"D:\Coding\amongi\data\output\png_1m\png_1649112370315000000.png", r'.\data\output\test\big_test_1.png')

