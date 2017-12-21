#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output_directory', help='directory to write markermap images and config files')
    parser.add_argument('--width-m', default=1, type=float, help='width of map in meters')
    parser.add_argument('--height-m', default=1, type=float, help='height of map in meters')
    parser.add_argument('--page-width-m', default=0.19, type=float, help='width of page you are printing on')
    parser.add_argument('--page-height-m', default=0.25, type=float, help='height of page you are printing on')

    args = parser.parse_args()

    dictionary = 'ARUCO'  # has 1024 marker
    pixels_per_unit = 100
    units_per_margin = 1
    units_per_marker = 7
    m_per_marker = 0.02
    m_per_unit = m_per_marker / units_per_marker
    m_per_marker_plus_margin = (units_per_marker + units_per_margin) * m_per_unit
    # may slightly underestimate since there is one extra margin counted
    map_width = int(args.width_m / m_per_marker_plus_margin)
    map_height = int(args.height_m / m_per_marker_plus_margin)
    page_width = int(args.page_width_m / m_per_marker_plus_margin)
    page_height = int(args.page_height_m / m_per_marker_plus_margin)
    page_size = '{:d}:{:d}'.format(page_width, page_height)

    print("number of markers per page {:d}x{:d}".format(page_width, page_height))

    # there is one less margin than markers
    page_width_m = page_width * m_per_marker_plus_margin - m_per_unit
    page_height_m = page_height * m_per_marker_plus_margin - m_per_unit

    if not os.path.isdir(args.output_directory):
        os.mkdir(args.output_directory)

    page_height_mm = int(page_height_m * 1000)
    page_width_mm = int(page_width_m * 1000)
    print("print this page in portrait at exactly: width={:d}mm height={:d}mm".format(page_width_mm, page_height_mm))

    for page_idx, start_idx in enumerate(range(0, map_width * map_height, page_width * page_height)):
        image_filename = os.path.join(args.output_directory, "map-{:d}.png".format(page_idx))
        config_filename = os.path.join(args.output_directory, "map-config-{:d}.yml".format(page_idx))

        ids = str(start_idx)
        for i in range(start_idx + 1, start_idx + page_width * page_height):
            ids += ":" + str(i)

        cmd_args = ['aruco_create_markermap', page_size, image_filename, config_filename, '-d', dictionary, '-s',
                    str(pixels_per_unit), '-r', '0', '-ids', ids]

        devnull = open(os.devnull, 'w')
        subprocess.call(cmd_args, stdout=devnull)
        # subprocess.call(cmd_args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
