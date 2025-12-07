from django import forms

class MongoConnectionForm(forms.Form):
    mongo_uri = forms.CharField(
        label="MongoDB Connection URI",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition duration-200',
            'placeholder': 'mongodb+srv://user:password@cluster.mongodb.net/db_name',
            'autocomplete': 'off'
        }),
        help_text="Enter your standard MongoDB connection string."
    )
