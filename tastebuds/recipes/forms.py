from django import forms
from .models import Rating


class RatingForm(forms.ModelForm):
    """Form for submitting ratings and reviews."""
    rating = forms.IntegerField(
        widget=forms.HiddenInput(attrs={
            'id': 'rating-value',
            'required': True
        }),
        label='Rating',
        help_text='Click on the stars to rate this recipe'
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Write your review here...'
        }),
        label='Review (Optional)',
        required=False
    )

    class Meta:
        model = Rating
        fields = ['rating', 'comment']

