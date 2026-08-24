from django import forms

from .models import Lead


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ('name', 'phone', 'debt', 'message')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Как к вам обращаться'}),
            'phone': forms.TextInput(attrs={'placeholder': '+7 (___) ___-__-__'}),
            'debt': forms.TextInput(attrs={'placeholder': 'Например, 4 500 000 ₸'}),
            'message': forms.Textarea(attrs={'placeholder': 'Коротко опишите ситуацию', 'rows': 4}),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError('Укажите корректный номер телефона')
        return phone
