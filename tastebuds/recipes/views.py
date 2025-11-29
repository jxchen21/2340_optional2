import requests
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Rating, SavedRecipe, WeeklyMealPlan, ShoppingItem
from .forms import RatingForm


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

    # Get all ratings for this recipe
    ratings = Rating.objects.filter(recipe_id=id).select_related('user')

    # Calculate average rating
    avg_rating = ratings.aggregate(Avg('rating'))['rating__avg']
    avg_rating = round(avg_rating, 1) if avg_rating else None
    avg_rating_int = int(round(avg_rating)) if avg_rating else 0
    rating_count = ratings.count()

    # Check if current user has already rated
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(user=request.user, recipe_id=id)
        except Rating.DoesNotExist:
            user_rating = None

    # Handle rating submission
    form = None
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = RatingForm(request.POST)
            if form.is_valid():
                rating_obj, created = Rating.objects.update_or_create(
                    user=request.user,
                    recipe_id=id,
                    defaults={
                        'rating': form.cleaned_data['rating'],
                        'comment': form.cleaned_data['comment']
                    }
                )
                if created:
                    messages.success(request, 'Thank you for your rating!')
                else:
                    messages.success(request, 'Your rating has been updated!')
                return redirect('recipes.show', id=id)
        else:
            # Pre-populate form if user has already rated
            if user_rating:
                form = RatingForm(instance=user_rating)
            else:
                form = RatingForm()

    # Check if recipe is saved by user
    is_saved = False
    saved_recipe = None
    if request.user.is_authenticated and recipe:
        recipe_id_str = recipe.get('idMeal', str(id))
        try:
            saved_recipe = SavedRecipe.objects.get(user=request.user, recipe_id=recipe_id_str)
            is_saved = True
        except SavedRecipe.DoesNotExist:
            pass

    template_data = {
        'title': recipe.get('strMeal', 'Recipe') if recipe else 'Recipe Not Found',
        'recipe': recipe,
        'ingredients': ingredients,
        'instructions': recipe.get('strInstructions', '') if recipe else '',
        'ratings': ratings,
        'avg_rating': avg_rating,
        'avg_rating_int': avg_rating_int,
        'rating_count': rating_count,
        'user_rating': user_rating,
        'form': form,
        'is_saved': is_saved,
        'saved_recipe': saved_recipe,
    }
    return render(request, 'recipes/show.html', {'template_data': template_data})


@login_required
@require_POST
def save_recipe(request, id):
    """Save or unsave a recipe."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    # Fetch recipe details from API
    url = f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}'
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        recipe = data.get('meals', [None])[0]
    except Exception:
        return JsonResponse({'error': 'Recipe not found'}, status=404)

    if not recipe:
        return JsonResponse({'error': 'Recipe not found'}, status=404)

    # Use the recipe ID from the API (as string) to match SavedRecipe's CharField
    recipe_id_str = recipe.get('idMeal', str(id))

    # Check if already saved
    saved_recipe, created = SavedRecipe.objects.get_or_create(
        user=request.user,
        recipe_id=recipe_id_str,
        defaults={
            'recipe_name': recipe.get('strMeal', ''),
            'recipe_image': recipe.get('strMealThumb', ''),
        }
    )

    if created:
        return JsonResponse({'status': 'saved', 'message': 'Recipe saved successfully'})
    else:
        saved_recipe.delete()
        return JsonResponse({'status': 'unsaved', 'message': 'Recipe removed from saved'})


@login_required
def planner(request):
    """Weekly meal planner with kanban interface."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    meal_slots = ['Breakfast', 'Lunch', 'Dinner', 'Snack']

    # Get saved recipes for the user
    saved_recipes = SavedRecipe.objects.filter(user=request.user)

    # Get meal plans grouped by day and meal slot
    meal_plans = WeeklyMealPlan.objects.filter(user=request.user).select_related('saved_recipe')

    # Organize meal plans by day and meal slot
    planner_data = {}
    for day in days:
        planner_data[day] = {}
        for meal_slot in meal_slots:
            planner_data[day][meal_slot] = [
                plan for plan in meal_plans
                if plan.day == day and plan.meal_slot == meal_slot
            ]

    template_data = {
        'title': 'Weekly Meal Planner',
        'days': days,
        'meal_slots': meal_slots,
        'saved_recipes': saved_recipes,
        'planner_data': planner_data,
    }
    return render(request, 'recipes/planner.html', {'template_data': template_data})


@login_required
@require_POST
def add_to_planner(request):
    """Add a saved recipe to a specific day and meal slot."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    saved_recipe_id = request.POST.get('saved_recipe_id')
    day = request.POST.get('day')
    meal_slot = request.POST.get('meal_slot')

    if not all([saved_recipe_id, day, meal_slot]):
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    # Validate day and meal_slot
    valid_days = [d[0] for d in WeeklyMealPlan.DAYS_OF_WEEK]
    valid_meal_slots = [m[0] for m in WeeklyMealPlan.MEAL_SLOTS]

    if day not in valid_days or meal_slot not in valid_meal_slots:
        return JsonResponse({'error': 'Invalid day or meal slot'}, status=400)

    # Get saved recipe
    try:
        saved_recipe = SavedRecipe.objects.get(id=saved_recipe_id, user=request.user)
    except SavedRecipe.DoesNotExist:
        return JsonResponse({'error': 'Saved recipe not found'}, status=404)

    # Create meal plan entry
    meal_plan = WeeklyMealPlan.objects.create(
        user=request.user,
        saved_recipe=saved_recipe,
        day=day,
        meal_slot=meal_slot
    )

    return JsonResponse({
        'status': 'success',
        'message': 'Recipe added to planner',
        'meal_plan_id': meal_plan.id,
        'recipe_name': saved_recipe.recipe_name,
        'recipe_image': saved_recipe.recipe_image,
    })


@login_required
@require_POST
def remove_from_planner(request, meal_plan_id):
    """Remove a recipe from the planner."""
    try:
        meal_plan = WeeklyMealPlan.objects.get(id=meal_plan_id, user=request.user)
        meal_plan.delete()
        return JsonResponse({'status': 'success', 'message': 'Recipe removed from planner'})
    except WeeklyMealPlan.DoesNotExist:
        return JsonResponse({'error': 'Meal plan not found'}, status=404)


@login_required
def shopping_list(request):
    """Shopping list page that aggregates ingredients from saved recipes."""
    # Get all saved recipes for the user
    saved_recipes = SavedRecipe.objects.filter(user=request.user)

    # Aggregate unique ingredients from all saved recipes
    all_ingredients = set()
    ingredients_by_recipe = {}

    for saved_recipe in saved_recipes:
        # Fetch recipe details from API
        url = f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={saved_recipe.recipe_id}'
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            recipe = data.get('meals', [None])[0]

            if recipe:
                recipe_ingredients = []
                for i in range(1, 21):
                    ingredient = recipe.get(f'strIngredient{i}')
                    if ingredient and ingredient.strip():
                        ingredient_name = ingredient.strip()
                        all_ingredients.add(ingredient_name)
                        recipe_ingredients.append(ingredient_name)

                if recipe_ingredients:
                    ingredients_by_recipe[saved_recipe.recipe_name] = recipe_ingredients
        except Exception:
            continue

    # Get existing shopping items
    shopping_items = ShoppingItem.objects.filter(user=request.user)
    existing_item_names = {item.name for item in shopping_items}
    # Create a mapping of item names to IDs for easy lookup
    item_name_to_id = {item.name: item.id for item in shopping_items}

    # Separate ingredients into: from recipes (not in shopping list) and already in shopping list
    recipe_ingredients_not_in_list = sorted(all_ingredients - existing_item_names)
    recipe_ingredients_in_list = sorted([(name, item_name_to_id[name]) for name in (all_ingredients & existing_item_names)], key=lambda x: x[0])

    # Get custom shopping items (not from recipes) with IDs
    custom_items = sorted([(item.name, item.id) for item in shopping_items if item.name not in all_ingredients], key=lambda x: x[0])

    template_data = {
        'title': 'Shopping List',
        'recipe_ingredients_not_in_list': recipe_ingredients_not_in_list,
        'recipe_ingredients_in_list': recipe_ingredients_in_list,
        'custom_items': custom_items,
        'all_shopping_items': shopping_items,
        'ingredients_by_recipe': ingredients_by_recipe,
    }
    return render(request, 'recipes/shopping_list.html', {'template_data': template_data})


@login_required
@require_POST
def add_shopping_item(request):
    """Add an item to the shopping list."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    item_name = request.POST.get('name', '').strip()

    if not item_name:
        return JsonResponse({'error': 'Item name is required'}, status=400)

    # Create shopping item (unique_together constraint will prevent duplicates)
    shopping_item, created = ShoppingItem.objects.get_or_create(
        user=request.user,
        name=item_name,
    )

    if created:
        return JsonResponse({
            'status': 'success',
            'message': 'Item added to shopping list',
            'item_id': shopping_item.id,
            'item_name': shopping_item.name,
        })
    else:
        return JsonResponse({
            'status': 'exists',
            'message': 'Item already in shopping list',
            'item_id': shopping_item.id,
            'item_name': shopping_item.name,
        })


@login_required
@require_POST
def remove_shopping_item(request, item_id):
    """Remove an item from the shopping list."""
    try:
        shopping_item = ShoppingItem.objects.get(id=item_id, user=request.user)
        item_name = shopping_item.name
        shopping_item.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Item removed from shopping list',
            'item_name': item_name,
        })
    except ShoppingItem.DoesNotExist:
        return JsonResponse({'error': 'Shopping item not found'}, status=404)