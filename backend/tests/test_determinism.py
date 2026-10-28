from app.models import SimulationConfig
from app.simulation.state import initialize_simulation


def snapshot_json(config: SimulationConfig) -> str:
    return initialize_simulation(config).snapshot().model_dump_json()


def test_same_seed_produces_identical_state():
    config = SimulationConfig(seed=42)
    assert snapshot_json(config) == snapshot_json(config)


def test_different_seeds_produce_different_state():
    assert snapshot_json(SimulationConfig(seed=1)) != snapshot_json(SimulationConfig(seed=2))


def test_rng_stream_is_reproducible_after_initialization():
    # Later phases draw from state.rng each tick. Both copies must stay in step.
    a = initialize_simulation(SimulationConfig(seed=7))
    b = initialize_simulation(SimulationConfig(seed=7))
    assert [a.rng.random() for _ in range(5)] == [b.rng.random() for _ in range(5)]


def test_difficulty_bounds_initial_patch_age():
    state = initialize_simulation(SimulationConfig(seed=99, difficulty="training"))
    assert all(device.patch_age_days <= 30 for device in state.snapshot().devices)


def test_api_reset_is_deterministic(client):
    payload = {"seed": 2024, "difficulty": "challenging"}

    client.post("/api/simulation", json=payload)
    first = client.get("/api/network").json()
    client.post("/api/simulation", json={"seed": 1})
    client.post("/api/simulation", json=payload)
    second = client.get("/api/network").json()

    assert first == second


def test_create_simulation_returns_summary(client):
    response = client.post("/api/simulation", json={"seed": 5, "tick_minutes": 30})

    assert response.status_code == 201
    body = response.json()
    assert body["config"]["seed"] == 5
    assert body["tick"] == 0
    assert body["device_count"] > 0
