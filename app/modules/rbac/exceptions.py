# ==========================================================
# Base Exception
# ==========================================================

class RBACException(Exception):
    """Base exception for RBAC module."""
    pass


# ==========================================================
# Role Exceptions
# ==========================================================

class RoleNotFoundException(RBACException):
    def __init__(self):
        super().__init__("Role not found.")


class RoleAlreadyExistsException(RBACException):
    def __init__(self):
        super().__init__("Role already exists.")


class SystemRoleModificationException(RBACException):
    def __init__(self):
        super().__init__(
            "System roles cannot be modified."
        )


class SystemRoleDeletionException(RBACException):
    def __init__(self):
        super().__init__(
            "System roles cannot be deleted."
        )


# ==========================================================
# Permission Exceptions
# ==========================================================

class PermissionNotFoundException(RBACException):
    def __init__(self):
        super().__init__("Permission not found.")


class PermissionAlreadyExistsException(RBACException):
    def __init__(self):
        super().__init__(
            "Permission already exists."
        )


# ==========================================================
# Assignment Exceptions
# ==========================================================

class UserRoleAlreadyAssignedException(RBACException):
    def __init__(self):
        super().__init__(
            "The user already has this role assigned."
        )


class PermissionAlreadyAssignedException(RBACException):
    def __init__(self):
        super().__init__(
            "The role already has this permission assigned."
        )


class UserHasNoRoleException(RBACException):
    def __init__(self):
        super().__init__(
            "The user has no assigned roles."
        )


class UserHasNoPermissionException(RBACException):
    def __init__(self):
        super().__init__(
            "The user does not have the required permission."
        )