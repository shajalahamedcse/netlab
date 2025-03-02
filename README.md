# Overview

*netlab* is bringing infrastructure-as-code concepts to networking labs. You'll describe your high-level network topology and routing design in a YAML file, and the tools in this repository will

* Create *Vagrantfile* configuration file for *virtualbox* or *libvirt* environment
* Create *containerlab* configuration file
* Create Ansible inventory and configuration file
* Create IPv4 and IPv6 addressing plan and OSPFv2, OSPFv3, EIGRP, IS-IS, and BGP routing design
* Configure IPv4, IPv6, VLANs, VRFs, VXLAN, LLDP, BFD, OSPFv2, OSPFv3, EIGRP, IS-IS, BGP, VRRP, anycast gateways, MPLS, BGP-LU, L3VPN (VPNv4 + VPNv6), 6PE, EVPN, SR-MPLS, or SRv6 on your lab devices.

Instead of wasting time creating lab topology in a GUI and configuring boring details, you'll start with a lab preconfigured according to your specifications.

Interested? [Read the documentation](https://netsim-tools.readthedocs.io/) and [installation guidelines](https://netsim-tools.readthedocs.io/en/latest/install.html).

## Releases

The latest release is [release 1.4.2](https://github.com/ipspace/netlab/releases/tag/release_1.4.2). We refactored several configuration modules and significantly improved topology validation in release 1.4.0, resulting in a number of potentially breaking changes. If you're a long-time _netlab_ user, please read the [release notes](https://netsim-tools.readthedocs.io/en/latest/release.html) first.

The latest release before the changes made in release 1.4.0 is [release 1.3.3](https://github.com/ipspace/netlab/releases/tag/release_1.3.3).

## An overview of tools:

**netlab up**
: Uses **netlab create** to create configuration files, starts the virtual lab, and uses **netlab initial** and **netlab config** to deploy device configurations. [More details](https://netsim-tools.readthedocs.io/en/latest/netlab/up.html) 

**netlab down**
: Destroys the virtual lab. [More details](https://netsim-tools.readthedocs.io/en/latest/netlab/down.html) 

**netlab restart**
: Restart and/or reconfigure the virtual lab. [More details](https://netsim-tools.readthedocs.io/en/latest/netlab/restart.html) 

**netlab create**
: Creates a full-blown network topology, Vagrantfile and Ansible inventory from a simple list of nodes and links. [More details](https://netsim-tools.readthedocs.io/en/latest/netlab/create.html)

**netlab initial**
: Using topology data generated by **netlab create** and default device configuration templates configures common device parameters, protocols that should have been enabled (LLDP, OSPF, IS-IS, BGP, SR-MPLS), enables interfaces, and configures IP addresses on interfaces. [More details](https://netsim-tools.readthedocs.io/en/latest/netlab/initial.html)

**netlab config**
: Applies any Jinja2 configuration templates to network devices.

**netlab collect**
: Using Ansible fact gathering or other device-specific Ansible modules, collects device configurations and saves them in specified directory (default: **config**).

**netlab connect**
: Use SSH or **docker exec** to connect to a lab device using device names, management network IP addresses (**ansible_host**), SSH port, and username/passwords from Ansible inventory. Ideal when you use centralized Vagrant environments and want to connect to the devices while being in playbook development directory.

**netlab show**
: Display system settings in tabular format. [More details](https://netsim-tools.readthedocs.io/en/latest/netlab/show.html)
