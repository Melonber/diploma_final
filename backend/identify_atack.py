from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report
from  data_for_atacks import data

def check_request(request):
    queries, labels = zip(*data)

    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(queries)

    X_train, X_test, y_train, y_test = train_test_split(X, labels, test_size=0.2, random_state=42)

    model = MultinomialNB()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)


    def classify_query(query):
        query_vector = vectorizer.transform([query])
        prediction = model.predict(query_vector)
        return prediction[0]

    new_query = request
    attack_type = classify_query(new_query)

    return attack_type


