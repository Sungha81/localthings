"""Power-source-priority override for the ARTIK051_TVTL-class air purifier
(issue #56 board) only.

Confirmed on this specific board that /power/vs/0 reflects a state change
(physical button, remote, SmartThings cloud, or a local write) BEFORE
/power/0 does, in both directions (On and Off) -- the opposite of
common.py's POWER_GENERIC/POWER_VS_FALLBACK pair, whose priority (OCF
generic href first, vendor href only as a fallback when the generic one is
absent) is still the correct default for the other two board generations
sharing this same by_type/air_purifier.py registry (TP1X_DA-AC-AIR, issue
#130; A-VTWW-TP2-21-COMMON, issue #151) -- neither has been checked for the
same lead/lag behavior, so their power capabilities are deliberately left
exactly as common.py already defines them, not swapped along with TVTL's.

_is_tvtl_board gates every capability below so /power/0 and /power/vs/0
each get exactly one *writable* cap regardless of board generation:
TVTL boards bind the *_TVTL pair (vs/0 primary); every other board
generation binds the *_OTHER pair, which is a byte-for-byte match of
common.py's own POWER_GENERIC/POWER_VS_FALLBACK priority and fields --
duplicated here rather than imported, since _build() requires every cap on
a shared href to carry its own match_fn once more than one cap targets
that href, and common.py's originals carry none.
"""
from ..capability import Capability
from ..entities import BinarySensorDesc, SwitchDesc
from .common import _power_switch_exists, _power_sensor_exists


def _is_tvtl_board(rep, resources):
    info = resources.get('/information/vs/0', {})
    return 'TVTL' in info.get('x.com.samsung.da.modelNum', '')


def _is_other_board(rep, resources):
    return not _is_tvtl_board(rep, resources)


# --- TVTL boards: /power/vs/0 leads, so it's the writable primary and the
# single source of truth for HA's displayed switch state. -------------------

POWER_VS_TVTL = Capability(
    href='/power/vs/0',
    match_fn=_is_tvtl_board,
    poll_tier='warm',
    entities=(
        SwitchDesc(key='power_switch', field='x.com.samsung.da.power',
                   value_fn=lambda v: v == 'On',
                   exists_fn=_power_switch_exists,
                   write_fn=lambda p, rep, href=None: (
                       ['power', 'vs', '0'],
                       {'x.com.samsung.da.power': 'On' if p == 'On' else 'Off'})),
        BinarySensorDesc(key='power_switch', field='x.com.samsung.da.power',
                         device_class='power',
                         value_fn=lambda v: v == 'On',
                         exists_fn=_power_sensor_exists),
    ),
)

# /power/0 stays bound as a read-only diagnostic mirror on TVTL boards, so
# discover() doesn't flag it unbound -- POWER_VS_TVTL above is the only
# writable power entity on this board generation. Two writable SwitchDescs
# sharing key='power_switch' on different hrefs would leave HA's displayed
# switch state depending on entity-registration order, not on which href
# is actually current.
POWER_GENERIC_TVTL_MIRROR = Capability(
    href='/power/0',
    match_fn=_is_tvtl_board,
    poll_tier='warm',
    entities=(
        BinarySensorDesc(key='power_switch_generic', field='value',
                         device_class='power',
                         icon='mdi:power-plug-outline',
                         entity_category='diagnostic',
                         value_fn=lambda v: bool(v)),
    ),
)

# --- Every other board generation on this registry (TP1X, A-VTWW): exact
# copy of common.py's POWER_GENERIC/POWER_VS_FALLBACK priority and fields,
# just with _is_other_board added so _build() accepts two caps per href. ---

POWER_GENERIC_OTHER = Capability(
    href='/power/0',
    match_fn=_is_other_board,
    entities=(
        SwitchDesc(key='power_switch', field='value',
                   value_fn=lambda v: bool(v),
                   exists_fn=_power_switch_exists,
                   write_fn=lambda p, rep, href=None: (
                       ['power', '0'], {'value': p == 'On'})),
        BinarySensorDesc(key='power_switch', field='value',
                         device_class='power',
                         value_fn=lambda v: bool(v),
                         exists_fn=_power_sensor_exists),
    ),
)

POWER_VS_OTHER = Capability(
    href='/power/vs/0',
    match_fn=lambda rep, resources: (
        _is_other_board(rep, resources) and '/power/0' not in resources
    ),
    entities=(
        SwitchDesc(key='power_switch', field='x.com.samsung.da.power',
                   value_fn=lambda v: v == 'On',
                   exists_fn=_power_switch_exists,
                   write_fn=lambda p, rep, href=None: (
                       ['power', 'vs', '0'],
                       {'x.com.samsung.da.power': 'On' if p == 'On' else 'Off'})),
        BinarySensorDesc(key='power_switch', field='x.com.samsung.da.power',
                         device_class='power',
                         value_fn=lambda v: v == 'On',
                         exists_fn=_power_sensor_exists),
    ),
)
