from app.models import SimulationConfig
from app.simulation.state import initialize_simulation


def snapshot_json(config: SimulationConfig) -> str:
    return initialize_simulation(config).definition().model_dump_json()


def test_same_seed_produces_identical_state():
    config = SimulationConfig(seed=42)
    assert snapshot_json(config) == snapshot_json(config)


def test_different_seeds_produce_different_state():
    assert snapshot_json(SimulationConfig(seed=1)) != snapshot_json(SimulationConfig(seed=2))


def test_rng_stream_is_reproducible_after_initialization():
    a = initialize_simulation(SimulationConfig(seed=7))
    b = initialize_simulation(SimulationConfig(seed=7))
    assert [a.rng.random() for _ in range(5)] == [b.rng.random() for _ in range(5)]


def test_difficulty_bounds_initial_patch_age():
    state = initialize_simulation(SimulationConfig(seed=99, difficulty="training"))
    assert all(d.patch.days_since_patch <= 30 for d in state.network.devices())


def test_unsupported_devices_stay_unsupported():
    state = initialize_simulation(SimulationConfig(seed=3))
    assert state.network.get_device("grid-plc-02").patch.level == "unsupported"


def test_patch_level_follows_seeded_age():
    for device in initialize_simulation(SimulationConfig(seed=11, difficulty="challenging")).network.devices():
        if device.patch.level != "unsupported":
            expected = "current" if device.patch.days_since_patch <= 30 else "behind"
            assert device.patch.level == expected


def test_api_reset_is_deterministic(client):
    payload = {"seed": 2024, "difficulty": "challenging"}

    client.post("/api/simulation", json=payload)
    first = client.get("/api/network").json()
    client.post("/api/simulation", json={"seed": 1})
    client.post("/api/simulation", json=payload)
    second = client.get("/api/network").json()

    assert first == second
