"""One fresh-process experimental run. No default rules or source are edited."""
from collections import Counter
from dataclasses import asdict
import argparse
import json
from pathlib import Path
import platform
import resource
import time

from gnome_fortress.engine import World
from gnome_fortress.storage import load
from research.study import write_csv
from research.phase2_controls import (Config, ExperimentalWorld, biological_digest,
                                     capacity, load_experiment, save_experiment)


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True)+"\n")


def checkpoint_check(w, path, steps=32):
    """Main trajectory never advances during this independent fork/replay check."""
    before = w.digest()
    save_experiment(w, path)
    restored = load_experiment(path, w.config)
    assert restored.digest() == before
    reference = ExperimentalWorld.adopt(World.from_state(w.state()), w.config)
    reference.step(steps)
    restored.step(steps)
    after = reference.digest()
    assert restored.digest() == after
    assert w.digest() == before
    return dict(tick=w.tick, continuation_ticks=steps, state_digest=before,
                continuation_digest=after, exact_load=True, exact_replay=True)


def count_event(counter, event):
    counter[event.kind] += 1
    if event.kind == "death":
        counter["cause:"+event.detail["cause"]] += 1


def run(spec):
    folder = Path(spec["out"])
    folder.mkdir(parents=True, exist_ok=False)
    dump(folder / "spec.json", spec)
    cfg = Config(spec.get("slots",60), spec.get("memory","enabled"))
    seed, horizon = spec["seed"], spec["ticks"]
    job_start = time.perf_counter()
    with capacity(cfg.slots):
        if spec.get("resume"):
            resume_path=Path(spec["resume"])
            if resume_path.with_suffix(".config.json").exists():
                w=load_experiment(resume_path,cfg)
            else:
                assert cfg==Config(), "Unconfigured historical prefix must be the original enabled 60-slot baseline"
                w=ExperimentalWorld.adopt(load(resume_path),cfg)
            old_summary = json.loads(Path(spec["resume"]).with_name("summary.json").read_text())
            assert w.digest() == old_summary["final_digest"]
        else:
            w = ExperimentalWorld(seed,cfg)
        assert w.seed == seed and w.tick < horizon
        initial_digest, initial_biology = w.digest(), biological_digest(w)
        start_tick = w.tick
        initial_events = Counter(e.kind for e in w.events)
        event_index = len(w.events)
        living = len(w.living())
        births, deaths = len(w.agents), len(w.agents)-living
        totals, interval = Counter(), Counter()
        rows, checkpoint_results = [], []
        min_population, max_population = living,living
        step_wall = step_cpu = checkpoint_seconds = 0.0
        interval_start = time.perf_counter()

        def sample():
            alive = w.living()
            n = len(alive)
            return dict(seed=seed, memory=cfg.memory, slots=cfg.slots, tick=w.tick,
                        living=n, births_total=births, deaths_total=deaths,
                        births_interval=interval["birth"], deaths_interval=interval["death"],
                        agent_ticks=interval["agent_ticks"], decisions=interval["decisions"],
                        eligible_agent_ticks=interval["eligible"], retained_slot_ticks=interval["retained"],
                        capacity_slot_ticks=interval["capacity"], scheduler_seconds=interval["scheduler_ns"]/1e9,
                        food_consumed=interval["food_consumed"], hazards=interval["hazard"],
                        starvation_deaths=interval["cause:starvation"], social=interval["social"],
                        sleep_events=interval["sleep"], wake_events=interval["wake"],
                        sleeping_end=sum(a.sleep_until>w.tick for a in alive),
                        eligible_at_schedule=w.eligible if w.tick>start_tick else None,
                        food_stock=sum(c.food for row in w.cells for c in row),
                        forage_cells=sum(c.food>=10 for row in w.cells for c in row),
                        hunger_over_100=sum(a.hunger>100 for a in alive),
                        thirst_over_100=sum(a.thirst>100 for a in alive),
                        mean_hunger=sum(a.hunger for a in alive)/n if n else None,
                        mean_thirst=sum(a.thirst for a in alive)/n if n else None,
                        max_generation=max(w.generations.values()),
                        mean_alive_generation=sum(w.generations[a.id] for a in alive)/n if n else None)

        rows.append(sample())
        block_wall, block_cpu = time.perf_counter(), time.process_time()
        previous_scheduler = previous_food = 0
        for tick in range(start_tick+1,horizon+1):
            before_population = living
            w.step()
            for e in w.events[event_index:]:
                for c in (totals,interval):
                    count_event(c,e)
                if e.kind == "birth":
                    living += 1
                    births += 1
                elif e.kind == "death":
                    living -= 1
                    deaths += 1
            event_index = len(w.events)
            retained = sum(i is not None for i in w.slots)
            scheduler = w.measured["scheduler_ns"]
            food = w.measured["food_consumed"]
            for c in (totals,interval):
                c["agent_ticks"] += before_population
                c["decisions"] += w.assigned
                c["eligible"] += w.eligible
                c["retained"] += retained
                c["capacity"] += cfg.slots
                c["scheduler_ns"] += scheduler-previous_scheduler
                c["food_consumed"] += food-previous_food
            previous_scheduler, previous_food = scheduler, food
            min_population, max_population = min(min_population,living),max(max_population,living)
            if tick % spec.get("sample",100) == 0 or tick == horizon:
                rows.append(sample())
                interval.clear()
            if tick % 5000 == 0:
                print(f"{folder.name}: tick={tick} living={living} born={births}",flush=True)
                # Small progress file makes unattended runs observable without parsing memory.
                dump(folder / "progress.json",dict(tick=tick,living=living,born=births))
            if tick in spec.get("checkpoints",[]):
                step_wall += time.perf_counter()-block_wall
                step_cpu += time.process_time()-block_cpu
                t=time.perf_counter()
                check=checkpoint_check(w,folder/f"checkpoint-{tick}.sqlite")
                checkpoint_results.append(check)
                checkpoint_seconds += time.perf_counter()-t
                dump(folder / "checkpoint-checks.json", checkpoint_results)
                write_csv(folder/"population.partial.csv", rows)
                block_wall,block_cpu=time.perf_counter(),time.process_time()
        step_wall += time.perf_counter()-block_wall
        step_cpu += time.process_time()-block_cpu
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
        w.validate()
        assert living == len(w.living()) == births-deaths
        agent_rows=[]
        for a in w.agents.values():
            end=a.died if a.died is not None else horizon
            m=w.metrics[a.id]
            agent_rows.append(dict(seed=seed,memory=cfg.memory,slots=cfg.slots,agent=a.id,
                                   founder=int(not a.parents),born_tick=a.born,end_tick=end,
                                   parent1=a.parents[0] if a.parents else None,parent2=a.parents[1] if a.parents else None,
                                   initial_age=w.initial_ages.get(a.id,0),age_ticks=a.age,
                                   observed_ticks=end-a.born,died=int(not a.alive),
                                   death_cause=a.death_cause or "",generation=w.generations[a.id],
                                   children=a.children,**a.traits,
                                   **{k:m[k] for k in ("decisions","move","eat","drink","sleep","socialize","reproduce","wait","novel_moves","hazard_entries")}))
        assert sum(a["decisions"] for a in agent_rows) == totals["decisions"]
        assert sum(a["hazard_entries"] for a in agent_rows) == totals["hazard"]
        write_csv(folder/"population.csv", rows)
        write_csv(folder/"agents.csv", agent_rows)
        events=Counter(e.kind for e in w.events)
        causes=Counter(a.death_cause for a in w.agents.values() if not a.alive)
        # Complete newborn cohort, including early deaths; no decision-count filter.
        complete=[a for a in w.agents.values() if a.parents and a.born <= horizon-3000]
        assert all(not a.alive for a in complete)
        digest=w.digest()
        outcome=dict(seed=seed,memory=cfg.memory,slots=cfg.slots,start_tick=start_tick,ticks=horizon,
                     initial_digest=initial_digest,initial_biological_digest=initial_biology,final_digest=digest,
                     final_population=living,total_births=births,offspring=births-60,deaths=deaths,
                     death_causes=dict(causes),events=dict(events),extension_counters=dict(totals),
                     reused_prefix_events=dict(initial_events) if start_tick else {},
                     min_measured_population=min_population,max_measured_population=max_population,
                     max_generation=max(w.generations.values()),
                     complete_cohort_n=len(complete),complete_cohort_mean_age=sum(a.age for a in complete)/len(complete) if complete else None,
                     python=platform.python_version(), config=asdict(cfg))
        performance=dict(loop_wall_seconds=step_wall,loop_cpu_seconds=step_cpu,
                         simulated_ticks=horizon-start_tick,ticks_per_second=(horizon-start_tick)/step_wall,
                         cpu_percent_one_core=100*step_cpu/step_wall,
                         cpu_percent_16_logical=100*step_cpu/step_wall/16,
                         simulation_peak_rss_mib=rss,
                         scheduler_seconds=totals["scheduler_ns"]/1e9,
                         scheduler_fraction_of_loop=totals["scheduler_ns"]/1e9/step_wall,
                         checkpoint_seconds=checkpoint_seconds)
        if not spec.get("no_save",False):
            t=time.perf_counter()
            if spec.get("final_checkpoint_check",False):
                checkpoint_results.append(checkpoint_check(w,folder/"final.sqlite"))
            else:
                save_experiment(w,folder/"final.sqlite")
                restored=load_experiment(folder/"final.sqlite",cfg)
                assert restored.digest()==digest
                del restored
            performance["final_save_verify_seconds"]=time.perf_counter()-t
        if spec.get("replay",False):
            t=time.perf_counter()
            # Enabled replay uses the uninstrumented ORIGINAL World implementation.
            replica=World(seed) if cfg.memory=="enabled" else ExperimentalWorld(seed,cfg)
            replica.step(horizon)
            performance["replay_loop_wall_seconds"]=time.perf_counter()-t
            assert replica.digest()==digest
            outcome["full_replay"]=dict(ticks=horizon,equal=True,digest=digest,
                                         original_uninstrumented=cfg.memory=="enabled")
            del replica
        dump(folder/"checkpoints.json", checkpoint_results)
        dump(folder/"summary.json",outcome)
        performance["job_wall_seconds"]=time.perf_counter()-job_start
        performance["overall_peak_rss_mib"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
        dump(folder/"performance.json",performance)
        print(f"COMPLETE {folder}: living={living} tps={performance['ticks_per_second']:.1f}",flush=True)
        return outcome


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--spec",type=Path)
    parser.add_argument("--out",type=Path)
    parser.add_argument("--seed",type=int,default=11)
    parser.add_argument("--slots",type=int,default=60)
    parser.add_argument("--memory",choices=["enabled","ablated"],default="enabled")
    parser.add_argument("--ticks",type=int,default=1000)
    parser.add_argument("--no-save",action="store_true")
    parser.add_argument("--replay",action="store_true")
    args=parser.parse_args()
    spec=json.loads(args.spec.read_text()) if args.spec else dict(out=str(args.out),seed=args.seed,slots=args.slots,
        memory=args.memory,ticks=args.ticks,no_save=args.no_save,replay=args.replay)
    run(spec)


if __name__ == "__main__":
    main()
