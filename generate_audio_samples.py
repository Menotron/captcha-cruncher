#!/usr/bin/env python3

import warnings
import os
import re
import random
import numpy as np
import argparse
from time import sleep
from multiprocessing.dummy import Pool as ThreadPool 
from google.cloud import texttospeech
import azure.cognitiveservices.speech as speechsdk
import boto3
from gtts import gTTS

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

def scramble_file_name(file_name):
    import hashlib
    m = hashlib.sha1()
    m.update(file_name.encode('utf- 8'))
    return m.hexdigest()

def gc_synthesize_text(client, text, voice_name, speaking_rate = 1, pitch_shift = 0):
    """Synthesizes speech from the input string of text."""
    input_text = texttospeech.types.SynthesisInput(text=text)

    voice = texttospeech.types.VoiceSelectionParams(
        name=voice_name,
        language_code='en-US',
        ssml_gender=texttospeech.enums.SsmlVoiceGender.FEMALE)

    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3,
        speaking_rate=speaking_rate,
        pitch=pitch_shift)

    return client.synthesize_speech(input_text, voice, audio_config)

def azure_speech_synthesis_to_mp3_file(speech_config, text, voice, output_file):
    """performs speech synthesis to an mp3 file"""
    # Sets the synthesis output format.
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
    speech_config.speech_synthesis_voice_name = voice
    # Creates a speech synthesizer using file as audio output.
    file_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=file_config)

    result = speech_synthesizer.speak_text_async(text).get()
        # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}], and the audio was saved to [{}]".format(text, output_file))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))

def create_filename(scramble, output_dir, text):
    file_name_scrambled = text
    if scramble:
        file_name_scrambled = scramble_image_name(text)
    audio_file_path = os.path.join(output_dir, text, file_name_scrambled+'.mp3')
    if os.path.exists(audio_file_path):
        version = 1
        while os.path.exists(os.path.join(output_dir, text, file_name_scrambled + '_' + str(version) + '.mp3')):
            version += 1
        audio_file_path = os.path.join(output_dir, text, file_name_scrambled + '_' + str(version) + '.mp3')
    if not os.path.exists(os.path.dirname(audio_file_path)):
        try:
            os.makedirs(os.path.dirname(audio_file_path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    print('writing synthesized audio to ', audio_file_path)
    return audio_file_path

def write_audio(response, file_name):
    # The response's audio_content is binary.
    with open(file_name, 'wb') as out:
        out.write(response)
        print('Audio content written to file ' + file_name)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api', help='Which API to use. Choose from (gc/azure/aws)', type=str)
    parser.add_argument('--api-key', help='API_KEY or the path to the Key fiile', type=str)
    parser.add_argument('--output-dir', help='Where to store the generated audio samples', type=str)
    parser.add_argument('--length', help='Length of captchas in characters', type=int)
    parser.add_argument('--count', help='How many captchas to generate', type=int)
    parser.add_argument('--scramble', help='Whether to scramble image names', default=False, action='store_true')
    parser.add_argument('--symbols', help='File with the symbols to use in captchas', type=str)
    args = parser.parse_args()

    if args.api is None:
        print("Please specify the cloud platform to use")
        exit(1)

    if args.api_key is None:
        print("Please specify the API_KEY or the path to the Key fiile")
        exit(1)

    if args.output_dir is None:
        print("Please specify the samples output directory")
        exit(1)

    if args.length is None:
        print("Please specify the captcha length")
        exit(1)

    if args.count is None:
        print("Please specify the captcha count to generate")
        exit(1)

    if args.symbols is None:
        print("Please specify the captcha symbols file")
        exit(1)

    symbols_file = open(args.symbols, 'r')
    symbols = symbols_file.readline().strip()

    if not os.path.exists(args.output_dir):
        print("Creating output directory " + args.output_dir)
        os.makedirs(args.output_dir)

    for i in range(args.count):
        captcha_text = ''.join([random.choice(symbols) for j in range(args.length)])
    
    # GOOGLE Cloud TTS API    
        if args.api.lower() == "gc": 
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = args.api_key
            client = texttospeech.TextToSpeechClient()
             
            voice_list = []
            voices = client.list_voices()

            for voice in voices.voices:
                gender = texttospeech.enums.SsmlVoiceGender(voice.ssml_gender)
                if format(gender.name) == 'FEMALE':
                    for language_code in voice.language_codes:
                        if re.match('^en-.*', language_code) is not None:
                            voice_list.append(format(voice.name))

            for voice_name in voice_list:
                print('Google TextToSpeech API voice ', voice_name)
                response = gc_synthesize_text(client, captcha_text, voice_name).audio_content
                file_name = create_filename(args.scramble, args.output_dir, captcha_text)
                write_audio(response, file_name)
            sleep(0.2)

# MICROSOFT Azure Cloud Cognitive Speeh API
        elif args.api.lower() == "azure":
            voice_list = ["Microsoft Server Speech Text to Speech Voice (en-AU, Catherine)","Microsoft Server Speech Text to Speech Voice (en-AU, HayleyRUS)",
            "Microsoft Server Speech Text to Speech Voice (en-CA, Linda)","Microsoft Server Speech Text to Speech Voice (en-CA, HeatherRUS)",
            "Microsoft Server Speech Text to Speech Voice (en-GB, Susan, Apollo)","Microsoft Server Speech Text to Speech Voice (en-GB, HazelRUS)",
            "Microsoft Server Speech Text to Speech Voice (en-US, ZiraRUS)","Microsoft Server Speech Text to Speech Voice (en-US, JessaRUS)",
            "Microsoft Server Speech Text to Speech Voice (en-US, Jessa24kRUS)"]
            speech_key, service_region = args.api_key, "westeurope"
            speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
            for voice in voice_list:
                file_name = create_filename(args.scramble, args.output_dir, captcha_text)
                azure_speech_synthesis_to_mp3_file(speech_config, " ".join(captcha_text), voice, file_name)
            sleep(0.5)

# AWS Polly Speeh API
        elif args.api.lower() == 'aws':
            voice_list = ['Salli', 'Joanna', 'Kendra', 'Kimberly', 'Amy', 'Emma','Nicole','Raveena','Aditi']
            polly_client = boto3.Session(
                aws_access_key_id= "AKIA3TQLBVKRT5JS7Y4O",aws_secret_access_key=args.api_key,region_name='eu-west-1').client('polly')
            for voice in voice_list: 
                response = polly_client.synthesize_speech(VoiceId=voice,
                    Engine = "standard",
                    OutputFormat='mp3', 
                    Text = " ".join(captcha_text))
                response = response['AudioStream'].read()
                file_name = create_filename(args.scramble, args.output_dir, captcha_text)
                write_audio(response, file_name)

# GTTS Library
        elif args.api.lower() == 'gtts':
            pool = ThreadPool(4)
            pool.map(my_function, my_array)
            gtts_instance = gTTS(text=captcha_text, lang='en', slow=False)
            file_name = create_filename(args.scramble, args.output_dir, captcha_text) 
            gtts_instance.save(file_name)

if __name__ == '__main__':
    main()







    