'''Admin customization for Django's built-in User model (authentication_app).

Features:
- Inline display of SimpleJWT Outstanding Tokens per user (if the blacklist app
  is installed and migrated).
- Boolean column to indicate whether each token is blacklisted.
- Admin action to blacklist all outstanding tokens for selected users.
- Extra columns and filters to make user management convenient.

Prerequisites:
- 'rest_framework_simplejwt.token_blacklist' must be in INSTALLED_APPS
  and migrations applied, otherwise JWT-related UI is hidden automatically.
'''

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

# Register your models here.

try:
    from rest_framework_simplejwt.token_blacklist.models import (
        OutstandingToken, BlacklistedToken
    )
    JWT_BLACKLIST_AVAILABLE = True
except Exception:
    JWT_BLACKLIST_AVAILABLE = False


if JWT_BLACKLIST_AVAILABLE:
    class OutstandingTokenInline(admin.TabularInline):
        '''Inline table showing a user's outstanding JWTs.'''

        model = OutstandingToken
        extra = 0
        can_delete = False
        verbose_name = 'JWT'
        verbose_name_plural = 'JWTs'
        fields = ('jti', 'created_at', 'expires_at', 'is_blacklisted')
        readonly_fields = ('jti', 'created_at', 'expires_at', 'is_blacklisted')

        def is_blacklisted(self, obj):
            '''Return True if this outstanding token is blacklisted.'''

            return BlacklistedToken.objects.filter(token=obj).exists()
        
        is_blacklisted.short_description = 'blacklisted'
        is_blacklisted.boolean = True


@admin.action(description='Invalidate all JWTs for selected users (blacklist)')
def blacklist_all_tokens(modeladmin, request, queryset):
    '''Admin action: blacklist all outstanding tokens for the selected users.'''

    if not JWT_BLACKLIST_AVAILABLE:
        messages.error(request, 'Token blacklist module is not installed.')
        return
    
    qs = OutstandingToken.objects.filter(user__in=queryset)
    count = 0
    for tok in qs:
        _, created = BlacklistedToken.objects.get_or_create(token=tok)
        count += int(created)

    messages.success(request, f'{count} token(s) have been blacklisted.')

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    '''Enhanced admin for Django's built-in User with JWT helpers.'''

    list_display = (
        'username', 'email', 'is_staff', 'is_active', 'date_joined', 'last_login', 'tokens_count'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    actions = [blacklist_all_tokens]

    if JWT_BLACKLIST_AVAILABLE:
        inlines = [OutstandingTokenInline]

    def tokens_count(self, obj):
        '''Number of outstanding JWTs for this user (or '-' if feature unavailable).'''

        if not JWT_BLACKLIST_AVAILABLE:
            return '-'
        return OutstandingToken.objects.filter(user=obj).count()
    
    tokens_count.short_description = 'JWTs'