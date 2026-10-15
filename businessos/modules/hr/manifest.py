VIEW_EMPLOYEES = "hr.employee.view"
MANAGE_EMPLOYEES = "hr.employee.manage"
VIEW_DEPARTMENTS = "hr.department.view"
MANAGE_DEPARTMENTS = "hr.department.manage"
VIEW_ATTENDANCE = "hr.attendance.view"
RECORD_ATTENDANCE = "hr.attendance.record"
CORRECT_ATTENDANCE = "hr.attendance.correct"
VIEW_LEAVE = "hr.leave.view"
REQUEST_LEAVE = "hr.leave.request"
APPROVE_LEAVE = "hr.leave.approve"
CANCEL_LEAVE = "hr.leave.cancel"
MANAGE_LEAVE_TYPES = "hr.leave_type.manage"

HR_PERMISSION_DECLARATIONS = (
    (VIEW_EMPLOYEES, "View employees"),
    (MANAGE_EMPLOYEES, "Manage employees"),
    (VIEW_DEPARTMENTS, "View departments"),
    (MANAGE_DEPARTMENTS, "Manage departments"),
    (VIEW_ATTENDANCE, "View attendance"),
    (RECORD_ATTENDANCE, "Record attendance"),
    (CORRECT_ATTENDANCE, "Correct attendance"),
    (VIEW_LEAVE, "View leave"),
    (REQUEST_LEAVE, "Request leave"),
    (APPROVE_LEAVE, "Approve or reject leave"),
    (CANCEL_LEAVE, "Cancel leave"),
    (MANAGE_LEAVE_TYPES, "Manage leave types"),
)

MODULE = {
    "code": "hr",
    "name": "Human Resources",
    "version": "0.1.0",
    "depends": ["party", "organization", "reference", "access"],
    "permissions": [code for code, _ in HR_PERMISSION_DECLARATIONS],
}
