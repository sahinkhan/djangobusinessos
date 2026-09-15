VIEW_MOVEMENTS = "inventory.movement.view"
CREATE_MOVEMENTS = "inventory.movement.create"
UPDATE_MOVEMENTS = "inventory.movement.update"
POST_MOVEMENTS = "inventory.movement.post"
VIEW_BALANCES = "inventory.balance.view"

INVENTORY_PERMISSION_DECLARATIONS = (
    (VIEW_MOVEMENTS, "View stock movements"),
    (CREATE_MOVEMENTS, "Create draft stock movements"),
    (UPDATE_MOVEMENTS, "Update draft stock movements and movement lines"),
    (POST_MOVEMENTS, "Post stock movements"),
    (VIEW_BALANCES, "View derived stock balances and stock history"),
)

MODULE = {
    "code": "inventory",
    "name": "Inventory",
    "version": "0.1.0",
    "depends": ["catalog", "organization", "reference", "access"],
    "permissions": [code for code, _name in INVENTORY_PERMISSION_DECLARATIONS],
}

