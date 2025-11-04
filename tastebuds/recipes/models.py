from django.db import models
from django.contrib.auth.models import User


class Rating(models.Model):
    """Model to store user ratings and reviews for recipes."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    recipe_id = models.IntegerField(help_text="The idMeal from TheMealDB API")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], help_text="Rating from 1 to 5")
    comment = models.TextField(blank=True, help_text="Optional review/comment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'recipe_id']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - Recipe {self.recipe_id} - {self.rating} stars"
