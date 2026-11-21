from src.data_generator import Measurement, generate
from src.simulator import simulate
from src.network_model import outages


def m(i, t): return Measurement(i,'p',t,70,98,37,False,None)


def test_no_outage_and_conservation():
    readings=[m(i,i*5) for i in range(5)]
    for p in ('P1','P2','P3','P4'):
        r=simulate(readings,[],p,2,1,30)
        assert len(r.delivered)==5 and not r.dropped and not r.pending


def test_overflow_recovery_and_short_outage():
    readings=[m(i,i*5) for i in range(6)]
    for p in ('P1','P2','P3','P4'):
        r=simulate(readings,[(5,20)],p,2,1,50,0)
        assert len(readings)==len(r.delivered)+len(r.dropped)+len(r.pending)
        assert not r.pending
        if p=='P2': assert {x.id for x,_ in r.delivered}=={0,1,2,4,5}
        if p=='P3': assert {x.id for x,_ in r.delivered}=={0,2,3,4,5}


def test_reproducible_generator():
    c={'observation_s':100,'reporting_interval_s':5,'patient_id':'p','episode_conditions':{'low':{'episodes_per_hour':1,'duration_s':[10,30]}}}
    assert generate(c,'low',101,0,0)==generate(c,'low',101,0,0)


def test_pending_boundary_and_repeated_outages():
    readings=[m(i,i*5) for i in range(6)]
    r=simulate(readings,outages(5,30,2),'P2',2,1,30,0)
    assert len(readings)==len(r.delivered)+len(r.dropped)+len(r.pending)
    assert r.pending


def test_reconnection_delay_and_fifo():
    readings=[m(0,0),m(1,5),m(2,10)]
    r=simulate(readings,[(5,12)],'P2',3,1,25,5)
    assert [x.id for x,_ in r.delivered]==[0,1,2]
    assert [t for x,t in r.delivered]==[1,17,18]
