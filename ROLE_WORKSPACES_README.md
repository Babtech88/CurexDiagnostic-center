# Curex Role-Based Workspaces

## Login routing
- Main Administrator -> `/dashboard/admin/`
- Sales Manager / Sales Agent -> `/dashboard/sales/`
- Lab Manager / Lab Technician -> `/dashboard/lab/`
- Sample Collection Rider -> `/dashboard/collector/`

All staff still sign in through `/accounts/login/`. Their role automatically sends them to the correct workspace. The Main Admin can create and manage roles from Staff & Roles.

Role visibility is separated in the sidebar. Admin sees the complete operations menu; Sales sees sales tools; Laboratory sees results and incoming samples; Collectors see only assigned collections.
