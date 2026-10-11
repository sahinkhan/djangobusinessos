VIEW_ACCOUNTS = "accounting.account.view"
MANAGE_ACCOUNTS = "accounting.account.manage"
VIEW_JOURNALS = "accounting.journal.view"
MANAGE_JOURNALS = "accounting.journal.manage"
VIEW_ENTRIES = "accounting.entry.view"
CREATE_ENTRIES = "accounting.entry.create"
UPDATE_ENTRIES = "accounting.entry.update"
POST_ENTRIES = "accounting.entry.post"

PERMISSIONS = (
    (VIEW_ACCOUNTS, "View accounts"),
    (MANAGE_ACCOUNTS, "Manage accounts"),
    (VIEW_JOURNALS, "View journals"),
    (MANAGE_JOURNALS, "Manage journals"),
    (VIEW_ENTRIES, "View journal entries and reports"),
    (CREATE_ENTRIES, "Create journal entries"),
    (UPDATE_ENTRIES, "Update draft journal entries"),
    (POST_ENTRIES, "Post journal entries"),
)

MODULE = {
    "code": "accounting",
    "name": "Accounting & Finance",
    "version": "0.1.0",
    "depends": ["party", "organization", "reference", "access"],
    "permissions": [code for code, _ in PERMISSIONS],
}
