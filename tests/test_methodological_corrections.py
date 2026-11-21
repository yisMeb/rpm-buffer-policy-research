import math
from src.data_generator import Episode, Measurement, SyntheticReadings, generate
from src.metrics import calculate
from src.simulator import simulate


def m(i,t,abnormal=False,ids=()):
    return Measurement(i,'p',t,110 if abnormal else 70,98,37,abnormal,ids[0] if ids else None,ids)


def test_occupancy_is_independent_of_logging():
    readings=[m(i,i*5) for i in range(5)]
    for policy in ('P1','P2','P3','P4'):
        a=simulate(readings,[(5,25)],policy,2,1,35,0,False)
        b=simulate(readings,[(5,25)],policy,2,1,35,0,True)
        assert a.occupancy==b.occupancy
        assert calculate(a)['occupancy_peak']==(1 if policy=='P1' else 2)
        assert calculate(a)['occupancy_mean']==calculate(b)['occupancy_mean']
        assert not a.events and b.events


def test_p1_uses_same_service_slots_as_buffered_policies():
    readings=[m(0,0),m(1,5)]
    a=simulate(readings,[],'P1',2,1,10)
    b=simulate(readings,[],'P2',2,1,10)
    assert [(x.id,t) for x,t in a.delivered]==[(x.id,t) for x,t in b.delivered]==[(0,1),(1,6)]
    assert calculate(a,aoi_end=10)['aoi_mean']==calculate(b,aoi_end=10)['aoi_mean']


def test_overlap_and_threshold_miss_keep_both_truth_episodes():
    readings=SyntheticReadings([m(0,5,False,(1,2)),m(1,10,True,(1,2))],
                               [Episode(1,4,12,0),Episode(2,5,15,1)])
    r=simulate(readings,[],'P2',2,1,20)
    x=calculate(r,aoi_end=20)
    assert x['episode_count']==2
    assert x['episode_threshold_detected_count']==2
    assert x['episode_preservation']==1
    assert math.isclose(x['episode_delay'],1.5)
    missed=SyntheticReadings([m(0,5,False,(1,2))],readings.episodes)
    y=calculate(simulate(missed,[],'P2',2,1,20))
    assert y['episode_count']==2 and y['episode_threshold_detected_count']==0
    assert y['episode_preservation']==1


def test_loss_types_and_pending_are_disjoint():
    readings=[m(i,i*5) for i in range(5)]
    p1=simulate(readings,[(5,20)],'P1',2,1,30,0)
    assert len(p1.network_losses)==3 and not p1.overflow_losses
    p2=simulate(readings,[(5,20)],'P2',2,1,30,0)
    assert len(p2.overflow_losses)==1 and not p2.network_losses
    assert calculate(p2)['total_losses']==len(p2.dropped)+len(p2.pending)
    short=simulate(readings,[(5,50)],'P2',2,1,25,0)
    assert len(short.pending)==2 and calculate(short)['total_losses']==4
    contention=simulate([m(0,0),m(1,5)],[],'P1',1,.1,12,0)
    assert contention.no_buffer_losses=={1} and not contention.network_losses


def test_backlog_recovery_boundaries():
    trace=[(5,10)]
    one=simulate([m(0,5)],trace,'P2',3,1,12,0)
    two=simulate([m(0,5),m(1,6)],trace,'P2',3,1,12,0)
    pending=simulate([m(0,5),m(1,6)],trace,'P2',3,1,10,0)
    empty=simulate([m(0,0)],trace,'P2',3,1,12,0)
    assert one.recovery_time==0
    assert two.recovery_time==1
    assert pending.recovery_time is None
    assert empty.recovery_time==0


def test_alternative_generators_are_deterministic_and_account_for_overlap():
    c={'observation_s':120,'reporting_interval_s':5,'patient_id':'p',
       'episode_conditions':{'low':{'episodes_per_hour':120,'duration_s':[60,90]}}}
    for model in ('poisson_uniform','fixed_uniform','clustered_long'):
        a=generate(c,'low',101,0,0,model)
        b=generate(c,'low',101,0,0,model)
        assert a==b and a.episodes==b.episodes
        assert {i for r in a for i in r.episode_ids}<={e.id for e in a.episodes}
        assert calculate(simulate(a,[],'P2',120,1,180))['episode_count']==len(a.episodes)


def test_deadline_rates_include_every_ground_truth_episode():
    readings=SyntheticReadings([m(0,10,False,(1,))],
                               [Episode(1,0,20,0),Episode(2,1,4,1)])
    r=simulate(readings,[(0,200)],'P2',2,1,220,0)
    x=calculate(r,(60,300,900),20)
    assert x['episode_count']==2 and x['episode_preservation']==.5
    assert x['episode_within_60s']==0
    assert x['episode_within_300s']==.5
    assert x['episode_within_900s']==.5


def test_p1_drops_if_connection_fails_before_shared_slot():
    r=simulate([m(0,0)],[(.5,5)],'P1',1,1,6,0)
    assert not r.delivered and r.network_losses=={0}
