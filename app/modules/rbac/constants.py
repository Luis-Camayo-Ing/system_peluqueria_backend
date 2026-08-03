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
# Suppliers Permissions
# ==========================================================

SUPPLIERS_CREATE = "suppliers:create"
SUPPLIERS_READ = "suppliers:read"
SUPPLIERS_UPDATE = "suppliers:update"
SUPPLIERS_DELETE = "suppliers:delete"


# ==========================================================
# Purchases Permissions
# ==========================================================

PURCHASES_CREATE = "purchases:create"
PURCHASES_READ = "purchases:read"
PURCHASES_UPDATE = "purchases:update"
PURCHASES_APPROVE = "purchases:approve"
PURCHASES_CANCEL = "purchases:cancel"
PURCHASES_RECEIVE = "purchases:receive"


# ==========================================================
# Sales Permissions
# ==========================================================

SALES_CREATE = "sales:create"
SALES_READ = "sales:read"
SALES_CANCEL = "sales:cancel"
SALES_RECEIPT = "sales:receipt"
SALES_SEND = "sales:send"


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
# Cash Register Permissions
# ==========================================================

CASH_REGISTERS_CREATE = "cash_registers:create"
CASH_REGISTERS_READ = "cash_registers:read"
CASH_REGISTERS_UPDATE = "cash_registers:update"
CASH_REGISTERS_DELETE = "cash_registers:delete"

CASH_SESSIONS_OPEN = "cash_sessions:open"
CASH_SESSIONS_READ = "cash_sessions:read"
CASH_SESSIONS_CLOSE = "cash_sessions:close"

CASH_TRANSACTIONS_CREATE = "cash_transactions:create"
CASH_TRANSACTIONS_READ = "cash_transactions:read"


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

    SUPPLIERS_CREATE,
    SUPPLIERS_READ,
    SUPPLIERS_UPDATE,
    SUPPLIERS_DELETE,

    PURCHASES_CREATE,
    PURCHASES_READ,
    PURCHASES_UPDATE,
    PURCHASES_APPROVE,
    PURCHASES_CANCEL,
    PURCHASES_RECEIVE,

    SALES_CREATE,
    SALES_READ,
    SALES_CANCEL,
    SALES_RECEIPT,
    SALES_SEND,

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

    CASH_REGISTERS_CREATE,
    CASH_REGISTERS_READ,
    CASH_REGISTERS_UPDATE,
    CASH_REGISTERS_DELETE,

    CASH_SESSIONS_OPEN,
    CASH_SESSIONS_READ,
    CASH_SESSIONS_CLOSE,

    CASH_TRANSACTIONS_CREATE,
    CASH_TRANSACTIONS_READ,

    PAYMENTS_CREATE,
    PAYMENTS_READ,
    PAYMENTS_UPDATE,
    PAYMENTS_DELETE,

    REPORTS_VIEW,
    DASHBOARD_VIEW,

    AUDIT_READ,
]