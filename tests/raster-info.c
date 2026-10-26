/* SPDX-License-Identifier: GPL-2.0-only
 * Copyright (C) 2026 reverse-engineered-printer contributors
 */
/* Inspect real CUPS Raster input independently of the SpliX filter. */
#include <cups/raster.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *file = fopen(argv[1], "rb");
    if (!file) return 3;
    cups_raster_t *raster = cupsRasterOpen(fileno(file), CUPS_RASTER_READ);
    cups_page_header2_t header;
    unsigned pages = 0;
    printf("{\"pages\":[");
    while (cupsRasterReadHeader2(raster, &header)) {
        if (!header.cupsBytesPerLine || header.cupsBytesPerLine > 1048576) return 4;
        unsigned char *line = malloc(header.cupsBytesPerLine);
        if (!line) return 5;
        unsigned long long black = 0;
        for (unsigned y = 0; y < header.cupsHeight; ++y) {
            if (cupsRasterReadPixels(raster, line, header.cupsBytesPerLine) != header.cupsBytesPerLine) return 6;
            for (unsigned x = 0; x < header.cupsBytesPerLine; ++x)
                black += __builtin_popcount((unsigned)line[x]);
        }
        free(line);
        printf("%s{\"width\":%u,\"height\":%u,\"xdpi\":%u,\"ydpi\":%u,"
               "\"bits_per_color\":%u,\"color_space\":%u,\"compression\":%u,\"set_bits\":%llu}",
               pages ? "," : "", header.cupsWidth, header.cupsHeight,
               header.HWResolution[0], header.HWResolution[1], header.cupsBitsPerColor,
               header.cupsColorSpace, header.cupsCompression, black);
        ++pages;
    }
    printf("]}\n");
    cupsRasterClose(raster);
    fclose(file);
    return pages ? 0 : 7;
}
