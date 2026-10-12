"""Fixed ACC-INT-1 proof schema, never derived from the source being admitted.

Canonical 4419bdc4 PostgreSQL 17 and fresh SQLite migrations captured the
BASELINE. New binding definitions correspond to the candidate initial
migrations. Review future changes as explicit compatibility changes.
"""

BASELINE = {
    "django_migrations": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "bigint",
                True,
            ],
            [
                "app",
                "character varying(255)",
                True,
            ],
            [
                "name",
                "character varying(255)",
                True,
            ],
            [
                "applied",
                "timestamp with time zone",
                True,
            ],
        ],
        "constraints": [
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
        ],
    },
    "identity_user": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "password",
                "character varying(128)",
                True,
            ],
            [
                "last_login",
                "timestamp with time zone",
                False,
            ],
            [
                "is_superuser",
                "boolean",
                True,
            ],
            [
                "id",
                "uuid",
                True,
            ],
            [
                "email",
                "character varying(254)",
                True,
            ],
            [
                "is_active",
                "boolean",
                True,
            ],
            [
                "is_staff",
                "boolean",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
        ],
        "constraints": [
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (email)",
                True,
            ],
        ],
    },
    "organization_branch": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "is_active",
                "boolean",
                True,
            ],
            [
                "code",
                "character varying(32)",
                True,
            ],
            [
                "name",
                "character varying(160)",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (company_id, code)",
                True,
            ],
        ],
    },
    "organization_company": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "is_active",
                "boolean",
                True,
            ],
            [
                "code",
                "character varying(32)",
                True,
            ],
            [
                "name",
                "character varying(160)",
                True,
            ],
            [
                "timezone",
                "character varying(64)",
                True,
            ],
            [
                "base_currency_id",
                "uuid",
                True,
            ],
            [
                "country_id",
                "uuid",
                True,
            ],
            [
                "default_language_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (base_currency_id) REFERENCES reference_currency(id)"
                    " DEFERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (country_id) REFERENCES reference_country(id) DEFERR"
                    "ABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (default_language_id) REFERENCES reference_language("
                    "id) DEFERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (code)",
                True,
            ],
        ],
    },
    "organization_warehouse": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "is_active",
                "boolean",
                True,
            ],
            [
                "code",
                "character varying(32)",
                True,
            ],
            [
                "name",
                "character varying(160)",
                True,
            ],
            [
                "branch_id",
                "uuid",
                False,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (branch_id) REFERENCES organization_branch(id) DEFER"
                    "RABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (company_id, code)",
                True,
            ],
        ],
    },
    "access_permission": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "code",
                "character varying(100)",
                True,
            ],
            [
                "name",
                "character varying(160)",
                True,
            ],
            [
                "is_active",
                "boolean",
                True,
            ],
        ],
        "constraints": [
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (code)",
                True,
            ],
        ],
    },
    "access_role": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "code",
                "character varying(64)",
                True,
            ],
            [
                "name",
                "character varying(160)",
                True,
            ],
            [
                "is_active",
                "boolean",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (company_id, code)",
                True,
            ],
        ],
    },
    "access_userbranchaccess": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "branch_id",
                "uuid",
                True,
            ],
            [
                "user_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (branch_id) REFERENCES organization_branch(id) DEFER"
                    "RABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (user_id) REFERENCES identity_user(id) DEFERRABLE IN"
                    "ITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (user_id, branch_id)",
                True,
            ],
        ],
    },
    "access_usercompanyaccess": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
            [
                "user_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (user_id) REFERENCES identity_user(id) DEFERRABLE IN"
                    "ITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (user_id, company_id)",
                True,
            ],
        ],
    },
    "access_userwarehouseaccess": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "user_id",
                "uuid",
                True,
            ],
            [
                "warehouse_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (user_id) REFERENCES identity_user(id) DEFERRABLE IN"
                    "ITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (warehouse_id) REFERENCES organization_warehouse(id)"
                    " DEFERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (user_id, warehouse_id)",
                True,
            ],
        ],
    },
    "access_rolepermission": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "permission_id",
                "uuid",
                True,
            ],
            [
                "role_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (permission_id) REFERENCES access_permission(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                ("FOREIGN KEY (role_id) REFERENCES access_role(id) DEFERRABLE INITIALLY DEFERRED"),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (role_id, permission_id)",
                True,
            ],
        ],
    },
    "access_userroleassignment": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
            [
                "role_id",
                "uuid",
                True,
            ],
            [
                "user_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                ("FOREIGN KEY (role_id) REFERENCES access_role(id) DEFERRABLE INITIALLY DEFERRED"),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (user_id) REFERENCES identity_user(id) DEFERRABLE IN"
                    "ITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (user_id, company_id, role_id)",
                True,
            ],
        ],
    },
    "billing_invoice": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "number",
                "character varying(40)",
                True,
            ],
            [
                "bill_to_display_name_snapshot",
                "character varying(200)",
                True,
            ],
            [
                "bill_to_legal_name_snapshot",
                "character varying(200)",
                True,
            ],
            [
                "invoice_date",
                "date",
                True,
            ],
            [
                "due_date",
                "date",
                False,
            ],
            [
                "currency_code_snapshot",
                "character varying(3)",
                True,
            ],
            [
                "currency_decimal_places_snapshot",
                "smallint",
                True,
            ],
            [
                "status",
                "character varying(8)",
                True,
            ],
            [
                "notes",
                "text",
                True,
            ],
            [
                "issued_at",
                "timestamp with time zone",
                False,
            ],
            [
                "bill_to_party_id",
                "uuid",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
            [
                "currency_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "c",
                "CHECK (currency_decimal_places_snapshot <= 8)",
                True,
            ],
            [
                "c",
                "CHECK (currency_decimal_places_snapshot >= 0)",
                True,
            ],
            [
                "c",
                "CHECK (due_date IS NULL OR due_date >= invoice_date)",
                True,
            ],
            [
                "c",
                (
                    "CHECK (issued_at IS NULL AND status::text = 'draft'::text OR iss"
                    "ued_at IS NOT NULL AND status::text = 'issued'::text)"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (bill_to_party_id) REFERENCES party_party(id) DEFERR"
                    "ABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (currency_id) REFERENCES reference_currency(id) DEFE"
                    "RRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (company_id, number)",
                True,
            ],
        ],
    },
    "party_party": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "is_active",
                "boolean",
                True,
            ],
            [
                "party_type",
                "character varying(16)",
                True,
            ],
            [
                "display_name",
                "character varying(200)",
                True,
            ],
            [
                "legal_name",
                "character varying(200)",
                True,
            ],
            [
                "is_customer",
                "boolean",
                True,
            ],
            [
                "is_supplier",
                "boolean",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
        ],
    },
    "reference_currency": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "is_active",
                "boolean",
                True,
            ],
            [
                "name",
                "character varying(120)",
                True,
            ],
            [
                "code",
                "character varying(3)",
                True,
            ],
            [
                "symbol",
                "character varying(8)",
                True,
            ],
            [
                "decimal_places",
                "smallint",
                True,
            ],
        ],
        "constraints": [
            [
                "c",
                "CHECK (decimal_places >= 0)",
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (code)",
                True,
            ],
        ],
    },
    "accounting_account": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "code",
                "character varying(32)",
                True,
            ],
            [
                "name",
                "character varying(160)",
                True,
            ],
            [
                "type",
                "character varying(9)",
                True,
            ],
            [
                "is_active",
                "boolean",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "c",
                (
                    "CHECK (type::text = ANY (ARRAY['ASSET'::character varying, 'LIAB"
                    "ILITY'::character varying, 'EQUITY'::character varying, 'INCOME'"
                    "::character varying, 'EXPENSE'::character varying]::text[]))"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (company_id, code)",
                True,
            ],
        ],
    },
    "accounting_journal": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "code",
                "character varying(32)",
                True,
            ],
            [
                "name",
                "character varying(160)",
                True,
            ],
            [
                "is_active",
                "boolean",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (company_id, code)",
                True,
            ],
        ],
    },
    "accounting_journalentry": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "number",
                "character varying(35)",
                True,
            ],
            [
                "entry_date",
                "date",
                True,
            ],
            [
                "memo",
                "text",
                True,
            ],
            [
                "status",
                "character varying(6)",
                True,
            ],
            [
                "base_currency_code_snapshot",
                "character varying(3)",
                True,
            ],
            [
                "base_currency_precision_snapshot",
                "smallint",
                True,
            ],
            [
                "posted_at",
                "timestamp with time zone",
                False,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
            [
                "journal_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "c",
                (
                    "CHECK (base_currency_precision_snapshot >= 0 AND base_currency_p"
                    "recision_snapshot <= 8)"
                ),
                True,
            ],
            [
                "c",
                "CHECK (base_currency_precision_snapshot >= 0)",
                True,
            ],
            [
                "c",
                (
                    "CHECK (posted_at IS NULL AND status::text = 'DRAFT'::text OR pos"
                    "ted_at IS NOT NULL AND status::text = 'POSTED'::text)"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (journal_id) REFERENCES accounting_journal(id) DEFER"
                    "RABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (company_id, number)",
                True,
            ],
        ],
    },
    "accounting_journalentryline": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "description",
                "text",
                True,
            ],
            [
                "debit",
                "numeric(38,8)",
                True,
            ],
            [
                "credit",
                "numeric(38,8)",
                True,
            ],
            [
                "position",
                "integer",
                True,
            ],
            [
                "account_id",
                "uuid",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
            [
                "journal_entry_id",
                "uuid",
                True,
            ],
            [
                "party_id",
                "uuid",
                False,
            ],
        ],
        "constraints": [
            [
                "c",
                'CHECK ("position" > 0 AND "position" <= 2147483647)',
                True,
            ],
            [
                "c",
                'CHECK ("position" >= 0)',
                True,
            ],
            [
                "c",
                (
                    "CHECK (credit = 0::numeric AND debit > 0::numeric OR credit > 0:"
                    ":numeric AND debit = 0::numeric)"
                ),
                True,
            ],
            [
                "c",
                (
                    "CHECK (credit >= 0::numeric AND credit < '1000000000000000000000"
                    "000000000'::numeric AND debit >= 0::numeric AND debit < '1000000"
                    "000000000000000000000000'::numeric)"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (account_id) REFERENCES accounting_account(id) DEFER"
                    "RABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (journal_entry_id) REFERENCES accounting_journalentr"
                    "y(id) DEFERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                ("FOREIGN KEY (party_id) REFERENCES party_party(id) DEFERRABLE INITIALLY DEFERRED"),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                'UNIQUE (journal_entry_id, "position")',
                True,
            ],
        ],
    },
    "billing_invoiceline": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "description",
                "text",
                True,
            ],
            [
                "quantity",
                "numeric(18,4)",
                True,
            ],
            [
                "unit_price",
                "numeric(18,4)",
                True,
            ],
            [
                "position",
                "integer",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
            [
                "invoice_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "c",
                'CHECK ("position" > 0)',
                True,
            ],
            [
                "c",
                'CHECK ("position" >= 0)',
                True,
            ],
            [
                "c",
                "CHECK (quantity > 0::numeric)",
                True,
            ],
            [
                "c",
                "CHECK (unit_price >= 0::numeric)",
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (invoice_id) REFERENCES billing_invoice(id) DEFERRAB"
                    "LE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                'UNIQUE (invoice_id, "position")',
                True,
            ],
        ],
    },
    "business_audit_auditentry": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "action",
                "character varying(100)",
                True,
            ],
            [
                "object_type",
                "character varying(100)",
                True,
            ],
            [
                "object_id",
                "character varying(128)",
                True,
            ],
            [
                "occurred_at",
                "timestamp with time zone",
                True,
            ],
            [
                "metadata",
                "jsonb",
                True,
            ],
            [
                "actor_id",
                "uuid",
                True,
            ],
            [
                "company_id",
                "uuid",
                False,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (actor_id) REFERENCES identity_user(id) DEFERRABLE I"
                    "NITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
        ],
    },
    "module_registry_businessmodule": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "code",
                "character varying(64)",
                True,
            ],
            [
                "name",
                "character varying(160)",
                True,
            ],
            [
                "version",
                "character varying(64)",
                True,
            ],
            [
                "dependencies",
                "jsonb",
                True,
            ],
            [
                "declared_permissions",
                "jsonb",
                True,
            ],
            [
                "is_enabled",
                "boolean",
                True,
            ],
        ],
        "constraints": [
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (code)",
                True,
            ],
        ],
    },
    "payments_billing_paymentallocation": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "amount",
                "numeric(38,8)",
                True,
            ],
            [
                "idempotency_key",
                "character varying(128)",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
            [
                "payment_id",
                "uuid",
                True,
            ],
            [
                "invoice_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "c",
                "CHECK (amount < '1000000000000000000000000000000'::numeric)",
                True,
            ],
            [
                "c",
                "CHECK (amount > 0::numeric)",
                True,
            ],
            [
                "c",
                (
                    "CHECK (length(TRIM(BOTH FROM idempotency_key)) > 0 AND length(id"
                    "empotency_key::text) <= 128 AND idempotency_key::text ~ '\\S'::te"
                    "xt)"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (invoice_id) REFERENCES billing_invoice(id) DEFERRAB"
                    "LE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (payment_id) REFERENCES payments_payment(id) DEFERRA"
                    "BLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (company_id, idempotency_key)",
                True,
            ],
        ],
    },
    "payments_payment": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "number",
                "character varying(40)",
                True,
            ],
            [
                "payer_display_name_snapshot",
                "character varying(200)",
                True,
            ],
            [
                "payer_legal_name_snapshot",
                "character varying(200)",
                True,
            ],
            [
                "payment_date",
                "date",
                True,
            ],
            [
                "currency_code_snapshot",
                "character varying(3)",
                True,
            ],
            [
                "currency_decimal_places_snapshot",
                "smallint",
                True,
            ],
            [
                "amount",
                "numeric(38,8)",
                True,
            ],
            [
                "payment_method_code_snapshot",
                "character varying(32)",
                True,
            ],
            [
                "payment_method_name_snapshot",
                "character varying(160)",
                True,
            ],
            [
                "external_reference",
                "character varying(128)",
                True,
            ],
            [
                "idempotency_key",
                "character varying(128)",
                False,
            ],
            [
                "notes",
                "text",
                True,
            ],
            [
                "recorded_at",
                "timestamp with time zone",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
            [
                "currency_id",
                "uuid",
                True,
            ],
            [
                "payer_party_id",
                "uuid",
                True,
            ],
            [
                "payment_method_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "c",
                "CHECK (amount < '1000000000000000000000000000000'::numeric)",
                True,
            ],
            [
                "c",
                "CHECK (amount > 0::numeric)",
                True,
            ],
            [
                "c",
                (
                    "CHECK (currency_decimal_places_snapshot >= 0 AND currency_decima"
                    "l_places_snapshot <= 8)"
                ),
                True,
            ],
            [
                "c",
                "CHECK (currency_decimal_places_snapshot >= 0)",
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (currency_id) REFERENCES reference_currency(id) DEFE"
                    "RRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (payer_party_id) REFERENCES party_party(id) DEFERRAB"
                    "LE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (payment_method_id) REFERENCES payments_paymentmetho"
                    "d(id) DEFERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (company_id, number)",
                True,
            ],
        ],
    },
    "payments_paymentmethod": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "code",
                "character varying(32)",
                True,
            ],
            [
                "name",
                "character varying(160)",
                True,
            ],
            [
                "is_active",
                "boolean",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (company_id, code)",
                True,
            ],
        ],
    },
}

BINDINGS = {
    "accounting_billing_invoiceposting": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "effect",
                "character varying(40)",
                True,
            ],
            [
                "ar_account_id",
                "uuid",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
            [
                "invoice_id",
                "uuid",
                True,
            ],
            [
                "journal_id",
                "uuid",
                True,
            ],
            [
                "journal_entry_id",
                "uuid",
                True,
            ],
            [
                "revenue_account_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "c",
                "CHECK (effect::text = 'billing_invoice_ar_revenue_v1'::text)",
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (ar_account_id) REFERENCES accounting_account(id) DE"
                    "FERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (invoice_id) REFERENCES billing_invoice(id) DEFERRAB"
                    "LE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (journal_entry_id) REFERENCES accounting_journalentr"
                    "y(id) DEFERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (journal_id) REFERENCES accounting_journal(id) DEFER"
                    "RABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (revenue_account_id) REFERENCES accounting_account(i"
                    "d) DEFERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (company_id, invoice_id, effect)",
                True,
            ],
            [
                "u",
                "UNIQUE (journal_entry_id)",
                True,
            ],
        ],
    },
    "accounting_payments_billing_allocationposting": {
        "kind": "r",
        "schema": "public",
        "columns": [
            [
                "id",
                "uuid",
                True,
            ],
            [
                "created_at",
                "timestamp with time zone",
                True,
            ],
            [
                "updated_at",
                "timestamp with time zone",
                True,
            ],
            [
                "effect",
                "character varying(40)",
                True,
            ],
            [
                "allocation_id",
                "uuid",
                True,
            ],
            [
                "ar_account_id",
                "uuid",
                True,
            ],
            [
                "cash_account_id",
                "uuid",
                True,
            ],
            [
                "company_id",
                "uuid",
                True,
            ],
            [
                "invoice_posting_id",
                "uuid",
                True,
            ],
            [
                "journal_id",
                "uuid",
                True,
            ],
            [
                "journal_entry_id",
                "uuid",
                True,
            ],
        ],
        "constraints": [
            [
                "c",
                "CHECK (effect::text = 'payment_allocation_cash_ar_v1'::text)",
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (allocation_id) REFERENCES payments_billing_paymenta"
                    "llocation(id) DEFERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (ar_account_id) REFERENCES accounting_account(id) DE"
                    "FERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (cash_account_id) REFERENCES accounting_account(id) "
                    "DEFERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (company_id) REFERENCES organization_company(id) DEF"
                    "ERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (invoice_posting_id) REFERENCES accounting_billing_i"
                    "nvoiceposting(id) DEFERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (journal_entry_id) REFERENCES accounting_journalentr"
                    "y(id) DEFERRABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "f",
                (
                    "FOREIGN KEY (journal_id) REFERENCES accounting_journal(id) DEFER"
                    "RABLE INITIALLY DEFERRED"
                ),
                True,
            ],
            [
                "p",
                "PRIMARY KEY (id)",
                True,
            ],
            [
                "u",
                "UNIQUE (company_id, allocation_id, effect)",
                True,
            ],
            [
                "u",
                "UNIQUE (journal_entry_id)",
                True,
            ],
        ],
    },
}

SQLITE = {
    "django_migrations": (
        'CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY '
        'KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(2'
        '55) NOT NULL, "applied" datetime NOT NULL)'
    ),
    "identity_user": (
        'CREATE TABLE "identity_user" ("password" varchar(128) NOT NULL, '
        '"last_login" datetime NULL, "is_superuser" bool NOT NULL, "id" c'
        'har(32) NOT NULL PRIMARY KEY, "email" varchar(254) NOT NULL UNIQ'
        'UE, "is_active" bool NOT NULL, "is_staff" bool NOT NULL, "create'
        'd_at" datetime NOT NULL, "updated_at" datetime NOT NULL)'
    ),
    "organization_branch": (
        'CREATE TABLE "organization_branch" ("id" char(32) NOT NULL PRIMA'
        'RY KEY, "created_at" datetime NOT NULL, "updated_at" datetime NO'
        'T NULL, "is_active" bool NOT NULL, "code" varchar(32) NOT NULL, '
        '"name" varchar(160) NOT NULL, "company_id" char(32) NOT NULL REF'
        'ERENCES "organization_company" ("id") DEFERRABLE INITIALLY DEFER'
        'RED, CONSTRAINT "unique_branch_code_per_company" UNIQUE ("compan'
        'y_id", "code"))'
    ),
    "organization_company": (
        'CREATE TABLE "organization_company" ("id" char(32) NOT NULL PRIM'
        'ARY KEY, "created_at" datetime NOT NULL, "updated_at" datetime N'
        'OT NULL, "is_active" bool NOT NULL, "code" varchar(32) NOT NULL '
        'UNIQUE, "name" varchar(160) NOT NULL, "timezone" varchar(64) NOT'
        ' NULL, "base_currency_id" char(32) NOT NULL REFERENCES "referenc'
        'e_currency" ("id") DEFERRABLE INITIALLY DEFERRED, "country_id" c'
        'har(32) NOT NULL REFERENCES "reference_country" ("id") DEFERRABL'
        'E INITIALLY DEFERRED, "default_language_id" char(32) NOT NULL RE'
        'FERENCES "reference_language" ("id") DEFERRABLE INITIALLY DEFERR'
        "ED)"
    ),
    "organization_warehouse": (
        'CREATE TABLE "organization_warehouse" ("id" char(32) NOT NULL PR'
        'IMARY KEY, "created_at" datetime NOT NULL, "updated_at" datetime'
        ' NOT NULL, "is_active" bool NOT NULL, "code" varchar(32) NOT NUL'
        'L, "name" varchar(160) NOT NULL, "branch_id" char(32) NULL REFER'
        'ENCES "organization_branch" ("id") DEFERRABLE INITIALLY DEFERRED'
        ', "company_id" char(32) NOT NULL REFERENCES "organization_compan'
        'y" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "unique_ware'
        'house_code_per_company" UNIQUE ("company_id", "code"))'
    ),
    "access_permission": (
        'CREATE TABLE "access_permission" ("id" char(32) NOT NULL PRIMARY'
        ' KEY, "created_at" datetime NOT NULL, "updated_at" datetime NOT '
        'NULL, "code" varchar(100) NOT NULL UNIQUE, "name" varchar(160) N'
        'OT NULL, "is_active" bool NOT NULL)'
    ),
    "access_role": (
        'CREATE TABLE "access_role" ("id" char(32) NOT NULL PRIMARY KEY, '
        '"created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, '
        '"code" varchar(64) NOT NULL, "name" varchar(160) NOT NULL, "is_a'
        'ctive" bool NOT NULL, "company_id" char(32) NOT NULL REFERENCES '
        '"organization_company" ("id") DEFERRABLE INITIALLY DEFERRED, CON'
        'STRAINT "unique_role_code_company" UNIQUE ("company_id", "code")'
        ")"
    ),
    "access_userbranchaccess": (
        'CREATE TABLE "access_userbranchaccess" ("id" char(32) NOT NULL P'
        'RIMARY KEY, "created_at" datetime NOT NULL, "updated_at" datetim'
        'e NOT NULL, "branch_id" char(32) NOT NULL REFERENCES "organizati'
        'on_branch" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" char('
        '32) NOT NULL REFERENCES "identity_user" ("id") DEFERRABLE INITIA'
        'LLY DEFERRED, CONSTRAINT "unique_user_branch_access" UNIQUE ("us'
        'er_id", "branch_id"))'
    ),
    "access_usercompanyaccess": (
        'CREATE TABLE "access_usercompanyaccess" ("id" char(32) NOT NULL '
        'PRIMARY KEY, "created_at" datetime NOT NULL, "updated_at" dateti'
        'me NOT NULL, "company_id" char(32) NOT NULL REFERENCES "organiza'
        'tion_company" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" ch'
        'ar(32) NOT NULL REFERENCES "identity_user" ("id") DEFERRABLE INI'
        'TIALLY DEFERRED, CONSTRAINT "unique_user_company_access" UNIQUE '
        '("user_id", "company_id"))'
    ),
    "access_userwarehouseaccess": (
        'CREATE TABLE "access_userwarehouseaccess" ("id" char(32) NOT NUL'
        'L PRIMARY KEY, "created_at" datetime NOT NULL, "updated_at" date'
        'time NOT NULL, "user_id" char(32) NOT NULL REFERENCES "identity_'
        'user" ("id") DEFERRABLE INITIALLY DEFERRED, "warehouse_id" char('
        '32) NOT NULL REFERENCES "organization_warehouse" ("id") DEFERRAB'
        'LE INITIALLY DEFERRED, CONSTRAINT "unique_user_warehouse_access"'
        ' UNIQUE ("user_id", "warehouse_id"))'
    ),
    "access_rolepermission": (
        'CREATE TABLE "access_rolepermission" ("id" char(32) NOT NULL PRI'
        'MARY KEY, "created_at" datetime NOT NULL, "updated_at" datetime '
        'NOT NULL, "permission_id" char(32) NOT NULL REFERENCES "access_p'
        'ermission" ("id") DEFERRABLE INITIALLY DEFERRED, "role_id" char('
        '32) NOT NULL REFERENCES "access_role" ("id") DEFERRABLE INITIALL'
        'Y DEFERRED, CONSTRAINT "unique_permission_per_role" UNIQUE ("rol'
        'e_id", "permission_id"))'
    ),
    "access_userroleassignment": (
        'CREATE TABLE "access_userroleassignment" ("id" char(32) NOT NULL'
        ' PRIMARY KEY, "created_at" datetime NOT NULL, "updated_at" datet'
        'ime NOT NULL, "company_id" char(32) NOT NULL REFERENCES "organiz'
        'ation_company" ("id") DEFERRABLE INITIALLY DEFERRED, "role_id" c'
        'har(32) NOT NULL REFERENCES "access_role" ("id") DEFERRABLE INIT'
        'IALLY DEFERRED, "user_id" char(32) NOT NULL REFERENCES "identity'
        '_user" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "unique_'
        'user_company_role" UNIQUE ("user_id", "company_id", "role_id"))'
    ),
    "billing_invoice": (
        'CREATE TABLE "billing_invoice" ("id" char(32) NOT NULL PRIMARY K'
        'EY, "created_at" datetime NOT NULL, "updated_at" datetime NOT NU'
        'LL, "number" varchar(40) NOT NULL, "bill_to_display_name_snapsho'
        't" varchar(200) NOT NULL, "bill_to_legal_name_snapshot" varchar('
        '200) NOT NULL, "invoice_date" date NOT NULL, "due_date" date NUL'
        'L, "currency_code_snapshot" varchar(3) NOT NULL, "currency_decim'
        'al_places_snapshot" smallint unsigned NOT NULL CHECK ("currency_'
        'decimal_places_snapshot" >= 0), "status" varchar(8) NOT NULL, "n'
        'otes" text NOT NULL, "issued_at" datetime NULL, "bill_to_party_i'
        'd" char(32) NOT NULL REFERENCES "party_party" ("id") DEFERRABLE '
        'INITIALLY DEFERRED, "company_id" char(32) NOT NULL REFERENCES "o'
        'rganization_company" ("id") DEFERRABLE INITIALLY DEFERRED, "curr'
        'ency_id" char(32) NOT NULL REFERENCES "reference_currency" ("id"'
        ') DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "billing_company_num'
        'ber_uniq" UNIQUE ("company_id", "number"), CONSTRAINT "billing_i'
        'nvoice_lifecycle" CHECK ((("issued_at" IS NULL AND "status" = \'d'
        'raft\') OR ("issued_at" IS NOT NULL AND "status" = \'issued\'))), C'
        'ONSTRAINT "billing_currency_precision" CHECK ("currency_decimal_'
        'places_snapshot" <= 8), CONSTRAINT "billing_due_date_order" CHEC'
        'K (("due_date" IS NULL OR "due_date" >= ("invoice_date"))))'
    ),
    "party_party": (
        'CREATE TABLE "party_party" ("id" char(32) NOT NULL PRIMARY KEY, '
        '"created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, '
        '"is_active" bool NOT NULL, "party_type" varchar(16) NOT NULL, "d'
        'isplay_name" varchar(200) NOT NULL, "legal_name" varchar(200) NO'
        'T NULL, "is_customer" bool NOT NULL, "is_supplier" bool NOT NULL'
        ', "company_id" char(32) NOT NULL REFERENCES "organization_compan'
        'y" ("id") DEFERRABLE INITIALLY DEFERRED)'
    ),
    "reference_currency": (
        'CREATE TABLE "reference_currency" ("id" char(32) NOT NULL PRIMAR'
        'Y KEY, "created_at" datetime NOT NULL, "updated_at" datetime NOT'
        ' NULL, "is_active" bool NOT NULL, "name" varchar(120) NOT NULL, '
        '"code" varchar(3) NOT NULL UNIQUE, "symbol" varchar(8) NOT NULL,'
        ' "decimal_places" smallint unsigned NOT NULL CHECK ("decimal_pla'
        'ces" >= 0))'
    ),
    "accounting_account": (
        'CREATE TABLE "accounting_account" ("id" char(32) NOT NULL PRIMAR'
        'Y KEY, "created_at" datetime NOT NULL, "updated_at" datetime NOT'
        ' NULL, "code" varchar(32) NOT NULL, "name" varchar(160) NOT NULL'
        ', "type" varchar(9) NOT NULL, "is_active" bool NOT NULL, "compan'
        'y_id" char(32) NOT NULL REFERENCES "organization_company" ("id")'
        ' DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "accounting_account_c'
        'ode_uniq" UNIQUE ("company_id", "code"), CONSTRAINT "accounting_'
        "account_type\" CHECK (\"type\" IN ('ASSET', 'LIABILITY', 'EQUITY', "
        "'INCOME', 'EXPENSE')))"
    ),
    "accounting_journal": (
        'CREATE TABLE "accounting_journal" ("id" char(32) NOT NULL PRIMAR'
        'Y KEY, "created_at" datetime NOT NULL, "updated_at" datetime NOT'
        ' NULL, "code" varchar(32) NOT NULL, "name" varchar(160) NOT NULL'
        ', "is_active" bool NOT NULL, "company_id" char(32) NOT NULL REFE'
        'RENCES "organization_company" ("id") DEFERRABLE INITIALLY DEFERR'
        'ED, CONSTRAINT "accounting_journal_code_uniq" UNIQUE ("company_i'
        'd", "code"))'
    ),
    "accounting_journalentry": (
        'CREATE TABLE "accounting_journalentry" ("id" char(32) NOT NULL P'
        'RIMARY KEY, "created_at" datetime NOT NULL, "updated_at" datetim'
        'e NOT NULL, "number" varchar(35) NOT NULL, "entry_date" date NOT'
        ' NULL, "memo" text NOT NULL, "status" varchar(6) NOT NULL, "base'
        '_currency_code_snapshot" varchar(3) NOT NULL, "base_currency_pre'
        'cision_snapshot" smallint unsigned NOT NULL CHECK ("base_currenc'
        'y_precision_snapshot" >= 0), "posted_at" datetime NULL, "company'
        '_id" char(32) NOT NULL REFERENCES "organization_company" ("id") '
        'DEFERRABLE INITIALLY DEFERRED, "journal_id" char(32) NOT NULL RE'
        'FERENCES "accounting_journal" ("id") DEFERRABLE INITIALLY DEFERR'
        'ED, CONSTRAINT "accounting_entry_number_uniq" UNIQUE ("company_i'
        'd", "number"), CONSTRAINT "accounting_entry_lifecycle" CHECK ((('
        '"posted_at" IS NULL AND "status" = \'DRAFT\') OR ("posted_at" IS N'
        'OT NULL AND "status" = \'POSTED\'))), CONSTRAINT "accounting_entry'
        '_precision" CHECK (("base_currency_precision_snapshot" >= 0 AND '
        '"base_currency_precision_snapshot" <= 8)))'
    ),
    "accounting_journalentryline": (
        'CREATE TABLE "accounting_journalentryline" ("id" char(32) NOT NU'
        'LL PRIMARY KEY, "created_at" datetime NOT NULL, "updated_at" dat'
        'etime NOT NULL, "description" text NOT NULL, "debit" decimal NOT'
        ' NULL, "credit" decimal NOT NULL, "position" integer unsigned NO'
        'T NULL CHECK ("position" >= 0), "account_id" char(32) NOT NULL R'
        'EFERENCES "accounting_account" ("id") DEFERRABLE INITIALLY DEFER'
        'RED, "company_id" char(32) NOT NULL REFERENCES "organization_com'
        'pany" ("id") DEFERRABLE INITIALLY DEFERRED, "journal_entry_id" c'
        'har(32) NOT NULL REFERENCES "accounting_journalentry" ("id") DEF'
        'ERRABLE INITIALLY DEFERRED, "party_id" char(32) NULL REFERENCES '
        '"party_party" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "'
        'accounting_line_position_uniq" UNIQUE ("journal_entry_id", "posi'
        'tion"), CONSTRAINT "accounting_line_position" CHECK (("position"'
        ' > 0 AND "position" <= 2147483647)), CONSTRAINT "accounting_line'
        '_amount_range" CHECK (("credit" >= \'0\' AND "credit" < \'1E+30\' AN'
        'D "debit" >= \'0\' AND "debit" < \'1E+30\')), CONSTRAINT "accounting'
        '_line_sides" CHECK ((("credit" = \'0\' AND "debit" > \'0\') OR ("cre'
        "dit\" > '0' AND \"debit\" = '0'))))"
    ),
    "billing_invoiceline": (
        'CREATE TABLE "billing_invoiceline" ("id" char(32) NOT NULL PRIMA'
        'RY KEY, "created_at" datetime NOT NULL, "updated_at" datetime NO'
        'T NULL, "description" text NOT NULL, "quantity" decimal NOT NULL'
        ', "unit_price" decimal NOT NULL, "position" integer unsigned NOT'
        ' NULL CHECK ("position" >= 0), "company_id" char(32) NOT NULL RE'
        'FERENCES "organization_company" ("id") DEFERRABLE INITIALLY DEFE'
        'RRED, "invoice_id" char(32) NOT NULL REFERENCES "billing_invoice'
        '" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "billing_quan'
        'tity_positive" CHECK ("quantity" > \'0\'), CONSTRAINT "billing_pri'
        'ce_nonnegative" CHECK ("unit_price" >= \'0\'), CONSTRAINT "billing'
        '_position_positive" CHECK ("position" > 0), CONSTRAINT "billing_'
        'line_position_uniq" UNIQUE ("invoice_id", "position"))'
    ),
    "business_audit_auditentry": (
        'CREATE TABLE "business_audit_auditentry" ("id" char(32) NOT NULL'
        ' PRIMARY KEY, "created_at" datetime NOT NULL, "updated_at" datet'
        'ime NOT NULL, "action" varchar(100) NOT NULL, "object_type" varc'
        'har(100) NOT NULL, "object_id" varchar(128) NOT NULL, "occurred_'
        'at" datetime NOT NULL, "metadata" text NOT NULL CHECK ((JSON_VAL'
        'ID("metadata") OR "metadata" IS NULL)), "actor_id" char(32) NOT '
        'NULL REFERENCES "identity_user" ("id") DEFERRABLE INITIALLY DEFE'
        'RRED, "company_id" char(32) NULL REFERENCES "organization_compan'
        'y" ("id") DEFERRABLE INITIALLY DEFERRED)'
    ),
    "module_registry_businessmodule": (
        'CREATE TABLE "module_registry_businessmodule" ("id" char(32) NOT'
        ' NULL PRIMARY KEY, "created_at" datetime NOT NULL, "updated_at" '
        'datetime NOT NULL, "code" varchar(64) NOT NULL UNIQUE, "name" va'
        'rchar(160) NOT NULL, "version" varchar(64) NOT NULL, "dependenci'
        'es" text NOT NULL CHECK ((JSON_VALID("dependencies") OR "depende'
        'ncies" IS NULL)), "declared_permissions" text NOT NULL CHECK ((J'
        'SON_VALID("declared_permissions") OR "declared_permissions" IS N'
        'ULL)), "is_enabled" bool NOT NULL)'
    ),
    "payments_billing_paymentallocation": (
        'CREATE TABLE "payments_billing_paymentallocation" ("id" char(32)'
        ' NOT NULL PRIMARY KEY, "created_at" datetime NOT NULL, "updated_'
        'at" datetime NOT NULL, "amount" decimal NOT NULL, "idempotency_k'
        'ey" varchar(128) NOT NULL, "company_id" char(32) NOT NULL REFERE'
        'NCES "organization_company" ("id") DEFERRABLE INITIALLY DEFERRED'
        ', "payment_id" char(32) NOT NULL REFERENCES "payments_payment" ('
        '"id") DEFERRABLE INITIALLY DEFERRED, "invoice_id" char(32) NOT N'
        'ULL REFERENCES "billing_invoice" ("id") DEFERRABLE INITIALLY DEF'
        'ERRED, CONSTRAINT "allocation_company_key_uniq" UNIQUE ("company'
        '_id", "idempotency_key"), CONSTRAINT "allocation_amount_positive'
        '" CHECK ("amount" > \'0\'), CONSTRAINT "allocation_amount_range" C'
        'HECK ("amount" < \'1E+30\'), CONSTRAINT "allocation_key_bounds" CH'
        'ECK ((LENGTH(TRIM("idempotency_key")) > 0 AND LENGTH("idempotenc'
        'y_key") <= 128 AND "idempotency_key" REGEXP \'\\S\')))'
    ),
    "payments_payment": (
        'CREATE TABLE "payments_payment" ("id" char(32) NOT NULL PRIMARY '
        'KEY, "created_at" datetime NOT NULL, "updated_at" datetime NOT N'
        'ULL, "number" varchar(40) NOT NULL, "payer_display_name_snapshot'
        '" varchar(200) NOT NULL, "payer_legal_name_snapshot" varchar(200'
        ') NOT NULL, "payment_date" date NOT NULL, "currency_code_snapsho'
        't" varchar(3) NOT NULL, "currency_decimal_places_snapshot" small'
        'int unsigned NOT NULL CHECK ("currency_decimal_places_snapshot" '
        '>= 0), "amount" decimal NOT NULL, "payment_method_code_snapshot"'
        ' varchar(32) NOT NULL, "payment_method_name_snapshot" varchar(16'
        '0) NOT NULL, "external_reference" varchar(128) NOT NULL, "idempo'
        'tency_key" varchar(128) NULL, "notes" text NOT NULL, "recorded_a'
        't" datetime NOT NULL, "company_id" char(32) NOT NULL REFERENCES '
        '"organization_company" ("id") DEFERRABLE INITIALLY DEFERRED, "cu'
        'rrency_id" char(32) NOT NULL REFERENCES "reference_currency" ("i'
        'd") DEFERRABLE INITIALLY DEFERRED, "payer_party_id" char(32) NOT'
        ' NULL REFERENCES "party_party" ("id") DEFERRABLE INITIALLY DEFER'
        'RED, "payment_method_id" char(32) NOT NULL REFERENCES "payments_'
        'paymentmethod" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT '
        '"payments_company_number_uniq" UNIQUE ("company_id", "number"), '
        'CONSTRAINT "payments_amount_positive" CHECK ("amount" > \'0\'), CO'
        'NSTRAINT "payments_amount_range" CHECK ("amount" < \'1E+30\'), CON'
        'STRAINT "payments_currency_precision" CHECK (("currency_decimal_'
        'places_snapshot" >= 0 AND "currency_decimal_places_snapshot" <= '
        "8)))"
    ),
    "payments_paymentmethod": (
        'CREATE TABLE "payments_paymentmethod" ("id" char(32) NOT NULL PR'
        'IMARY KEY, "created_at" datetime NOT NULL, "updated_at" datetime'
        ' NOT NULL, "code" varchar(32) NOT NULL, "name" varchar(160) NOT '
        'NULL, "is_active" bool NOT NULL, "company_id" char(32) NOT NULL '
        'REFERENCES "organization_company" ("id") DEFERRABLE INITIALLY DE'
        'FERRED, CONSTRAINT "payments_method_code_uniq" UNIQUE ("company_'
        'id", "code"))'
    ),
    "accounting_billing_invoiceposting": (
        'CREATE TABLE "accounting_billing_invoiceposting" ("id" char(32) '
        'NOT NULL PRIMARY KEY, "created_at" datetime NOT NULL, "updated_a'
        't" datetime NOT NULL, "effect" varchar(40) NOT NULL, "ar_account'
        '_id" char(32) NOT NULL REFERENCES "accounting_account" ("id") DE'
        'FERRABLE INITIALLY DEFERRED, "company_id" char(32) NOT NULL REFE'
        'RENCES "organization_company" ("id") DEFERRABLE INITIALLY DEFERR'
        'ED, "invoice_id" char(32) NOT NULL REFERENCES "billing_invoice" '
        '("id") DEFERRABLE INITIALLY DEFERRED, "journal_id" char(32) NOT '
        'NULL REFERENCES "accounting_journal" ("id") DEFERRABLE INITIALLY'
        ' DEFERRED, "journal_entry_id" char(32) NOT NULL UNIQUE REFERENCE'
        'S "accounting_journalentry" ("id") DEFERRABLE INITIALLY DEFERRED'
        ', "revenue_account_id" char(32) NOT NULL REFERENCES "accounting_'
        'account" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "invoi'
        'ce_posting_source_uniq" UNIQUE ("company_id", "invoice_id", "eff'
        'ect"), CONSTRAINT "invoice_posting_effect" CHECK ("effect" = \'bi'
        "lling_invoice_ar_revenue_v1'))"
    ),
    "accounting_payments_billing_allocationposting": (
        'CREATE TABLE "accounting_payments_billing_allocationposting" ("i'
        'd" char(32) NOT NULL PRIMARY KEY, "created_at" datetime NOT NULL'
        ', "updated_at" datetime NOT NULL, "effect" varchar(40) NOT NULL,'
        ' "allocation_id" char(32) NOT NULL REFERENCES "payments_billing_'
        'paymentallocation" ("id") DEFERRABLE INITIALLY DEFERRED, "ar_acc'
        'ount_id" char(32) NOT NULL REFERENCES "accounting_account" ("id"'
        ') DEFERRABLE INITIALLY DEFERRED, "cash_account_id" char(32) NOT '
        'NULL REFERENCES "accounting_account" ("id") DEFERRABLE INITIALLY'
        ' DEFERRED, "company_id" char(32) NOT NULL REFERENCES "organizati'
        'on_company" ("id") DEFERRABLE INITIALLY DEFERRED, "invoice_posti'
        'ng_id" char(32) NOT NULL REFERENCES "accounting_billing_invoicep'
        'osting" ("id") DEFERRABLE INITIALLY DEFERRED, "journal_id" char('
        '32) NOT NULL REFERENCES "accounting_journal" ("id") DEFERRABLE I'
        'NITIALLY DEFERRED, "journal_entry_id" char(32) NOT NULL UNIQUE R'
        'EFERENCES "accounting_journalentry" ("id") DEFERRABLE INITIALLY '
        'DEFERRED, CONSTRAINT "allocation_posting_source_uniq" UNIQUE ("c'
        'ompany_id", "allocation_id", "effect"), CONSTRAINT "allocation_p'
        'osting_effect" CHECK ("effect" = \'payment_allocation_cash_ar_v1\''
        "))"
    ),
}
