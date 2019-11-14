#!/usr/bin/env python3

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import shutil
import numpy as np
import argparse

def copy_files(t_data_dir,v_data_dir,sp):
	files = os.listdir(t_data_dir)
	for f in files:
		if np.random.rand(1) < (sp / 100):
			shutil.copy(t_data_dir + '/'+ f, v_data_dir + '/'+ f)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--training-data-dir', help='Where to read the training data to split', type=str)
    parser.add_argument('--validation-data-dir', help='where the validation dataset should be saved', type=str)
    parser.add_argument('--split-percentage', help='Percentage of training dataset to be randomly sampled for validation', type=int)
    args = parser.parse_args()

    if args.training_data_dir is None:
        print("Please specify the directory with training data to split")
        exit(1)
    
    if args.validation_data_dir is None:
        print("Please specify the directory where the validation dataset should be saved")
        exit(1)
    
    if args.split_percentage is None:
        print("")
        exit(1)

    copy_files(args.training_data_dir, args.validation_data_dir, args.split_percentage)
    

if __name__ == '__main__':
    main()