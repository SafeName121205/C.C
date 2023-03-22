from datetime import datetime

import listener
import speech_recognition as sr
import pyttsx3
import webbrowser


# OpenAI GPT-3
import openai

# Load credentials
import os
from dotenv import load_dotenv
load_dotenv()

# Google TTS
import google.cloud.texttospeech as tts
import pygame
import time

# Mute ALSA errors...
from ctypes import *
from contextlib import contextmanager

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def noalsaerr():
    try: 
        asound = cdll.LoadLibrary('libasound.so')
        asound.snd_lib_error_set_handler(c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except:
        yield
        print('')

### PARAMETERS ###
activationWords = ['Mindbot', 'Hello']
tts_type = 'local' # google or local

# Local speech engine initialisation
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id) # 0 = male, 1 = female

# Google TTS client
def google_text_to_wav(voice_name: str, text: str):
    language_code = "-".join(voice_name.split("-")[:2])

    # Set the text input to be synthesized
    text_input = tts.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the voice name
    voice_params = tts.VoiceSelectionParams(
        language_code=language_code, name=voice_name
    )

    # Select the type of audio file you want returned
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

    client = tts.TextToSpeechClient()
    response = client.synthesize_speech(
        input=text_input, voice=voice_params, audio_config=audio_config
    )

    return response.audio_content


def speak(text, rate = 130):
    time.sleep(0.3)

    if tts_type == 'local':
        engine.setProperty('rate', rate) 
        engine.say(text)
        engine.runAndWait()
    if tts_type == 'google':
        speech = google_text_to_wav('en-US-News-K', text)
        pygame.mixer.init(frequency=12000, buffer = 512)
        speech_sound = pygame.mixer.Sound(speech)
        speech_sound.play()
        time.sleep(len(text.split()))
        pygame.mixer.quit()

def parseCommand():
    with noalsaerr():
        listener = sr.Recognizer()
        print('Listening...')

        with sr.Microphone() as source:
            listener.pause_threshold = 2
            input_speech = listener.listen(source)


        try:
            print('Recognizing speech...')
            new_question = listener.recognize_google(input_speech, language='en_gb')

            print(f'The input speech was: {new_question}')

        except Exception as exception:
            print('I did not quite catch that')
            print(exception)

            return 'None'

        return new_question





# load values from the .env file if it exists
load_dotenv()

# configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

INSTRUCTIONS = """
You are a Cognitive behavioral therapist, that gives provides short answers that can be read from 5- 15 seconds to people's answers to engage in conversation with them. 

Please aim to be helpful, creative, and friendly in all your responses.

The conversation only ends when the user says, "I'm satisfied". 

At the end of the conversation you will give a short diagnosis on if they have a mental illness or not.

After the diagnosis you will say, "Please vote for Group BASA".

If you dont know the answer to a question, please reply with, "I'm afraid you'll have to refer to my cousin chatgbt for that".
"""

TEMPERATURE = 0.7
MAX_TOKENS = 256
FREQUENCY_PENALTY = 0
PRESENCE_PENALTY = 0.6
# limits how many questions we include in the prompt
MAX_CONTEXT_QUESTIONS = 12


def get_response(instructions, previous_questions_and_answers, new_question):
    """Get a response from ChatCompletion

    Args:
        instructions: The instructions for the chat bot - this determines how it will behave
        previous_questions_and_answers: Chat history
        new_question: The new question to ask the bot

    Returns:
        The response text
    """
    # build the messages
    messages = [
        { "role": "system", "content": instructions },
    ]
    # add the previous questions and answers
    for question, answer in previous_questions_and_answers[-MAX_CONTEXT_QUESTIONS:]:
        messages.append({ "role": "user", "content": question })
        messages.append({ "role": "assistant", "content": answer })

    # add the new question
    messages.append({ "role": "user", "content": new_question })

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        top_p=1,
        frequency_penalty=FREQUENCY_PENALTY,
        presence_penalty=PRESENCE_PENALTY,
    )
    return completion.choices[0].message.content

# Main loop
def main():

    speak('Hello, I am a compassionate companion, also known as CC, How was your day today?', 120)

    os.system("cls" if os.name == "nt" else "clear")
    # keep track of previous questions and answers
    previous_questions_and_answers = []

    while True:

        with noalsaerr():
            listener = sr.Recognizer()
            print('Listening...')

            with sr.Microphone() as source:
                listener.pause_threshold = 2
                input_speech = listener.listen(source)

            try:
                print('Recognizing speech...')
                new_question = listener.recognize_google(input_speech, language='en_gb')

                print(f'The input speech was: {new_question}')

            except Exception as exception:
                print('I did not quite catch that')
                print(exception)

                return 'None'
            # ask the user for their question

            response = get_response(INSTRUCTIONS, previous_questions_and_answers, new_question)

            # add the new question and answer to the list of previous questions and answers
            previous_questions_and_answers.append((new_question, response))

            # print the response
            speak(response)

        query = new_question

        # Set commands
        if new_question == "I'm satisfied":
            break

            if new_question == "I am satisfied":
                break


if __name__ == "__main__":

    main()
    # Parse as a list
    # query = 'computer say hello'.split()







