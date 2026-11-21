from src.buffer_policies import admit
from src.data_generator import Measurement


def m(i, abnormal=False): return Measurement(i, 'p', i, 70, 98, 37, abnormal, i if abnormal else None)


def test_drop_newest_and_oldest():
    q=[m(0),m(1)]
    assert admit(q,m(2),2,'P2')==(False,None)
    assert [x.id for x in q]==[0,1]
    assert admit(q,m(2),2,'P3')==(True,m(0))
    assert [x.id for x in q]==[1,2]


def test_event_aware_all_abnormal():
    q=[m(0,True),m(1),m(2,True)]
    assert admit(q,m(3,True),3,'P4')==(True,m(1))
    assert [x.id for x in q]==[0,2,3]
    assert admit(q,m(4),3,'P4')==(False,None)
    assert admit(q,m(5,True),3,'P4')==(True,m(0,True))
