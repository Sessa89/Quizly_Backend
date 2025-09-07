'''Admin configuration for the quiz_app.

Features:
- Inline management of questions inside the Quiz admin (TabularInline).
- Editor-friendly input for question options via a textarea (one option per line).
- Strong validation in the form:
  * exactly 4 options
  * all options must be unique
  * the correct answer must be one of the options
- Separate Question admin for direct editing/viewing when needed.

Notes:
- The Question model is expected to store options in a JSON-like list field
  (e.g., JSONField) named 'question_options'.
- The inline form mirrors the list into a textarea for comfortable editing,
  and writes it back on save.
'''

from django.contrib import admin
from django import forms
from .models import Quiz, Question

# Register your models here.

class QuestionInlineForm(forms.ModelForm):
    '''Inline form used within Quiz admin to handle options as newline-separated text.'''

    options_text = forms.CharField(
        label='Answer options',
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='Enter exactly 4 answer options – one per line.',
        required=True,
    )

    class Meta:
        model = Question
        fields = ('question_title', 'options_text', 'answer')

    def __init__(self, *args, **kwargs):
        '''Populate textarea with the current list of options on edit.'''

        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and self.instance.question_options:
            self.fields['options_text'].initial = '\n'.join(self.instance.question_options)

    def clean(self):
        '''Validate exactly 4 unique options and ensure answer is among them.'''

        cleaned = super().clean()
        raw = cleaned.get('options_text', '')
        opts = [o.strip() for o in raw.splitlines() if o.strip()]

        if len(opts) != 4:
            raise forms.ValidationError('Exactly 4 answer options must be provided.')
        if len(set(opts)) != 4:
            raise forms.ValidationError('All answer options must be unique.')

        ans = cleaned.get('answer')
        if ans and ans not in opts:
            raise forms.ValidationError('The correct answer must be among the options.')

        cleaned['question_options_list'] = opts
        return cleaned

    def save(self, commit=True):
        '''Write normalized options list back to the model field.'''

        self.instance.question_options = self.cleaned_data['question_options_list']
        return super().save(commit=commit)

class QuestionInline(admin.TabularInline):
    '''Inline questions table within a Quiz change page.'''

    model = Question
    form = QuestionInlineForm
    extra = 1
    show_change_link = True

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    '''Admin for Quiz, with inline Questions and helpful list configuration.'''

    list_display = ('id', 'title', 'owner', 'created_at')
    list_filter  = ('owner', 'created_at')
    search_fields = ('title', 'description', 'owner__username', 'video_url')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [QuestionInline]
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_select_related = ('owner',)

class QuestionAdminForm(QuestionInlineForm):
    '''Reuse the inline form in standalone Question admin.'''

    class Meta(QuestionInlineForm.Meta):
        fields = ('quiz', 'question_title', 'options_text', 'answer')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    '''Standalone admin for individual Question entries.'''
    
    form = QuestionAdminForm
    list_display = ('id', 'quiz', 'question_title', 'answer')
    search_fields = ('question_title', 'answer', 'quiz__title', 'quiz__owner__username')
    list_filter = ('quiz__owner',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('quiz', 'id')