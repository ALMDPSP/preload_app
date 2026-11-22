"""Read-only rollout consolidation using the same store leadership as the app."""
from dashboard import normalize
from rollout_base import deployed


def organization_rollout(data, records):
    organizations, inventory = records
    groups, stores = {}, []
    for store in data['stores']:
        organization = organizations.get(store['id'], {})
        leadership = {key: organization.get(key) or 'Sem vínculo' for key in ('division', 'ggr', 'gr')}
        key = tuple(normalize(leadership[field]) for field in ('division', 'ggr', 'gr'))
        row = groups.setdefault(key, dict(leadership, stores_expected=0, stores_updated=0,
            stores_complete=0, pdvs_expected=0, pdvs_deployed=0, pdvs_ok=0))
        installed = [machine['pdv'] for machine in store['machines']
                     if deployed(machine, inventory.get((store['id'], machine['pdv'])))]
        ok = sum(bool(machine.get('ok')) for machine in store['machines'])
        complete = bool(store['expected'] and len(installed) == store['expected'])
        row['stores_expected'] += 1
        row['stores_updated'] += bool(installed)
        row['stores_complete'] += complete
        row['pdvs_expected'] += store['expected']
        row['pdvs_deployed'] += len(installed)
        row['pdvs_ok'] += ok
        if installed:
            stores.append(dict(leadership, code=store['code'], name=store['name'],
                expected=store['expected'], installed=installed, ok=ok, complete=complete))
    for row in groups.values():
        row['percent'] = round(row['pdvs_deployed'] / row['pdvs_expected'] * 100, 2) if row['pdvs_expected'] else 0
    return {'groups': [groups[key] for key in sorted(groups)],
            'stores': sorted(stores, key=lambda row: tuple(normalize(row[key]) for key in ('division', 'ggr', 'gr', 'code')))}
