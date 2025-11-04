from django.contrib import admin
from .models import SavedRecipe, WeeklyMealPlan

# Register your models here.
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
