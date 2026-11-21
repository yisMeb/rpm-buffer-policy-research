import math
from src.data_generator import Measurement
from src.simulator import Result
from src.metrics import aoi_stats, calculate


def m(i,t,e=None): return Measurement(i,'p',t,110 if e else 70,98,37,bool(e),e)


def test_aoi_out_of_order_and_hand_calculated():
    assert math.isclose(aoi_stats([(m(0,0),0),(m(1,5),5)],10)['aoi_mean'],2.5)
    x=aoi_stats([(m(1,5),5),(m(0,0),8)],10)
    assert math.isclose(x['aoi_mean'],2.5)
    assert math.isclose(x['aoi_peak'],5)


def test_episode_preservation_and_zero_episodes():
    readings=[m(0,0,1),m(1,5,1),m(2,10,2),m(3,15)]
    r=Result(readings,[(readings[0],0),(readings[3],15)],{1,2},[],[],[],20,0)
    x=calculate(r)
    assert x['episode_preservation']==.5 and x['episodes_lost']==.5
    assert x['episode_fraction']==.25 and x['episode_within_60s']==.5
    y=calculate(Result([readings[3]],[(readings[3],15)],set(),[],[],[],20,0))
    assert math.isnan(y['episode_preservation'])
