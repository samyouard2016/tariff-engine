from django import forms

class SearchForm(forms.Form):
        zipcode = forms.IntegerField(label='Zip Code')
        sector  = forms.CharField(label='Sector', max_length=20)
        utility = forms.CharField(label='Utility', max_length=100)