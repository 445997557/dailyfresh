from django.contrib.auth.decorators import login_required
from django.views.generic import View


# class LoginRequiredView(View):
#     @classmethod
#     def as_view(cls, **initkwargs):
#         view_fun = super().as_view(**initkwargs)
#         return login_required(view_fun)


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view_fun = super().as_view(**initkwargs)
        return login_required(view_fun)
