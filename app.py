import nltk
import json
import streamlit as st
import speech_recognition as sr
import time
import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download NLTK data if not already downloaded
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab')
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('wordnet', quiet=True)

# Load JSON file
def load_file(file_path="intents.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data['intents']

intents = load_file()

# Define stopwords and initialize lemmatizer
custom_stopwords = set(stopwords.words('english')).union(
    {"i'm", "how", "what", "about", "yourself", "thanks", "asking", "been", 
     "going", "do", "you", "very", "much", "with", "good", "well", "there"}
)
lemmatizer = WordNetLemmatizer()

# Preprocess text
def preprocess(text):
    words = word_tokenize(text)
    words = [
        lemmatizer.lemmatize(word.lower()) for word in words 
        if word.lower() not in custom_stopwords and word not in string.punctuation
    ]
    return words

# Prepare patterns and responses for each intent
corpus = [(preprocess(pattern), intent['responses']) for intent in intents for pattern in intent['patterns']]

# Function to get the most relevant response
def get_most_relevant_response(query):
    query_words = set(preprocess(query))
    max_similarity = 0
    best_response = "I'm not sure how to respond to that. Please try asking in another way."

    for pattern_words, responses in corpus:
        union_len = len(query_words.union(pattern_words))
        if union_len > 0:
            similarity = len(query_words.intersection(pattern_words)) / float(union_len)
            if similarity > max_similarity:
                max_similarity = similarity
                best_response = responses[0]  # Select the first response for simplicity

    return best_response

# Initialize recognizer class
r = sr.Recognizer()

# Function to transcribe speech
def transcribe_speech(api_choice):
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=5)
        st.info("Speak now...")
        
        audio_text = r.listen(source)

        st.info("Transcribing now...")        
        with st.spinner("Transcribing..."):
            time.sleep(10)  

            try:
                if api_choice == "Google":
                    text = r.recognize_google(audio_text).lower()
                else:
                    st.error("Selected API is not supported. Choose the available ones.")
                    return None

                st.success("Transcription complete!")
                st.write("Did you say: ", text)
                return text
            except sr.RequestError as e:
                st.error(f"API request failed; {e}")
                return None
            except sr.UnknownValueError:
                st.error("Sorry, I could not understand the audio.")
                return None

# Streamlit app
def main():
    st.title("First Aid Assistant Chatbot")
    st.write("I'm here to help with basic first aid advice.")

    # Initialize session state for question
    if 'question' not in st.session_state:
        st.session_state['question'] = ""

    # Select speech recognition API
    api_choice = st.selectbox("Selected API", ("Google",))
    
    # User question input
    text_question = st.text_input("You:", placeholder="Type your question here...")
    
    # Button to start recording
    if st.button("Start Recording"):
        text = transcribe_speech(api_choice)
        if text:
            st.session_state['question'] = text  # Store the transcribed text in session state

    # Set question from session state
    question = st.session_state['question'] if not text_question else text_question

    # Response button
    if st.button("Submit"):
        if question.strip():
            response = get_most_relevant_response(question)
            st.write("First Aid Assistant:", response)
            # Clear the session state question after responding
            st.session_state['question'] = ""
        else:
            st.write("Please enter a question before submitting.")

if __name__ == "__main__":
    main()