# -*- coding: utf-8 -*-
"""
Created on Thu Aug 25 15:31:42 2016

@author: dcantor
"""
import errno
import os,shutil
import zipfile

import Image
import nibabel as nib
import numpy as np
from PIL import ImageFilter
from scipy import misc
from scipy.misc import bytescale

from deephisto import Locations, Console




class ImageUtils:
 
    def __init__(self, locations):
        if locations == None or not isinstance(locations, Locations):
            raise 'You must provide a valid ImageLocations object to initialize the ImageUtils object'
    
        self.locations = locations
        self.subject = self.locations.subject
    
    @staticmethod
    def load_nifti_image(filename):
        """
        Loads a nifti image and returns the data as a multidimensional numpy array
        """
        img = nib.load(filename)
        data = img.get_data()
        return data

    @staticmethod
    def data_to_unscaled_rgb(data):  #  used to create the GROUND TRUTH PNGs (Histology)
        w, h = data.shape
        ret = np.empty((w, h, 3), dtype=np.uint8)
        ret[:, :, 0] = data
        ret[:, :, 1] = data
        ret[:, :, 2] = data
        return ret

    @staticmethod
    def data_to_bytescale_rgb(data): # used to create the SOURCE PNGs (MRI, FA, MD)
        """
        Converts a single-channel grayscale image to a 3-channel image that can be 
        then saved as a  PNG        
        """
        im = bytescale(data)
        w, h = im.shape
        ret = np.empty((w,h,3), dtype=np.uint8)
        ret[:,:,0] = im
        ret[:,:,1] = im
        ret[:,:,2] = im
        return ret


    # @staticmethod
    # def rgb_to_single(data, channel):
    #     w,h = data.shape[0:2]
    #     ret = np.empty((w,h))
    #     ret[:,:] = data[:,:,channel]
    #     return ret

    # def image_to_gray(data):
    #     """
    #     Converts a PNG image to a single-channel grayscale image
    #     """
    #     r, g, b = data[:,:,0], data[:,:,1],data[:,:,2]
    #     gray = 0.2989 * r + 0.5870 *g + 0.1140*b
    #     return gray
    
    def set_subject(self, subject):
        self.subject = subject
        self.locations.set_subject(subject)
    
  
    def load_mask_png(self, index):
        """
        index: index of the  mask to retrieve
        """
        return misc.imread(self.locations.get_mask_location(index))      
        

    def get_binary_mask(self,index):
        """
        Reads a PNG mask (color) and returns a binary mask where elements in the mask
        are set to 255 and elements in the background are set to 0
        
        index:  index of the mask to retrieve
        """
        mask = self.load_mask_png(index)
        (rows,cols) = np.where(mask>0)[0:2] #pixels in mask disregarding the color
        new_mask = np.zeros(shape=mask.shape[0:2], dtype=np.uint8)
        new_mask[(rows,cols)] = 255
        return new_mask


    def get_dynrange_histo(self):
        """
        :return: a (min,max) tuple indicating the dynamic range of the histo map
        """
        if self.subject is None:
            print Console.WARNING + 'You need to specify a subject first' + Console.ENDC
            return
        #fmap_img = ImageUtils.load_nifti_image(self.locations.HIST_FMAP)
        #return (int(fmap_img.min()), int(fmap_img.max()))

        #look only through the slices that are masked
        indices = self.get_annotation_indices()
        print 'Recovering dynamic range for histo from slices %s'%indices
        max = -1
        min = 10000000
        for idx in indices:
            data = self.load_unscaled_histo_png_image(idx)
            print data.min(), data.max()
            if data.min() < min:
                min = data.min()

            if data.max() > max:
                max = data.max()

        print 'Dynamic Range:  (%d, %d)'%(min,max)

        return min, max




    def create_png_images(self):
        """
        Loads the feature map (histology image) and creates the PNGs for all the
        source and histology images
        """
        if self.subject is None:
            print Console.WARNING + 'You need to specify a subject first' + Console.ENDC
            return

        check_dir = self.locations.check_dir
        check_dir(self.locations.HISTO_PNG_U)
        check_dir(self.locations.HISTO_PNG)
        check_dir(self.locations.SOURCE_PNG)



        fmap_img = ImageUtils.load_nifti_image(self.locations.HIST_FMAP) #loading subject nifti files
        volumes = []
        try:
            for s in self.locations.SOURCES:
                volumes.append(ImageUtils.load_nifti_image(s))
        except IOError as e:
            print Console.FAIL + 'There are errors loading nifi files for subject %s'%self.subject + Console.ENDC
            return False
        

        num_slices = volumes[0].shape[2] #use first volume to check expected number of slices

        print 'Creating input PNGs for %s'%self.subject
        for k, vol in enumerate(volumes):
            for i in range(num_slices):
                imslice = ImageUtils.data_to_bytescale_rgb(vol[:, :, i])
                im = Image.fromarray(imslice)
                im.save(self.locations.SOURCE_PNG % (i, self.locations.LABELS[k]))

        
        print 'Creating histology PNGs for %s'%self.subject
        for i in range(num_slices):

            im_unscaled = ImageUtils.data_to_unscaled_rgb(fmap_img[:, :, i]);  #keeps the original values
            im_unscaled = Image.fromarray(im_unscaled)
            im_unscaled = im_unscaled.filter(ImageFilter.GaussianBlur(radius=2))  #Filter requested by Ali Khan
            im_unscaled.save(self.locations.HISTO_PNG_U % i)

            im_scaled = ImageUtils.data_to_bytescale_rgb(fmap_img[:,:,i]); # bytescaled histology
            im_scaled = Image.fromarray(im_scaled)
            im_scaled = im_scaled.filter(ImageFilter.GaussianBlur(radius=2))  #Filter requested by Ali Khan
            im_scaled.save(self.locations.HISTO_PNG % i)

        print
        return True
    
 
    def load_source_png_images(self, num_slice):
        """
        Loads the respective source png images for the slice being analyzed
        """
        if self.subject is None:
            print Console.WARNING + 'You need to specify a subject first' + Console.ENDC
            return
        data = []    
        for l in self.locations.LABELS:
            slice_file = self.locations.SOURCE_PNG % (num_slice, l)
            
            #print 'Loading Input Image \t\t%s'%slice_file 
            slice_data = misc.imread(slice_file) 
            data.append(slice_data)
            
        return data #images in the same order as labels

    def load_multichannel_input(self, num_slice):
        """
        Creates a multi-channel array with all the inputs:
         R->MRI
         G->FA
         B->MD
         for now..
        """
        data = np.array(self.load_source_png_images(num_slice))
        items, w, h, channels = data.shape
        multi = np.empty((w,h,channels))
        assert items == channels, 'The number of images must be equal to the number of channels'
        for i in range(0,items):
            multi[:,:,i] = data[i,:,:,0]
        return multi
    
    def load_unscaled_histo_png_image(self, num_slice):
        """
        Loads the respective Histology png for the slice being analyzed
        """
        if self.subject is None:
            print Console.WARNING + 'You need to specify a subject first' + Console.ENDC
            return
        data = []
        hfile = self.locations.HISTO_PNG_U % (num_slice)
        data = misc.imread(hfile)

        return data #png histology

    def load_bytescaled_histo_png_image(self, num_slice):
        """
        Loads the respective Histology png for the slice being analyzed
        """
        if self.subject is None:
            print Console.WARNING + 'You need to specify a subject first' + Console.ENDC
            return
        data = []
        hfile = self.locations.HISTO_PNG % (num_slice)
        data = misc.imread(hfile)

        return data  # png histology

 
    def unpack_annotations(self):
        url = self.locations.ANNOTATIONS_ZIP

        shutil.rmtree(self.locations.MASK_DIR)
        os.makedirs(self.locations.MASK_DIR)

        try:
            zipf = zipfile.ZipFile(url)
            zipf.extractall(self.locations.MASK_DIR)
            print Console.OKBLUE + 'All annotations have been extracted for %s'%self.subject + Console.ENDC
        except IOError as e:
            if e.errno != errno.ENOENT: raise e
            else:
                print 'No annotations yet for %s'%self.subject
        
    def get_annotation_indices(self):
       files = [fn for fn in os.listdir(self.locations.MASK_DIR) if fn.endswith('.png')]
       indices = []
       for fn in files:
           index  = int(fn.split('_')[2])  #A_S_5_t_HI.png = A, S, 5, t, HI.png
           indices.append(index)
           indices.sort()
       return indices





        
        