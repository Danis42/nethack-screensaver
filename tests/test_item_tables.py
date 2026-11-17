import nle.nethack as nh

from autoascend.item import item_manager as im


def test_object_tables_equal_what_nle_returns_for_every_object():
    for i in range(nh.NUM_OBJECTS):
        assert im._OC_CLASS[i] == ord(nh.objclass(i).oc_class)
        assert im._OC_NAME[i] == nh.objdescr.from_idx(i).oc_name
        assert im._OC_DESCR[i] == nh.objdescr.from_idx(i).oc_descr


def test_parse_name_still_resolves_names_and_appearances():
    objs, glyphs = im.ItemManager.parse_name('long sword')
    assert [o.name for o in objs] == ['long sword'] and glyphs
    objs, _ = im.ItemManager.parse_name('food rations')
    assert [o.name for o in objs] == ['food ration']
