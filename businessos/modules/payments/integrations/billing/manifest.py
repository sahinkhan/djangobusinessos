VIEW_ALLOCATIONS = "payments_billing.allocation.view"
CREATE_ALLOCATIONS = "payments_billing.allocation.create"

MODULE = {
    "code": "payments_billing",
    "name": "Payment allocations",
    "version": "0.1.0",
    "depends": ["billing", "payments"],
    "permissions": [VIEW_ALLOCATIONS, CREATE_ALLOCATIONS],
}
