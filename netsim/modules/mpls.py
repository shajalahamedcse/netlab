#
# MPLS (LDP/BGP-LU) transformation module
#
import typing

from box import Box

from . import _Module,_routing
from .. import common
from ..common import AF_LIST,BGP_SESSIONS
from .. import data
from ..data.validate import must_be_bool,must_be_list,validate_list_elements
from ..augment import devices

DEFAULT_BGP_LU: dict = {
  'ipv4': [ 'ibgp','ebgp' ],
  'ipv6': [ 'ibgp','ebgp' ]
}

DEFAULT_VPN_AF: dict = {
  'ipv4': [ 'ibgp' ],
  'ipv6': [ 'ibgp' ]
}

DEFAULT_6PE_AF: list = [ 'ibgp' ]

FEATURE_NAME: dict = {
  'ldp': 'LDP-based label distribution',
  'bgp': 'BGP Labeled Unicast',
  'vpn': 'MPLS/VPN',
  '6pe': '6PE (IPv6 transport over LDP)'
}

def node_adjust_ldp(node: Box, topology: Box, features: Box) -> None:
  if not 'ipv4' in node.get('af',{}):
    common.error(
      f'You cannot enable MPLS LDP on node {node.name} without IPv4 address family',
      common.MissingValue,
      'mpls')
    return

  node.ldp = node.mpls.ldp
  node.mpls.pop('ldp',None)
  _routing.router_id(node,'ldp',topology.pools)

  for intf in node.get('interfaces',[]):
    if not 'ipv4' in intf:
      continue                                                    # Cannot run MPLS LDP on non-IPv4 interface
    intf_ldp = data.get_from_box(intf,'mpls.ldp')                 # ... get interface LDP status (if set)
    if 'vrf' in intf:
      if not intf_ldp:                                            # ... VRF LDP must be enabled on individual interfaces (MPLS CSC)
        continue
      if not features.mpls.csc:
        common.error(
          f'Device {node.device} does not support MPLS CsC (LDP in VRF) configured on {node.name}',
          common.IncorrectValue,
          'mpls')
        continue

    if not intf_ldp is None and 'mpls' in intf:
      data.bool_to_defaults(intf.mpls,'ldp')
      if 'ldp' in intf.mpls:
        intf.ldp = intf.mpls.ldp

    if not _routing.external(intf,'ldp'):
      _routing.passive(intf,'ldp')

  _routing.remove_unused_igp(node,'ldp')

def validate_mpls_bgp_parameter(node: Box, feature: str) -> bool:
  if isinstance(node.mpls[feature],list):
    session_list = node.mpls[feature]
    if not validate_list_elements(session_list,BGP_SESSIONS,f'nodes.{node.name}.mpls.{feature}'):
      common.error(
        f'Invalid BGP session type in nodes.{node.name}.mpls.{feature} parameter',
        common.IncorrectValue,
        'mpls')
      return False

    node.mpls[feature] = Box({})
    for af in node.af:
      node.mpls[feature][af] = session_list
  elif isinstance(node.mpls[feature],Box):
    for af in AF_LIST:
      if not af in node.mpls[feature]:
        continue

      if must_be_list(node.mpls[feature],af,f'nodes.{node.name}.mpls.{feature}') is None:
        return False

      if not validate_list_elements(node.mpls[feature][af],BGP_SESSIONS,f'nodes.{node.name}.mpls.{feature}.{af}'):
        common.error(
          f'Invalid BGP session type in nodes.{node.name}.mpls.{feature}.{af} parameter',
          common.IncorrectValue,
          'mpls')
        return False
  else:
    common.error(
      f'nodes.{node.name}.mpls.{feature} parameter must be a boolean, list, or dictionary',
      common.IncorrectValue,
      'mpls')
    return False

  return True

def node_adjust_bgplu(node: Box, topology: Box, features: Box) -> None:
  if not validate_mpls_bgp_parameter(node,'bgp'):
    return

  if not 'neighbors' in node.get('bgp',{}):
    return

  for n in node.bgp.neighbors:
    for af in ['ipv4','ipv6']:
      if af in n and af in node.mpls.bgp and n.type in node.mpls.bgp[af]:
        n[af+'_label'] = True

def node_adjust_6pe(node: Box, topology: Box, features: Box) -> None:
  if not validate_mpls_bgp_parameter(node,'bgp'):
    return

  if not 'ipv4' in node.bgp:
    common.error(
      f'6PE feature used on {node.name} needs IPv4 address family configured within BGP process',
      common.IncorrectValue,
      'mpls')
    return
    
  if 'bgp' in node.mpls and 'ipv6' in node.mpls.bgp:
    common.error(
      f'6PE and IPv6 BGP Labeled Unicast cannot be used at the same time on {node.name}',
      common.IncorrectValue,
      'mpls')
    return    

  if not 'neighbors' in node.get('bgp',{}):
    return

  for n in node.bgp.neighbors:                          # Now iterate over BGP neighbors
    if 'ipv4' in n and n.type in node.mpls['6pe']:      # Do we have an IPv4 session with the neighbor and 6PE enabled?
      n['6pe'] = True                                   # ... enable 6PE AF on IPv4 neighbor session

      # If the neighbor is also using 6PE and will enable 6PE on this session
      # ... then we don't need IPv6 BGP session --> remove it
      #
      if n.type in (data.get_from_box(topology.nodes[n.name],'mpls.6pe') or []):
        n.pop('ipv6',None)

def prune_mplsvpn_af(setting: Box, node: Box) -> None:
  vrf_af :dict = {}

  for af in AF_LIST:
    for vdata in node.get('vrfs',{}).values():
      if af in vdata.af:
        vrf_af[af] = True
        break

  for af in AF_LIST:
    if af in setting and not af in vrf_af and not 'ebgp' in setting[af]:
      setting.pop(af,None)

def node_adjust_mplsvpn(node: Box, topology: Box, features: Box) -> None:
  if not validate_mpls_bgp_parameter(node,'vpn'):
    return

  if not node.bgp.get('rr',False):
    prune_mplsvpn_af(node.mpls.vpn,node)

  for n in node.bgp.neighbors:
    if 'ipv4' in n:
      for af in AF_LIST:
        if af in node.mpls.vpn:
          n['vpn'+af.replace('ip','')] = n.ipv4

class MPLS(_Module):

  def node_pre_transform(self, node: Box, topology: Box) -> None:
    global DEFAULT_BGP_LU
    if not 'mpls' in node:
      return

    data.bool_to_defaults(node.mpls,'ldp',{})
    if 'ldp' in node.mpls:
      must_be_bool(node.mpls.ldp,'disable_unlabeled',f'nodes.{node.name}.mpls.ldp')
      if not any(m in ['ospf','isis','eigrp'] for m in node.module):
        common.error(
          f'You cannot enable LDP on node {node.name} without an IGP',
          common.MissingValue,
          'mpls')

    data.bool_to_defaults(node.mpls,'bgp',DEFAULT_BGP_LU)
    data.bool_to_defaults(node.mpls,'vpn',DEFAULT_VPN_AF)
    data.bool_to_defaults(node.mpls,'6pe',DEFAULT_6PE_AF)
    if 'bgp' in node.mpls or 'vpn' in node.mpls:
      if not 'bgp' in node.module:
        common.error(
          f'You cannot enable BGP-LU or MPLS/VPN on node {node.name} without BGP module',
          common.MissingValue,
          'mpls')

  def node_post_transform(self, node: Box, topology: Box) -> None:
    global FEATURE_NAME

    if not node.mpls:     
      return

    features = devices.get_device_features(node,topology.defaults)

    for fn in FEATURE_NAME.keys():
      if fn in node.mpls and not features.mpls[fn]:
        common.error(
          f'Device {node.device} used by {node.name} does not support {FEATURE_NAME[fn]}',
          common.IncorrectValue,
          'mpls')

    if 'ldp' in node.mpls:
      node_adjust_ldp(node,topology,features)

    if 'bgp' in node.mpls:
      node_adjust_bgplu(node,topology,features)

    if 'vpn' in node.mpls:
      node_adjust_mplsvpn(node,topology,features)

    if '6pe' in node.mpls:
      node_adjust_6pe(node,topology,features)
