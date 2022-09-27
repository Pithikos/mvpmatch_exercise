from rest_framework_roles.roles import is_user, is_anon, is_admin


# Granting checks

def is_creator(request, view):
    obj = view.get_object()
    return obj.seller_id == request.user


# Role checks

def is_buyer(request, view):
    return request.user.is_authenticated and request.user.role == 'buyer'


def is_seller(request, view):
    return request.user.is_authenticated and request.user.role == 'seller'


ROLES = {
    'user': is_user,
    'admin': is_admin,
    'anon': is_anon,

    # user roles
    'buyer': is_buyer,
    'seller': is_seller,
}
