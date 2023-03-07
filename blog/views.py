from django.shortcuts import render
from .models import Post
import pickle
import pandas as pd
from Crypto.Cipher import AES
from wordcloud import WordCloud, STOPWORDS
from bs4 import BeautifulSoup
import re
from scipy.sparse import csr_matrix

def home(request):
    context = {
        'posts' : Post.objects.all()
    }
    return render(request, 'blog/home.html', context)


def about(request):
    return render(request, 'blog/about.html', {'title':'About'})

#Cleaning tet by converting text to lowecase,removing emails,urls,html tags,spaces,punctuations,numbers and stop words
def cleaning_text(text):
    #Converting to lowercase
    text = text.lower()
    #Removing emails
    text = re.sub(r'([a-zA-Z0-9+.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z0-9_-]+)', '', text)
    #Removing URLs
    text = re.sub(r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/+#-]*[\w@?^=%&/+#-])?', '', text)
    #Removing HTML tags
    text = BeautifulSoup(text, 'lxml').get_text()
    #Removing punctuations and numbers
    text = re.sub('[^A-Z a-z ]+', ' ', text)
    #Removing Multiple spaces
    text =  " ".join(text.split())
    #Removing Stop words
    text =  " ".join([t for t in text.split() if t not in STOPWORDS])
    return text


def encrypt_message(message, key):
    message = message.encode()
    padding = 16 - (len(message) % 16)
    message += bytes([padding] * padding)
    key = key[:16].encode()
    cipher = AES.new(key, AES.MODE_ECB)
    ciphertext = cipher.encrypt(message)
    return ciphertext

def encrypt_ques(question):
    vectorizer = pickle.load(open(r'C:\Users\HP\Desktop\Django_BlogApp\blog\vectorizer1.pkl','rb'))
    mat = vectorizer.transform([question])
    vec_df = pd.DataFrame.sparse.from_spmatrix(mat)
    X_cols = list(vec_df.columns)
    key = "the key is somerandombullshit"
    for col in X_cols:
        vec_df[col] = [encrypt_message(str(x), key) for x in vec_df[col]]
        vec_df[col] = [int.from_bytes(x, byteorder='big') for x in vec_df[col]]
        vec_df[col] = pd.to_numeric(vec_df[col], errors='coerce').astype(float)
    return vec_df

def predict_quality(matrix):
    model = pickle.load(open(r'C:\Users\HP\Desktop\Django_BlogApp\blog\multinomialNB_SO1.pkl','rb'))
    return model.predict(matrix)[0]

def result(request):
    if request.method == "POST":
        d = request.POST
        for key,value in d.items():
            if key == "ques":
                question = value
                break
        my_value = question
        #context = {"my_value":my_value}
        question = cleaning_text(question)
        quality = predict_quality(encrypt_ques(question))
        print(quality)
        if quality == "HQ":
            quality = "High"
        elif quality == "LQ_EDIT":
            quality = "Medium"
        else:
            quality = "Low"

        return render(request, 'blog/home.html', {"output": quality})