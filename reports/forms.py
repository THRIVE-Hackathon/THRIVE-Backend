from django import forms

from .models import TripResult


class TripResultForm(forms.ModelForm):
    disruption_score = forms.ChoiceField(
        label="착륙 다음 날, 계획했던 일을 얼마나 하셨나요?",
        choices=TripResult.DisruptionScore.choices,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = TripResult
        fields = ["disruption_score"]

    def save(self, commit=True):
        result = super().save(commit=False)
        score = int(self.cleaned_data["disruption_score"])
        result.disruption_score = score
        result.selected_answer = dict(TripResult.DisruptionScore.choices)[score]
        if commit:
            result.save()
        return result
