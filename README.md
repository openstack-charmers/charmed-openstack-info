# Charmed OpenStack Info

![Build Badge](https://github.com/openstack-charmers/charmed-openstack-info/actions/workflows/tox.yml/badge.svg)

Provides information about Charmed OpenStack artifacts:

* List of charms per category (see
  [lp-builder-config](./charmed_openstack_info/data/lp-builder-config)).
* Each charm's entry describes holds the following information for machine
  consumption in a yaml file:
  - upstream repository where the code is hosted
  - LP project name
  - [Charmhub](https://charmhub.io) name
  - List of maintained git branches
  - List of Charmhub channels where each git branch will be published to when
    built by LP recipes (e.g. [Charm recipes for OpenStack Nova Cloud
    Controller](https://launchpad.net/charm-nova-cloud-controller/+charm-recipes))

The package comes with a python module (see [loader
module](./charmed_openstack_info/loader.py)) to assist the loading of the yaml
files.

Usage example:

```python
from charmed_openstack_info import loader
fpath = loader.find_file('misc')
gc = loader.load_file(fpath)
for charm in gc.projects():
    print(charm.charmhub_name, charm.repository)
```

```
>>> from charmed_openstack_info import loader
>>> fpath = loader.find_file('misc')
>>> gc = loader.load_file(fpath)
>>> for charm in gc.projects():
...     print(charm.charmhub_name, charm.repository)
...
hacluster https://opendev.org/openstack/charm-hacluster.git
magpie https://opendev.org/openstack/charm-magpie.git
mysql-innodb-cluster https://opendev.org/openstack/charm-mysql-innodb-cluster.git
mysql-router https://opendev.org/openstack/charm-mysql-router.git
percona-cluster https://opendev.org/openstack/charm-percona-cluster.git
rabbitmq-server https://opendev.org/openstack/charm-rabbitmq-server.git
openstack-charmers-next-woodpecker https://github.com/openstack-charmers/charm-woodpecker
vault https://opendev.org/openstack/charm-vault.git
openstack-loadbalancer https://opendev.org/openstack/charm-openstack-loadbalancer.git
```

## Charmhub LP tool

The lp-builder-config can be used with
[charmhub-lp-tool](https://github.com/openstack-charmers/charmhub-lp-tools/)
using the following command:

``` shell
charmhub-lp-tool --config-dir ./charmed_openstack_info/data/lp-builder-config <command>
```
