<<<<<<< HEAD
import  requests
HUGGINGFACE_API_KEY = "hf_aMYfxMdewmcJCESRNcymXisbgUYEgKS"

MODEL = "bigscience/bloom"

def analyze_sentiment(news_text):
    url = f"https://api-inference.huggingface.co/models/{MODEL}"  # API URL
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}  # API Key
    payload = {"inputs": f"Analyze the sentiment of this financial news: {news_text}"}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        text_output = result[0]["generated_text"]
        if "positive" in text_output.lower():
            return {"label": "POSITIVE", "score": 0.98}
        elif "negative" in text_output.lower():
            return {"label": "NEGATIVE", "score": 0.92}
        else:
            return {"label": "NEUTRAL", "score": 0.80}
    
    else:
        return {"error": response.text}



# ✅ Example Usage
if __name__ == "__main__":
    test_news = "Bitcoin price surges 15% after Tesla's announcement!"
    sentiment_result = analyze_sentiment(test_news)

    print("🔹 AI Market Sentiment Analysis 🔹")
    print(f"News: {test_news}")
    print(f"Sentiment: {sentiment_result}")
=======
import  requests
HUGGINGFACE_API_KEY = "hf_ypuJEkcwUdEllrdbbFHXPnxZSA*****"

MODEL = "bigscience/bloom"

def analyze_sentiment(news_text):
    url = f"https://api-inference.huggingface.co/models/{MODEL}"  # API URL
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}  # API Key
    payload = {"inputs": f"Analyze the sentiment of this financial news: {news_text}"}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        text_output = result[0]["generated_text"]
        if "positive" in text_output.lower():
            return {"label": "POSITIVE", "score": 0.98}
        elif "negative" in text_output.lower():
            return {"label": "NEGATIVE", "score": 0.92}
        else:
            return {"label": "NEUTRAL", "score": 0.80}
    
    else:
        return {"error": response.text}



# ✅ Example Usage
if __name__ == "__main__":
    test_news = "Bitcoin price surges 15% after Tesla's announcement!"
    sentiment_result = analyze_sentiment(test_news)

    print("🔹 AI Market Sentiment Analysis 🔹")
    print(f"News: {test_news}")
    print(f"Sentiment: {sentiment_result}")
>>>>>>> 24c39eb5ecfe7d76712abd16ead611cf63a7e569
