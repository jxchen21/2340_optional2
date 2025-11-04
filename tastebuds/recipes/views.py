import requests
from django.shortcuts import render, redirect
from django.urls import reverse


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


def fetch_by_category(category):
    """Fetch meals filtered by category from TheMealDB."""
    url = f'https://www.themealdb.com/api/json/v1/1/filter.php?c={category}'
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get('meals') or []
    except Exception:
        return []


def search_by_name(term):
    """Search meals by name (allows more specific lookups like 'pizza')."""
    url = f'https://www.themealdb.com/api/json/v1/1/search.php?s={term}'
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get('meals') or []
    except Exception:
        return []


def fetch_by_region(region):
    """Fetch meals filtered by area/region from TheMealDB."""
    url = f'https://www.themealdb.com/api/json/v1/1/filter.php?a={region}'
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get('meals') or []
    except Exception:
        return []


def index(request):
    # If user submitted a search, require authentication for searching
    category = request.GET.get('category', '').strip()
    region = request.GET.get('region', '').strip()

    template_data = {
        'title': 'Recipes',
    }

    # Initialize form fields so only the one typed into keeps its value
    template_data['category_term'] = ''
    template_data['region_term'] = ''

    if category or region:
        # Require registered user for searching
        if not request.user.is_authenticated:
            # redirect to login page
            return redirect(reverse('accounts.login'))

        # If both provided, fetch both lists and intersect by idMeal
        if category and region:
            cat_results = fetch_by_category(category)
            reg_results = fetch_by_region(region)

            # Build maps by idMeal for fast lookup
            cat_map = {m.get('idMeal'): m for m in (cat_results or [])}
            reg_map = {m.get('idMeal'): m for m in (reg_results or [])}

            # Intersection of ids
            intersect_ids = set(cat_map.keys()) & set(reg_map.keys())
            results = [cat_map[i] for i in intersect_ids]

            template_data['search_type'] = 'Category & Region'
            template_data['search_term'] = f"{category} / {region}"
            template_data['category_term'] = category
            template_data['region_term'] = region
        else:
            # Prefer category if provided, otherwise region
            if category:
                # First try category filter (broad categories like 'Dessert')
                cat_results = fetch_by_category(category)
                # Also attempt name search (for specific items like 'pizza')
                name_results = search_by_name(category)

                # Prefer category results if they exist; otherwise fall back to name search
                if cat_results:
                    results = cat_results
                    template_data['search_type'] = 'Category'
                    template_data['search_term'] = category
                else:
                    results = name_results
                    template_data['search_type'] = 'Name Search'
                    template_data['search_term'] = category

                # Preserve both form fields appropriately
                template_data['category_term'] = category
                template_data['region_term'] = ''
            else:
                results = fetch_by_region(region)
                template_data['search_type'] = 'Region'
                template_data['search_term'] = region
                template_data['region_term'] = region
                template_data['category_term'] = ''

        template_data['search_results'] = results
        template_data['recipes'] = []
    else:
        # No search => show random picks
        template_data['recipes'] = fetch_random_recipes(8)

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