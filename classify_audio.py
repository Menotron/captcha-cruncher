#!/usr/bin/env python3

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import cv2
import numpy
import string
import random
import argparse
import tensorflow as tf
from presets import Preset
import librosa as _librosa
import matplotlib.pyplot as plt
import tensorflow.keras as keras
import librosa.display as _display

#Setting Librosa presets for audio captchas
_librosa.display = _display
librosa = Preset(_librosa)
librosa['sr'] = 44100

def decode(characters, y):
    y = numpy.argmax(numpy.array(y), axis=2)[:,0]
    return ''.join([characters[x] for x in y])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--captcha-type', help='Specify the type of captcha, audio | image', default='image', type=str)
    parser.add_argument('--model-name', help='Model name to use for classification', type=str)
    parser.add_argument('--captcha-dir', help='Where to read the captchas to break', type=str)
    parser.add_argument('--output', help='File where the classifications should be saved', type=str)
    parser.add_argument('--symbols', help='File with the symbols to use in captchas', type=str)
    args = parser.parse_args()

    if args.model_name is None:
        print("Please specify the CNN model to use")
        exit(1)

    if args.captcha_dir is None:
        print("Please specify the directory with captchas to break")
        exit(1)

    if args.output is None:
        print("Please specify the path to the output file")
        exit(1)

    if args.symbols is None:
        print("Please specify the captcha symbols file")
        exit(1)

    symbols_file = open(args.symbols, 'r')
    captcha_symbols = symbols_file.readline().strip()
    symbols_file.close()

    print("Classifying captchas with symbol set {" + captcha_symbols + "}")

    # with tf.device('/cpu:0'):
    with tf.device('/device:GPU:0'):
        with open(args.output, 'w') as output_file:
            json_file = open(args.model_name+'.json', 'r')
            loaded_model_json = json_file.read()
            json_file.close()
            model = keras.models.model_from_json(loaded_model_json)
            model.load_weights(args.model_name+'.h5')
            model.compile(loss='categorical_crossentropy',
                          optimizer=keras.optimizers.Adam(1e-3, amsgrad=True),
                          metrics=['accuracy'])

            for x in os.listdir(args.captcha_dir):
                raw_data = None
                captcha_file = os.path.join(args.captcha_dir, x)
                
                if args.captcha_type.lower() == 'image':
                # load image and preprocess it
                    raw_data = cv2.adaptiveThreshold(cv2.imread(captcha_file,0),255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,11,2)

                elif args.captcha_type.lower() == 'audio':
                    y,sr = librosa.core.load(captcha_file)
                    M = librosa.feature.melspectrogram(y=y)
                    fig = plt.figure(figsize=(1.28, .64),dpi = 1024)
                    plt.axes([0., 0., 1., 1., ], frameon=False, xticks=[], yticks=[])
                    plot = librosa.display.specshow(librosa.power_to_db(M, ref=np.max),cmap='gray_r')
                    fig.canvas.draw()
                    audio_buffer = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(fig.canvas.get_width_height()[::-1] + (3,))
                    plt.close(fig)
                    raw_data = cv2.resize(cv2.cvtColor(audio_buffer, cv2.COLOR_BGR2GRAY), (128, 64))

                normalized_data = numpy.array(raw_data) / 255.0
    
                (h, w) = normalized_data.shape
                image = normalized_data.reshape([-1, h, w, 1])

                prediction = model.predict(image)
                output_file.write(x + ", " + decode(captcha_symbols, prediction) + "\n")

                print('Classified ' + x)

if __name__ == '__main__':
    main()
