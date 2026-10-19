"""The pinned Phase 2 implementation is an independent behavioral oracle."""
import pytest
from gnome_fortress.engine import World
from research.phase3.reference.engine import World as ReferenceWorld


@pytest.mark.parametrize('seed',[1,42,2026])
def test_reference_full_state_at_boundaries(seed):
    actual,reference=World(seed),ReferenceWorld(seed)
    for boundary in (0,1,100,500,1200):
        actual.step(boundary-actual.tick); reference.step(boundary-reference.tick)
        actual.validate()
        assert actual.state()==reference.state()
        assert actual.rng.getstate()==reference.rng.getstate()


def test_live_index_positions_birth_death_sleep_and_restore():
    w=World(42)
    for a in w.agents.values(): a.x=a.y=1
    a=w.agents[1]; a.x=a.y=4
    w.agents[2].x,w.agents[2].y=5,4
    w.agents[3].x,w.agents[3].y=4,4
    w.agents[3].sleep_until=10
    child=w._spawn(4,3,a.traits,(1,2))
    w.kill(w.agents[2],'test')
    reference=ReferenceWorld.from_state(w.state())
    for own in w.living():
        assert [b.id for b in w._nearby_agents(own)]==[b.id for b in reference._nearby_agents(reference.agents[own.id])]
    assert child.id in w._living_agents and 2 not in w._living_agents
    restored=World.from_state(w.state()); restored.validate()
    assert restored.state()==w.state()
    w.step(20); reference.step(20)
    assert w.state()==reference.state()
