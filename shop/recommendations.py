from sklearn.neighbors import NearestNeighbors
import numpy as np
from .models import ProductRating, Product

def get_interaction_matrix():
    ratings = ProductRating.objects.all()
    user_ids = list(set([rating.user_id for rating in ratings]))
    product_ids = list(set([rating.product_id for rating in ratings]))

    # Initialize an empty user-product interaction matrix
    interaction_matrix = np.zeros((len(user_ids), len(product_ids)))

    # Fill the matrix with ratings
    for rating in ratings:
        user_idx = user_ids.index(rating.user_id)
        product_idx = product_ids.index(rating.product_id)
        interaction_matrix[user_idx][product_idx] = rating.rating

    return interaction_matrix, user_ids, product_ids

def train_recommendation_model():
    interaction_matrix, user_ids, product_ids = get_interaction_matrix()
    
    # Train a K-Nearest Neighbors model
    model = NearestNeighbors(metric='cosine', algorithm='brute')
    model.fit(interaction_matrix)

    return model, user_ids, product_ids

def recommend_products(user_id):
    model, user_ids, product_ids = train_recommendation_model()
    interaction_matrix, _, _ = get_interaction_matrix()
    user_idx = user_ids.index(user_id)

    distances, indices = model.kneighbors([interaction_matrix[user_idx]], n_neighbors=5)
    recommended_product_ids = [product_ids[i] for i in indices.flatten()]

    return Product.objects.filter(id__in=recommended_product_ids)
from django.shortcuts import render
from .models import Product

def recommended_products_view(request):
    # Assuming this function returns a feature array
    product_features = fetch_product_features()
    
    if product_features.size == 0:
        # Handle the case where there are no products
        recommendations = []  # or some default behavior
    else:
        # Your recommendation logic here
        recommendations = []  # Replace with actual recommendation logic

    return render(request, 'shop/recommended_products.html', {'recommendations': recommendations})
