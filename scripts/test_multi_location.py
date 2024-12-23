from scripts.multi_location import GlobalMultiLocation, parachain_id, RelativeMultiLocation


def test_reanchor_global_pov_should_remain_unchanged():
    initial = GlobalMultiLocation(junctions=[parachain_id(1000)])
    pov = GlobalMultiLocation(junctions=[])
    expected = initial.as_relative()

    result = initial.reanchor(pov)

    assert result == expected


def test_no_common_junctions():
    initial = GlobalMultiLocation(junctions=[parachain_id(1000)])
    pov = GlobalMultiLocation(junctions=[parachain_id(2000)])
    expected = RelativeMultiLocation(parents=1, junctions=[parachain_id(1000)])

    result = initial.reanchor(pov)

    assert result == expected

def test_one_common_junctions():
    initial = GlobalMultiLocation(junctions=[parachain_id(1000), parachain_id(2000)])
    pov = GlobalMultiLocation(junctions=[parachain_id(1000), parachain_id(3000)])
    expected = RelativeMultiLocation(parents=1, junctions=[parachain_id(2000)])

    result = initial.reanchor(pov)

    assert result == expected

def test_all_common_junctions():
    initial = GlobalMultiLocation(junctions=[parachain_id(1000), parachain_id(2000)])
    pov = GlobalMultiLocation(junctions=[parachain_id(1000), parachain_id(2000)])
    expected = RelativeMultiLocation(parents=0, junctions=[])

    result = initial.reanchor(pov)

    assert result == expected

def test_global_to_global():
    initial = GlobalMultiLocation(junctions=[])
    pov = GlobalMultiLocation(junctions=[])
    expected = RelativeMultiLocation(parents=0, junctions=[])

    result = initial.reanchor(pov)

    assert result == expected

# This is "DOT on Relay from PAH pov" test
def test_pov_is_successor():
    initial = GlobalMultiLocation(junctions=[])
    pov = GlobalMultiLocation(junctions=[parachain_id(1000)])
    expected = RelativeMultiLocation(parents=1, junctions=[])

    result = initial.reanchor(pov)

    assert result == expected
