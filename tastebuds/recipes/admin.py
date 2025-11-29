from django.contrib import admin
from .models import Rating, SavedRecipe, WeeklyMealPlan, ShoppingItem


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe_id', 'rating', 'created_at', 'updated_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'recipe_id', 'comment']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SavedRecipe)
class SavedRecipeAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe_name', 'recipe_id', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('recipe_name', 'user__username')
    readonly_fields = ('created_at',)


@admin.register(WeeklyMealPlan)
class WeeklyMealPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'day', 'meal_slot', 'saved_recipe', 'created_at')
    list_filter = ('day', 'meal_slot', 'created_at')
    search_fields = ('saved_recipe__recipe_name', 'user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'user__username')
    readonly_fields = ('created_at',)
