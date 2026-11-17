"""Roles that can administer operations or edit the rollout."""
OPERATIONAL_ADMIN_ROLES = ('admin', 'operator')
ROLLOUT_EDITOR_ROLES = (*OPERATIONAL_ADMIN_ROLES, 'manager')
