import pandas as pd
from sklearn.cluster import KMeans
import joblib
from etl.load_excel import load_graduate_data

def train_kmeans(excel_path, out_model='models/kmeans_model.pkl'):
    df = load_graduate_data(excel_path)
    X = df[['Year', 'Semester', 'Credits']].values
    kmeans = KMeans(n_clusters=4, random_state=42)
    kmeans.fit(X)
    joblib.dump(kmeans, out_model)
    return out_model
