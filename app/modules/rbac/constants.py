# ==========================================================
# System Roles
# ==========================================================

ADMINISTRATOR_ROLE = "Administrator"
MANAGER_ROLE = "Manager"
RECEPTIONIST_ROLE = "Receptionist"
STYLIST_ROLE = "Stylist"
BARBER_ROLE = "Barber"
MANICURIST_ROLE = "Manicurist"
CASHIER_ROLE = "Cashier"


SYSTEM_ROLES = [
    ADMINISTRATOR_ROLE,
    MANAGER_ROLE,
    RECEPTIONIST_ROLE,
    STYLIST_ROLE,
    BARBER_ROLE,
    MANICURIST_ROLE,
    CASHIER_ROLE,
]


# ==========================================================
# RBAC Permissions
# ==========================================================

ROLES_CREATE = "roles:create"
ROLES_READ = "roles:read"
ROLES_UPDATE = "roles:update"
ROLES_DELETE = "roles:delete"
ROLES_ASSIGN = "roles:assign"

PERMISSIONS_CREATE = "permissions:create"
PERMISSIONS_READ = "permissions:read"
PERMISSIONS_UPDATE = "permissions:update"
PERMISSIONS_DELETE = "permissions:delete"
PERMISSIONS_ASSIGN = "permissions:assign"


# ==========================================================
# Users Permissions
# ==========================================================

USERS_CREATE = "users:create"
USERS_READ = "users:read"
USERS_UPDATE = "users:update"
USERS_DELETE = "users:delete"


# ==========================================================
# Employees Permissions
# ==========================================================

EMPLOYEES_CREATE = "employees:create"
EMPLOYEES_READ = "employees:read"
EMPLOYEES_UPDATE = "employees:update"
EMPLOYEES_DELETE = "employees:delete"


# ==========================================================
# Customers Permissions
# ==========================================================

CUSTOMERS_CREATE = "customers:create"
CUSTOMERS_READ = "customers:read"
CUSTOMERS_UPDATE = "customers:update"
CUSTOMERS_DELETE = "customers:delete"


# ==========================================================
# Services Permissions
# ==========================================================

SERVICES_CREATE = "services:create"
SERVICES_READ = "services:read"
SERVICES_UPDATE = "services:update"
SERVICES_DELETE = "services:delete"


# ==========================================================
# Appointments Permissions
# ==========================================================

APPOINTMENTS_CREATE = "appointments:create"
APPOINTMENTS_READ = "appointments:read"
APPOINTMENTS_UPDATE = "appointments:update"
APPOINTMENTS_DELETE = "appointments:delete"


# ==========================================================
# Inventory Permissions
# ==========================================================

INVENTORY_CREATE = "inventory:create"
INVENTORY_READ = "inventory:read"
INVENTORY_UPDATE = "inventory:update"
INVENTORY_DELETE = "inventory:delete"


# ==========================================================
# Payments Permissions
# ==========================================================

PAYMENTS_CREATE = "payments:create"
PAYMENTS_READ = "payments:read"
PAYMENTS_UPDATE = "payments:update"
PAYMENTS_DELETE = "payments:delete"


# ==========================================================
# Reports and Dashboard
# ==========================================================

REPORTS_VIEW = "reports:view"
DASHBOARD_VIEW = "dashboard:view"


# ==========================================================
# Audit Permissions
# ==========================================================

AUDIT_READ = "audit:read"


# ==========================================================
# Complete Permission Catalog
# ==========================================================

SYSTEM_PERMISSIONS = [
    ROLES_CREATE,
    ROLES_READ,
    ROLES_UPDATE,
    ROLES_DELETE,
    ROLES_ASSIGN,

    PERMISSIONS_CREATE,
    PERMISSIONS_READ,
    PERMISSIONS_UPDATE,
    PERMISSIONS_DELETE,
    PERMISSIONS_ASSIGN,

    USERS_CREATE,
    USERS_READ,
    USERS_UPDATE,
    USERS_DELETE,

    EMPLOYEES_CREATE,
    EMPLOYEES_READ,
    EMPLOYEES_UPDATE,
    EMPLOYEES_DELETE,

    CUSTOMERS_CREATE,
    CUSTOMERS_READ,
    CUSTOMERS_UPDATE,
    CUSTOMERS_DELETE,

    SERVICES_CREATE,
    SERVICES_READ,
    SERVICES_UPDATE,
    SERVICES_DELETE,

    APPOINTMENTS_CREATE,
    APPOINTMENTS_READ,
    APPOINTMENTS_UPDATE,
    APPOINTMENTS_DELETE,

    INVENTORY_CREATE,
    INVENTORY_READ,
    INVENTORY_UPDATE,
    INVENTORY_DELETE,

    PAYMENTS_CREATE,
    PAYMENTS_READ,
    PAYMENTS_UPDATE,
    PAYMENTS_DELETE,

    REPORTS_VIEW,
    DASHBOARD_VIEW,

    AUDIT_READ,
]