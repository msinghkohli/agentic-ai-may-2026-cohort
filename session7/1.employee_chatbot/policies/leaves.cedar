// Cedar authorization policy for leave tools.
//
// An employee may read or apply leaves only on the Leaves resource they own.
// `resource.owner` is set (in authz.py) to the employee_id passed to the tool,
// and `principal` is the authenticated employee from the Session. When they
// differ, no policy permits the action and Cedar returns Deny.
permit(
    principal,
    action in [Action::"ReadLeaves", Action::"InsertLeave"],
    resource
)
when { principal == resource.owner };
