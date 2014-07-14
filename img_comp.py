#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Hitoshi Yamauchi
#
# PIL image comparison command: numpy version
#

import argparse, numpy
from PIL import Image

class ImgComp(object):
    """Image comparison class
    """
    def __init__(self, opt):
        """constructor

        option:
        'save_diff_fname': str, save difference image filename.
        """
        self.__img1 = None
        self.__img2 = None
        self.__diff_pixel_count = 0
        self.__opt = opt


    def compare(self, img1fname, img2fname, err_tol):
        
        self.__img1 = Image.open(img1fname)
        self.__img2 = Image.open(img2fname)

        if(self.__img1.size != self.__img2.size):
            print 'image size differ [{0}] != [{1}]'.format(self.__img1.size,
                                                            self.__img2.size)
            return False

        a1 = numpy.asarray(self.__img1)
        a2 = numpy.asarray(self.__img2)
        diff = numpy.abs(a1 - a2)
        pix_diff_array = diff.reshape(diff.shape[0] * diff.shape[1], diff.shape[2])
        diff_count = numpy.sum(numpy.sum(numpy.transpose(pix_diff_array > 0)) > 0)

        resol = self.__img1.size
        pixel_count =  float(resol[0] * resol[1])
        diff_ratio = float(diff_count) / pixel_count
        
        if(True):
            print 'image differs: diff count: {0} of {1}. error {2} >= {3}'.\
                format(diff_count, pixel_count, diff_ratio, err_tol)
            if(('save_diff_fname' in self.__opt) and (self.__opt['save_diff_fname'])):
                save_diff_fname = 'diff.png'
                if('save_diff_fname' not in self.__opt):
                    print 'Error! no save_diff_fname specified. use diff.png.'
                else:
                    save_diff_fname = self.__opt['save_diff_fname']

                img3 = Image.fromarray(diff)
                img3.save(save_diff_fname)
                print 'save difference image to [{0}]'.format(save_diff_fname)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(epilog="""
Example: python ImgCompNumpy.py -v --img1 img_1.jpg --img2 img_2.png -e 0.001
""")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="increase output verbosity")
    parser.add_argument("--img1", type=str, 
                        help="image compaison source 1 filename")
    parser.add_argument("--img2", type=str, 
                        help="image compaison source 2 filename")
    parser.add_argument("-e", "--error_tolerance", type=float,
                        help="error tolerance. How much (ratio) pixel can be differ?")
    parser.add_argument("--save_diff_if_error", action='store_true',
                        help="When the error is detected, save the difference images.")
    parser.add_argument("--save_diff_fname", type=str, default='diff_result.png',
                        help="save difference image filename. " + 
                        "only effective save_diff_if_error is True.")


    args = parser.parse_args()

    if(args.verbose):
        print "verbose: {0}".format(args.verbose)
        print "img1: {0}".format(args.img1)
        print "img2: {0}".format(args.img2)
        print "error_tolerance: {0}".format(args.error_tolerance)
        print "save_diff_if_error: {0}".format(args.save_diff_if_error)
        print "save_diff_fname: {0}".format(args.save_diff_fname)

    opt = {
        'verbose': args.verbose,
        'save_diff_fname': args.save_diff_fname,
        'save_diff_if_error': args.save_diff_if_error,
        }

    ic = ImgComp(opt)
    ic.compare(args.img1, args.img2, args.error_tolerance)

    