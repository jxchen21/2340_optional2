from django.db import models
from django.contrib.auth.models import User


class SavedRecipe(models.Model):
    """Model to store recipes saved by users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_recipes')
    recipe_id = models.CharField(max_length=100)  # TheMealDB recipe ID
    recipe_name = models.CharField(max_length=200)
    recipe_image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'recipe_id']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.recipe_name}"


class WeeklyMealPlan(models.Model):
    """Model to store recipes assigned to specific day and meal slots."""
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    
    MEAL_SLOTS = [
        ('Breakfast', 'Breakfast'),
        ('Lunch', 'Lunch'),
        ('Dinner', 'Dinner'),
        ('Snack', 'Snack'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans')
    saved_recipe = models.ForeignKey(SavedRecipe, on_delete=models.CASCADE, related_name='meal_plans')
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    meal_slot = models.CharField(max_length=10, choices=MEAL_SLOTS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['day', 'meal_slot', 'created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.day} {self.meal_slot}: {self.saved_recipe.recipe_name}"
