from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = {'text', 'group', 'image'}
        labels = {
            'text': 'Текст',
            'group': 'Группа'
        }
        help_texts = {
            'text': 'Введите текст для публикации',
            'group': 'не обязательное поле'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = {'text'}
