from django.contrib import admin
from django import forms
from .models import Quiz, Question

# Register your models here.

class QuestionInlineForm(forms.ModelForm):
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
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and self.instance.question_options:
            self.fields['options_text'].initial = '\n'.join(self.instance.question_options)

    def clean(self):
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
        self.instance.question_options = self.cleaned_data['question_options_list']
        return super().save(commit=commit)


class QuestionInline(admin.TabularInline):
    model = Question
    form = QuestionInlineForm
    extra = 1
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'created_at')
    list_filter  = ('owner', 'created_at')
    search_fields = ('title', 'description', 'owner__username', 'video_url')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [QuestionInline]
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_select_related = ('owner',)


class QuestionAdminForm(QuestionInlineForm):
    class Meta(QuestionInlineForm.Meta):
        fields = ('quiz', 'question_title', 'options_text', 'answer')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm
    list_display = ('id', 'quiz', 'question_title', 'answer')
    search_fields = ('question_title', 'answer', 'quiz__title', 'quiz__owner__username')
    list_filter = ('quiz__owner',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('quiz', 'id')