from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from tenants.models import Tenant
from users.models import User


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────
def make_tenant(name="TestCorp"):
    return Tenant.objects.create(organization_name=name)


def make_user(username, password, tenant, role=User.USER_ROLE, created_by=None):
    user = User.objects.create_user(username=username, password=password)
    user.tenant = tenant
    user.role = role
    user.created_by = created_by
    user.save()
    return user


def auth_client(user):
    """User se authenticated APIClient banao — JWT bypass karke direct auth."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def login_client():
    """Login endpoint test karne ke liye — bina auth ke."""
    return APIClient()


# =============================================================
# 1. LOGIN TESTS
# =============================================================
class LoginTests(TestCase):

    def setUp(self):
        self.tenant = make_tenant()
        self.user = make_user("sagar", "pass1234", self.tenant)

    # Login endpoint ke liye throttle mock karna zaroori hai
    @patch('users.throttles.LoginRateThrottle.get_rate', return_value='100/min')
    def test_valid_login_returns_tokens(self, _):
        """Sahi username + password → 200 + access/refresh token milna chahiye."""
        res = login_client().post(reverse("login"), {
            "username": "sagar", "password": "pass1234"
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    @patch('users.throttles.LoginRateThrottle.get_rate', return_value='100/min')
    def test_wrong_password_returns_401(self, _):
        """Galat password → 401 Unauthorized."""
        res = login_client().post(reverse("login"), {
            "username": "sagar", "password": "wrongpass"
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", res.data)

    @patch('users.throttles.LoginRateThrottle.get_rate', return_value='100/min')
    def test_wrong_username_returns_401(self, _):
        """Exist na karne wala username → 401."""
        res = login_client().post(reverse("login"), {
            "username": "ghost_user", "password": "pass1234"
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('users.throttles.LoginRateThrottle.get_rate', return_value='100/min')
    def test_empty_credentials_returns_400(self, _):
        """Khaali fields → 400."""
        res = login_client().post(reverse("login"), {
            "username": "", "password": ""
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('users.throttles.LoginRateThrottle.get_rate', return_value='100/min')
    def test_missing_password_field_returns_400(self, _):
        """Password field missing → 400."""
        res = login_client().post(reverse("login"), {"username": "sagar"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_without_token_cannot_access_profile(self):
        """Token ke bina profile → 401."""
        res = login_client().get(reverse("profile"))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_user_can_access_profile(self):
        """Authenticated user apna profile dekh sakta hai → 200."""
        res = auth_client(self.user).get(reverse("profile"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["username"], "sagar")

    def test_profile_response_has_role_and_tenant(self):
        """Profile response me role aur tenant dono honge."""
        res = auth_client(self.user).get(reverse("profile"))
        self.assertIn("role", res.data)
        self.assertIn("tenant", res.data)


# =============================================================
# 2. TENANT ISOLATION TESTS
# =============================================================
class TenantIsolationTests(TestCase):

    def setUp(self):
        self.tenant_a = make_tenant("CompanyA")
        self.admin_a  = make_user("admin_a", "pass1234", self.tenant_a, role=User.ADMIN)
        self.user_a   = make_user("user_a",  "pass1234", self.tenant_a, created_by=self.admin_a)

        self.tenant_b = make_tenant("CompanyB")
        self.admin_b  = make_user("admin_b", "pass1234", self.tenant_b, role=User.ADMIN)
        self.user_b   = make_user("user_b",  "pass1234", self.tenant_b, created_by=self.admin_b)

    def test_admin_a_sees_only_own_tenant_users(self):
        """Admin A ke list me sirf Tenant A ke users honge."""
        res = auth_client(self.admin_a).get(reverse("user-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        usernames = [u["username"] for u in res.data["results"]]
        self.assertIn("user_a", usernames)
        self.assertNotIn("user_b", usernames)

    def test_admin_b_sees_only_own_tenant_users(self):
        """Admin B ke list me sirf Tenant B ke users honge."""
        res = auth_client(self.admin_b).get(reverse("user-list"))
        usernames = [u["username"] for u in res.data["results"]]
        self.assertIn("user_b", usernames)
        self.assertNotIn("user_a", usernames)

    def test_admin_a_cannot_change_role_of_tenant_b_user(self):
        """Admin A, Tenant B ke user ka role nahi badal sakta → 404."""
        res = auth_client(self.admin_a).post(
            reverse("change-role", kwargs={"user_id": self.user_b.id}),
            {"role": "MANAGER"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_b_cannot_change_role_of_tenant_a_user(self):
        """Admin B bhi cross-tenant role change nahi kar sakta → 404."""
        res = auth_client(self.admin_b).post(
            reverse("change-role", kwargs={"user_id": self.user_a.id}),
            {"role": "MANAGER"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_bulk_delete_only_affects_own_tenant(self):
        """Bulk delete me dusre tenant ke IDs daalne pe unhe delete nahi karega."""
        res = auth_client(self.admin_a).post(
            reverse("bulk-delete"),
            {"user_ids": [self.user_b.id]}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user_b.refresh_from_db()
        self.assertTrue(self.user_b.is_active)
        self.assertEqual(res.data["deleted"], [])

    def test_bulk_restore_only_affects_own_tenant(self):
        """Bulk restore bhi cross-tenant kaam nahi karega."""
        self.user_b.is_active = False
        self.user_b.save()
        res = auth_client(self.admin_a).post(
            reverse("bulk-restore"),
            {"user_ids": [self.user_b.id]}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user_b.refresh_from_db()
        self.assertFalse(self.user_b.is_active)
        self.assertEqual(res.data["restored"], [])

    def test_admin_a_cannot_restore_tenant_b_user(self):
        """Admin A, Tenant B ke deleted user ko restore nahi kar sakta → 404."""
        self.user_b.is_active = False
        self.user_b.save()
        res = auth_client(self.admin_a).post(
            reverse("restore-user", kwargs={"user_id": self.user_b.id})
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.user_b.refresh_from_db()
        self.assertFalse(self.user_b.is_active)


# =============================================================
# 3. PERMISSION / ROLE TESTS
# =============================================================
class PermissionTests(TestCase):

    def setUp(self):
        self.tenant  = make_tenant()
        self.admin   = make_user("admin",   "pass1234", self.tenant, role=User.ADMIN)
        self.manager = make_user("manager", "pass1234", self.tenant, role=User.MANAGER, created_by=self.admin)
        self.normal  = make_user("normaluser", "pass1234", self.tenant, created_by=self.manager)

    def test_admin_can_register_new_user(self):
        res = auth_client(self.admin).post(
            reverse("register"), {"username": "newuser", "password": "pass1234"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_manager_can_register_new_user(self):
        res = auth_client(self.manager).post(
            reverse("register"), {"username": "newuser2", "password": "pass1234"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_normal_user_cannot_register(self):
        """Normal user register nahi kar sakta → 403."""
        res = auth_client(self.normal).post(
            reverse("register"), {"username": "hacker", "password": "pass1234"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_normal_user_cannot_see_user_list(self):
        """Normal user user-list nahi dekh sakta → 403."""
        res = auth_client(self.normal).get(reverse("user-list"))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_sees_only_own_created_users(self):
        """Manager sirf apne banaye users dekhega."""
        make_user("admin_user", "pass1234", self.tenant, created_by=self.admin)
        res = auth_client(self.manager).get(reverse("user-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        usernames = [u["username"] for u in res.data["results"]]
        self.assertIn("normaluser", usernames)
        self.assertNotIn("admin_user", usernames)

    def test_only_admin_can_change_role(self):
        res = auth_client(self.admin).post(
            reverse("change-role", kwargs={"user_id": self.normal.id}),
            {"role": "MANAGER"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.normal.refresh_from_db()
        self.assertEqual(self.normal.role, "MANAGER")

    def test_manager_cannot_change_role(self):
        """Manager role change nahi kar sakta → 403."""
        res = auth_client(self.manager).post(
            reverse("change-role", kwargs={"user_id": self.normal.id}),
            {"role": "ADMIN"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_normal_user_cannot_change_role(self):
        """Normal user role change nahi kar sakta → 403."""
        res = auth_client(self.normal).post(
            reverse("change-role", kwargs={"user_id": self.manager.id}),
            {"role": "ADMIN"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_change_own_role(self):
        """Admin apna role nahi badal sakta → 400."""
        res = auth_client(self.admin).post(
            reverse("change-role", kwargs={"user_id": self.admin.id}),
            {"role": "USER"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_role_value_returns_400(self):
        """Galat role value → 400."""
        res = auth_client(self.admin).post(
            reverse("change-role", kwargs={"user_id": self.normal.id}),
            {"role": "SUPERADMIN"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_access_dashboard(self):
        res = auth_client(self.admin).get(reverse("dashboard"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("total_users", res.data)
        self.assertIn("active_users", res.data)
        self.assertIn("roles", res.data)

    def test_normal_user_cannot_access_dashboard(self):
        """Normal user dashboard access nahi kar sakta → 403."""
        res = auth_client(self.normal).get(reverse("dashboard"))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


# =============================================================
# 4. USER CRUD TESTS
# =============================================================
class UserCRUDTests(TestCase):

    def setUp(self):
        self.tenant  = make_tenant()
        self.admin   = make_user("admin",   "pass1234", self.tenant, role=User.ADMIN)
        self.manager = make_user("manager", "pass1234", self.tenant, role=User.MANAGER, created_by=self.admin)
        self.normal  = make_user("normaluser", "pass1234", self.tenant, created_by=self.manager)

    def test_admin_can_soft_delete_user(self):
        res = auth_client(self.admin).delete(
            reverse("user-detail", kwargs={"user_id": self.normal.id})
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.normal.refresh_from_db()
        self.assertFalse(self.normal.is_active)

    def test_admin_cannot_delete_themselves(self):
        """Admin apne aap ko delete nahi kar sakta → 400."""
        res = auth_client(self.admin).delete(
            reverse("user-detail", kwargs={"user_id": self.admin.id})
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deleting_already_deleted_user_returns_400(self):
        """Pehle se deleted user ko dobara delete → 400."""
        self.normal.is_active = False
        self.normal.save()
        res = auth_client(self.admin).delete(
            reverse("user-detail", kwargs={"user_id": self.normal.id})
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_restore_deleted_user(self):
        self.normal.is_active = False
        self.normal.save()
        res = auth_client(self.admin).post(
            reverse("restore-user", kwargs={"user_id": self.normal.id})
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.normal.refresh_from_db()
        self.assertTrue(self.normal.is_active)

    def test_restoring_active_user_returns_400(self):
        """Pehle se active user ko restore → 400."""
        res = auth_client(self.admin).post(
            reverse("restore-user", kwargs={"user_id": self.normal.id})
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manager_can_only_restore_own_users(self):
        """Manager sirf apne banaye users ko restore kar sakta hai."""
        admin_user = make_user("admin_user", "pass1234", self.tenant, created_by=self.admin)
        admin_user.is_active = False
        admin_user.save()
        res = auth_client(self.manager).post(
            reverse("restore-user", kwargs={"user_id": admin_user.id})
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_update_own_username(self):
        res = auth_client(self.normal).patch(
            reverse("user-detail", kwargs={"user_id": self.normal.id}),
            {"username": "updateduser"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.normal.refresh_from_db()
        self.assertEqual(self.normal.username, "updateduser")

    def test_duplicate_username_update_returns_400(self):
        """Existing username se update → 400."""
        res = auth_client(self.admin).patch(
            reverse("user-detail", kwargs={"user_id": self.admin.id}),
            {"username": "manager"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_username_update_returns_400(self):
        """Khaali username se update → 400."""
        res = auth_client(self.normal).patch(
            reverse("user-detail", kwargs={"user_id": self.normal.id}),
            {"username": ""}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_username_register_returns_400(self):
        """Same username se register → 400 (not 500 crash)."""
        res = auth_client(self.admin).post(
            reverse("register"),
            {"username": "normaluser", "password": "pass1234"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_delete_works_correctly(self):
        extra1 = make_user("extra1", "pass1234", self.tenant, created_by=self.admin)
        extra2 = make_user("extra2", "pass1234", self.tenant, created_by=self.admin)
        res = auth_client(self.admin).post(
            reverse("bulk-delete"),
            {"user_ids": [extra1.id, extra2.id]}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        extra1.refresh_from_db(); extra2.refresh_from_db()
        self.assertFalse(extra1.is_active)
        self.assertFalse(extra2.is_active)

    def test_bulk_delete_skips_already_deleted(self):
        """Pehle se deleted user bulk delete me skip hoga."""
        extra = make_user("extra", "pass1234", self.tenant, created_by=self.admin)
        extra.is_active = False
        extra.save()
        res = auth_client(self.admin).post(
            reverse("bulk-delete"), {"user_ids": [extra.id]}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["deleted"], [])
        self.assertIn("extra", [s["username"] for s in res.data["skipped"]])

    def test_bulk_restore_works_correctly(self):
        r1 = make_user("r1", "pass1234", self.tenant, created_by=self.admin)
        r2 = make_user("r2", "pass1234", self.tenant, created_by=self.admin)
        r1.is_active = False; r1.save()
        r2.is_active = False; r2.save()
        res = auth_client(self.admin).post(
            reverse("bulk-restore"),
            {"user_ids": [r1.id, r2.id]}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        r1.refresh_from_db(); r2.refresh_from_db()
        self.assertTrue(r1.is_active)
        self.assertTrue(r2.is_active)
