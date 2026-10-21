"""Accepted / disabled / observed full-state replay with exact detached saves."""
import hashlib,json,tempfile
from pathlib import Path
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.decision_observation import DecisionObservation,for_world
from gnome_fortress.chronicle import Chronicle
from gnome_fortress.terrain_storage import save_game,load_game
from research.g8b_profile import accepted
from research.saveguard_replay import apply_inputs


def main():
    reference=accepted();results=[]
    with tempfile.TemporaryDirectory(prefix='g8b-replay-') as temp:
        for seed in (1,42):
            worlds=[reference(seed),TerrainWorld(seed),TerrainWorld(seed)]
            o=DecisionObservation();o.start(worlds[2],1);cache=Chronicle();rows=[];restart=None
            rock=next((x,y) for y,row in enumerate(worlds[0].cells) for x,c in enumerate(row) if c.terrain=='rock')
            for tick in range(501):
                for w in worlds:apply_inputs(w,rock)
                cache.prepare(worlds[2])
                if tick in (0,1,9,10,19,20,21,29,30,31,40,60,100,500):
                    state=worlds[0].state();rng=worlds[0].rng.getstate()
                    assert all(w.state()==state and w.rng.getstate()==rng for w in worlds)
                    payload=cache.detach(worlds[2]);captured=payload.restore();assert captured.state()==state
                    path=Path(temp)/f'{seed}.g5.sqlite';save_game(captured,path);loaded=load_game(path)
                    assert loaded.state()==state and for_world(loaded) is None
                    if tick==20:restart=loaded
                    rows.append(dict(tick=tick,digest=loaded.digest(),state_and_rng_exact=True))
                if tick<500:
                    for w in worlds:w.step()
            while restart.tick<500:
                if restart.tick>20:apply_inputs(restart,rock)
                restart.step()
            assert restart.state()==worlds[0].state()
            results.append(dict(seed=seed,boundaries=rows,reload_from=20,reload_exact=True,
                final_digest=worlds[0].digest(),rng_sha256=hashlib.sha256(json.dumps(rng).encode()).hexdigest(),
                births=len(worlds[0].agents)-60,deaths=sum(not a.alive for a in worlds[0].agents.values()),
                record_count=len(o.records),observation_error=o.error))
    Path('docs/g8b/evidence/replay.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':main()
