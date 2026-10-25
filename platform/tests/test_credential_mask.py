"""Masked credential values sent back by the dashboard must not overwrite stored secrets."""

from core.credential_vault import CREDENTIAL_MASK, submitted_credential_values


def test_mask_and_empty_values_are_dropped() -> None:
    submitted = submitted_credential_values(
        {"nip": CREDENTIAL_MASK, "ksef_token": "new-token", "environment": "", "certificate_path": CREDENTIAL_MASK}
    )
    assert submitted == {"ksef_token": "new-token"}


def test_real_values_are_kept() -> None:
    values = {"nip": "5273148508", "environment": "production"}
    assert submitted_credential_values(values) == values


def test_merge_on_rename_keeps_stored_value_for_masked_field() -> None:
    stored = {"nip": "5273148508", "ksef_token": "old-token"}
    merged = {**stored, **submitted_credential_values({"nip": CREDENTIAL_MASK, "ksef_token": "new-token"})}
    assert merged == {"nip": "5273148508", "ksef_token": "new-token"}
