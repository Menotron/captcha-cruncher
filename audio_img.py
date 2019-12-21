from os import path
import os
import numpy
from multiprocessing import Pool
import matplotlib.pyplot as plt
import librosa as _librosa
import librosa.display as _display
_librosa.display = _display
from presets import Preset
import cv2

librosa = Preset(_librosa)

# To change the default sampling rate, we can set the `sr` entry:
librosa['sr'] = 44100


def convert(audio_data, output_file):
    try:
        y, sr= librosa.core.load(audio_data)
        M = librosa.feature.melspectrogram(y=y)
        fig = plt.figure(figsize=(1.28, .64),dpi = 1024)
        plt.axes([0., 0., 1., 1., ], frameon=False, xticks=[], yticks=[])
        plot = librosa.display.specshow(librosa.power_to_db(M, ref=numpy.max),cmap='gray_r')
        fig.canvas.draw()
        audio_buffer = numpy.frombuffer(fig.canvas.tostring_rgb(), dtype=numpy.uint8).reshape(fig.canvas.get_width_height()[::-1] + (3,))
        plt.close(fig)
        raw_data = cv2.resize(audio_buffer, (128, 64))
        cv2.imwrite(output_file, raw_data)
     except Exception as e:
        print('processing {0}: {1}'.format(audio_data, e))
                

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src-dir', help='Source directory', type= str)
    parser.add_argument('--dest-dir', help='Destination directory', type = str)
    parser.add_argument('--n', help='Number to processes to run in parallel', type=int, default=4)
    args = parser.parse_args()

    if args.src_dir == args.dest_dir:
        print('source and destination directory must be different!')
        exit(1)

    if not os.path.exists(args.dest_dir):
        os.makedirs(args.dest_dir)

    process_args = []
    file_list = os.listdir(args.src_dir)
    for audio_file in file_list:
        src_fname_path = os.path.join(args.src_dir, audio_file)
        dest_fname = audio_file.replace('.mp3', '.png')
        dest_fname_path = os.path.join(args.dest_dir, dest_fname)
        process_args.append((src_fname_path, dest_fname_path))

    with Pool(args.n) as p:
        p.starmap(convert, process_args)

    exit(0)

if __name__ == '__main__':
    main()