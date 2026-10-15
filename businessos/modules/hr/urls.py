from django.urls import path

from . import views

app_name = "hr"
urlpatterns = [
    path("", views.record_list, {"kind": "employee"}, name="employee_list"),
    path("employees/", views.record_list, {"kind": "employee"}, name="employees"),
    path(
        "employees/new/",
        views.record_action,
        {"operation": "create_employee", "kind": "employee"},
        name="employee_create",
    ),
    path(
        "employees/<uuid:record_id>/",
        views.record_detail,
        {"kind": "employee"},
        name="employee_detail",
    ),
    path(
        "employees/<uuid:record_id>/edit/",
        views.record_action,
        {"operation": "update_employee", "kind": "employee"},
        name="employee_edit",
    ),
    path(
        "employees/<uuid:record_id>/end/",
        views.record_action,
        {"operation": "end_employee", "kind": "employee"},
        name="employee_end",
    ),
    path(
        "employees/<uuid:record_id>/transfer/",
        views.record_action,
        {"operation": "transfer_employee_branch", "kind": "employee"},
        name="employee_transfer",
    ),
    path("departments/", views.record_list, {"kind": "department"}, name="department_list"),
    path(
        "departments/new/",
        views.record_action,
        {"operation": "create_department", "kind": "department"},
        name="department_create",
    ),
    path(
        "departments/<uuid:record_id>/",
        views.record_detail,
        {"kind": "department"},
        name="department_detail",
    ),
    path(
        "departments/<uuid:record_id>/edit/",
        views.record_action,
        {"operation": "update_department", "kind": "department"},
        name="department_edit",
    ),
    path("leave-types/", views.record_list, {"kind": "leave_type"}, name="leave_type_list"),
    path(
        "leave-types/new/",
        views.record_action,
        {"operation": "create_leave_type", "kind": "leave_type"},
        name="leave_type_create",
    ),
    path(
        "leave-types/<uuid:record_id>/",
        views.record_detail,
        {"kind": "leave_type"},
        name="leave_type_detail",
    ),
    path(
        "leave-types/<uuid:record_id>/edit/",
        views.record_action,
        {"operation": "update_leave_type", "kind": "leave_type"},
        name="leave_type_edit",
    ),
    path("attendance/", views.record_list, {"kind": "attendance"}, name="attendance_list"),
    path(
        "attendance/new/",
        views.record_action,
        {"operation": "record_attendance", "kind": "attendance"},
        name="attendance_record",
    ),
    path(
        "attendance/<uuid:record_id>/",
        views.record_detail,
        {"kind": "attendance"},
        name="attendance_detail",
    ),
    path(
        "attendance/<uuid:record_id>/correct/",
        views.record_action,
        {
            "operation": "revise_attendance",
            "kind": "attendance",
            "presentation_operation": "CORRECT",
        },
        name="attendance_correct",
    ),
    path(
        "attendance/<uuid:record_id>/void/",
        views.record_action,
        {"operation": "revise_attendance", "kind": "attendance", "presentation_operation": "VOID"},
        name="attendance_void",
    ),
    path(
        "attendance/<uuid:record_id>/reinstate/",
        views.record_action,
        {
            "operation": "revise_attendance",
            "kind": "attendance",
            "presentation_operation": "REINSTATE",
        },
        name="attendance_reinstate",
    ),
    path(
        "attendance/<uuid:attendance_id>/revisions/",
        views.revision_history,
        name="attendance_revisions",
    ),
    path("leave/", views.record_list, {"kind": "leave"}, name="leave_list"),
    path(
        "leave/new/",
        views.record_action,
        {"operation": "create_leave", "kind": "leave"},
        name="leave_create",
    ),
    path("leave/<uuid:record_id>/", views.record_detail, {"kind": "leave"}, name="leave_detail"),
    path(
        "leave/<uuid:record_id>/edit/",
        views.record_action,
        {"operation": "update_leave", "kind": "leave"},
        name="leave_edit",
    ),
    path(
        "leave/<uuid:record_id>/submit/",
        views.record_action,
        {"operation": "submit_leave", "kind": "leave"},
        name="leave_submit",
    ),
    path(
        "leave/<uuid:record_id>/approve/",
        views.record_action,
        {"operation": "decide_leave", "kind": "leave", "presentation_operation": "approve_leave"},
        name="leave_approve",
    ),
    path(
        "leave/<uuid:record_id>/reject/",
        views.record_action,
        {"operation": "decide_leave", "kind": "leave", "presentation_operation": "reject_leave"},
        name="leave_reject",
    ),
    path(
        "leave/<uuid:record_id>/cancel/",
        views.record_action,
        {"operation": "cancel_leave", "kind": "leave"},
        name="leave_cancel",
    ),
]
