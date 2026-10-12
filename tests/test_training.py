import pytest

from app.training.qlora import assert_training_allowed, eligible_records, memory_stop, qlora_config, run_training, split_records


def test_training_is_refused_by_default():
    with pytest.raises(Exception):
        assert_training_allowed(False, False)
    with pytest.raises(Exception):
        run_training(False, True)


def test_only_licensed_records_are_eligible():
    records = [
        {"training_allowed": True, "copyright_or_license_status": "original-structured-notes", "text": "no"},
        {"training_allowed": True, "copyright_or_license_status": "apache-2.0", "text": "yes"},
        {"training_allowed": False, "copyright_or_license_status": "mit", "text": "nope"},
    ]
    chosen = eligible_records(records)
    assert [row["text"] for row in chosen] == ["yes"]
    parts = split_records(chosen * 3, seed=1)
    assert set(parts) == {"train", "validation", "evaluation"}
    assert memory_stop(1000, 9000)
    assert qlora_config()["per_device_train_batch_size"] == 1
    assert qlora_config()["gradient_checkpointing"] is True
