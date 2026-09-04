from django import forms

from .models import Lead


CALC_FIELDS = ('calc_debt', 'calc_payments', 'calc_income', 'calc_result')


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ('name', 'phone', 'debt', 'message') + CALC_FIELDS
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Как к вам обращаться'}),
            'phone': forms.TextInput(attrs={'type': 'tel', 'inputmode': 'tel', 'autocomplete': 'tel', 'placeholder': '+7 (700) 000-00-00'}),
            'debt': forms.TextInput(attrs={'placeholder': 'Например, 4 500 000 ₸'}),
            'message': forms.Textarea(attrs={'placeholder': 'Коротко опишите ситуацию', 'rows': 4}),
            **{name: forms.HiddenInput() for name in CALC_FIELDS},
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError('Укажите корректный номер телефона')
        return phone
