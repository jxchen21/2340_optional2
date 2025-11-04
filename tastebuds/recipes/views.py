import requests
from django.core.paginator import Paginator
from django.shortcuts import render


def fetch_random_recipes(n=8):
    url = 'https://www.themealdb.com/api/json/v1/1/random.php'
    recipes = []
    for _ in range(n):
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            meal = data.get('meals', [None])[0]
            if meal:
                recipes.append(meal)
        except Exception:
            continue
    return recipes


def index(request):
    recipes = fetch_random_recipes(8)
    template_data = {
        'title': 'Recipes',
        'recipes': recipes,
    }
    return render(request, 'recipes/index.html', {'template_data': template_data})

def show(request, id):
    url = f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}'
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        recipe = data.get('meals', [None])[0]
    except Exception:
        recipe = None

    # Extract ingredients and measures
    ingredients = []
    if recipe:
        for i in range(1, 21):
            ingredient = recipe.get(f'strIngredient{i}')
            measure = recipe.get(f'strMeasure{i}')
            if ingredient and ingredient.strip():
                ingredients.append({
                    'ingredient': ingredient.strip(),
                    'measure': measure.strip() if measure else '',
                })

    template_data = {
        'title': recipe.get('strMeal', 'Recipe') if recipe else 'Recipe Not Found',
        'recipe': recipe,
        'ingredients': ingredients,
        'instructions': recipe.get('strInstructions', '') if recipe else '',
    }
    return render(request, 'recipes/show.html', {'template_data': template_data})