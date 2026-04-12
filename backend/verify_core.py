#!/usr/bin/env python3
"""Smoke-test core PPA APIs via Flask test client. Run: python verify_core.py"""
import json
import sys

from app import create_app


def j(resp):
    if resp.content_type and "json" in resp.content_type:
        return resp.get_json(silent=True) or {}
    return {}


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def main():
    app = create_app()
    client = app.test_client()
    failed = []

    def check(name, cond, detail=""):
        ok = bool(cond)
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            failed.append(name)

    print("=== Placement Portal core verification ===\n")

    # --- Public / index ---
    r = client.get("/")
    check("GET / serves SPA", r.status_code == 200, r.status_code)

    # --- Admin ---
    r = client.post(
        "/api/auth/login",
        data=json.dumps({"email": "ashuathu93@gmail.com", "password": "admin123"}),
        content_type="application/json",
    )
    admin_t = j(r).get("token")
    check("Admin login", r.status_code == 200 and admin_t, r.status_code)
    h = auth_headers(admin_t)

    r = client.get("/api/admin/dashboard", headers=h)
    d = j(r)
    check(
        "Admin dashboard metrics",
        r.status_code == 200 and "total_students" in d and "total_drives" in d,
        d if r.status_code != 200 else "",
    )

    r = client.get("/api/admin/companies?search=Google", headers=h)
    check("Admin search companies", r.status_code == 200 and isinstance(j(r), list), r.status_code)

    r = client.get("/api/admin/drives", headers=h)
    check("Admin list drives", r.status_code == 200 and isinstance(j(r), list), r.status_code)

    r = client.get("/api/admin/students?search=Alex", headers=h)
    check("Admin search students", r.status_code == 200 and isinstance(j(r), list), r.status_code)

    r = client.get("/api/admin/applications", headers=h)
    check("Admin all applications", r.status_code == 200 and isinstance(j(r), list), r.status_code)

    r = client.get("/api/admin/stats", headers=h)
    check("Admin stats / reports API", r.status_code == 200 and "status_counts" in j(r), r.status_code)

    # --- Student ---
    r = client.post(
        "/api/auth/login",
        data=json.dumps({"email": "a@a.com", "password": "123456"}),
        content_type="application/json",
    )
    st_t = j(r).get("token")
    check("Student login", r.status_code == 200 and st_t, r.status_code)
    sh = auth_headers(st_t)

    r = client.get("/api/student/dashboard", headers=sh)
    check("Student dashboard", r.status_code == 200 and "total_applications" in j(r), r.status_code)

    r = client.get("/api/student/drives", headers=sh)
    drives = j(r)
    check(
        "Student eligible drives list",
        r.status_code == 200 and isinstance(drives, list) and len(drives) > 0,
        f"count={len(drives) if isinstance(drives, list) else 'n/a'}",
    )

    r = client.get("/api/student/companies?search=Info", headers=sh)
    cos = j(r)
    check(
        "Student company browse/search",
        r.status_code == 200 and isinstance(cos, list) and len(cos) >= 1,
        f"count={len(cos) if isinstance(cos, list) else 'n/a'}",
    )

    r = client.get("/api/student/applications", headers=sh)
    apps = j(r)
    check("Student applications history", r.status_code == 200 and isinstance(apps, list), r.status_code)

    # Apply: first drive that is eligible for this student and not yet applied
    applied_ids = {a["drive_id"] for a in apps} if isinstance(apps, list) else set()
    to_apply = next(
        (
            d["id"]
            for d in drives
            if d["id"] not in applied_ids and d.get("eligible") is not False
        ),
        None,
    )
    if to_apply:
        r = client.post(f"/api/student/drives/{to_apply}/apply", headers=sh)
        check(
            "Student apply to drive",
            r.status_code in (201, 409),
            f"status={r.status_code} body={j(r)}",
        )
    else:
        check(
            "Student apply (skipped: no eligible open drive to try)",
            True,
            "",
        )

    r = client.get("/api/student/applications", headers=sh)
    apps_after = j(r) if r.status_code == 200 else []
    dup_id = apps_after[0]["drive_id"] if apps_after else None
    if dup_id:
        r = client.post(f"/api/student/drives/{dup_id}/apply", headers=sh)
        check("Duplicate apply rejected (409)", r.status_code == 409, r.status_code)
    else:
        check("Duplicate apply (skipped: no applications)", False, "no drive_id")

    r = client.post("/api/student/export", headers=sh)
    ex = j(r)
    sync_ok = r.status_code == 200 and "csv_data" in ex and "Student ID" in ex.get("csv_data", "")
    async_ok = r.status_code == 202 and ex.get("task_id")
    check(
        "Student CSV export (sync or async)",
        sync_ok or async_ok,
        f"status={r.status_code} keys={list(ex.keys())}",
    )

    r = client.get("/api/student/profile", headers=sh)
    check("Student profile", r.status_code == 200 and j(r).get("name"), r.status_code)

    # --- Company ---
    r = client.post(
        "/api/auth/login",
        data=json.dumps({"email": "hr@google.com", "password": "company123"}),
        content_type="application/json",
    )
    co_t = j(r).get("token")
    check("Company login", r.status_code == 200 and co_t, r.status_code)
    ch = auth_headers(co_t)

    r = client.get("/api/company/dashboard", headers=ch)
    cd = j(r)
    check(
        "Company dashboard",
        r.status_code == 200 and "company_name" in cd and "drives" in cd,
        r.status_code,
    )

    r = client.get("/api/company/drives", headers=ch)
    cdr = j(r)
    check("Company drives list", r.status_code == 200 and isinstance(cdr, list) and len(cdr) > 0, r.status_code)

    first_drive_id = cdr[0]["id"] if cdr else None
    if first_drive_id:
        r = client.get(f"/api/company/drives/{first_drive_id}/applications", headers=ch)
        check(
            "Company view applications",
            r.status_code == 200 and isinstance(j(r), list),
            r.status_code,
        )

    # --- RBAC ---
    r = client.get("/api/admin/dashboard", headers=sh)
    check("Student blocked from admin", r.status_code == 403, r.status_code)

    print("\n=== Summary ===")
    if failed:
        print(f"FAILED ({len(failed)}):", ", ".join(failed))
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
