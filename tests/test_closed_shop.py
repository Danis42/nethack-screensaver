from autoascend.agent import reads_closed_shop


def _engraving(text):
    return f'Something is written here in the dust. You read: "{text}".'


def test_intact_sign():
    assert reads_closed_shop(_engraving('Closed for inventory'))


def test_scuffed_signs_from_replays():
    for text in ('C?osed for inventory', 'Closed for ?n?entory', 'C?o?ed for i?ven?ory',
                 '?|o?c  for inv?nt r', '?? ? c  ?   n  n ? v'):
        assert reads_closed_shop(_engraving(text))


def test_other_engravings():
    assert not reads_closed_shop(_engraving('x'))
    assert not reads_closed_shop(_engraving('ad aerarium'))
    assert not reads_closed_shop(_engraving('Vlad was here all day'))
    assert not reads_closed_shop('This door is locked.')
