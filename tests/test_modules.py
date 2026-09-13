import pytest

from businessos.core.modules.manifest import ModuleManifest, validate_manifest
from businessos.core.modules.models import BusinessModule
from businessos.core.modules.selectors import (
    ModuleUnavailable,
    enabled_module_codes,
    is_module_enabled,
    require_module_enabled,
)
from businessos.core.modules.services import register_manifest


def test_manifest_validation_returns_immutable_contract():
    manifest = validate_manifest(
        {"code": "sales", "name": "Sales", "version": "0.1.0", "depends": ["party", "catalog"]}
    )

    assert manifest == ModuleManifest("sales", "Sales", "0.1.0", ("party", "catalog"))
    with pytest.raises(AttributeError):
        manifest.version = "0.2.0"


@pytest.mark.parametrize(
    "manifest",
    [
        {"code": "Sales", "name": "Sales", "version": "0.1.0", "depends": []},
        {"code": "sales", "name": "Sales", "version": "v1", "depends": []},
        {"code": "sales", "name": "Sales", "version": "1.0.0-01", "depends": []},
        {"code": "sales", "name": "Sales", "version": "1.0.0-alpha..beta", "depends": []},
        {"code": "sales", "name": "Sales", "version": "1.0.0+build..meta", "depends": []},
        {"code": "sales", "name": "Sales", "version": "0.1.0", "depends": ["sales"]},
    ],
)
def test_manifest_validation_rejects_invalid_contracts(manifest):
    with pytest.raises(ValueError):
        validate_manifest(manifest)


@pytest.mark.django_db
def test_register_manifest_is_idempotent_and_keeps_enabled_state_explicit():
    value = {"code": "party", "name": "Party", "version": "0.1.0", "depends": []}

    first = register_manifest(value)
    second = register_manifest({**value, "version": "0.1.1"}, enabled=True)

    assert first.id == second.id
    assert second.version == "0.1.1"
    assert second.is_enabled

    third = register_manifest({**value, "version": "0.1.2"})
    assert third.is_enabled


@pytest.mark.django_db
def test_module_state_treats_missing_and_disabled_rows_as_disabled():
    BusinessModule.objects.filter(code="party").delete()

    assert is_module_enabled("party") is False
    assert "party" not in enabled_module_codes()
    with pytest.raises(ModuleUnavailable, match="not enabled"):
        require_module_enabled("party")

    register_manifest(
        {"code": "party", "name": "Party", "version": "0.1.0", "depends": []},
        enabled=False,
    )
    assert is_module_enabled("party") is False

    register_manifest(
        {"code": "party", "name": "Party", "version": "0.1.0", "depends": []},
        enabled=True,
    )
    require_module_enabled("party")
    assert is_module_enabled("party") is True
    assert "party" in enabled_module_codes()
