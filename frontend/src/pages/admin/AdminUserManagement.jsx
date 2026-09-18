import React, { useCallback, useEffect, useMemo, useState } from "react";
import { BadgeCheck, Plus, Search, ShieldCheck, UserRound, X } from "lucide-react";

import DashboardLayout from "../../layouts/DashboardLayout";
import {
  createAdministrator,
  getAdminUserDetail,
  getAdminUsers,
} from "../../services/api";
import "../../styles/admin.css";


const roles = ["", "Athlete", "Coach", "Physiotherapist", "Sports Scientist", "Administrator"];
const statuses = ["", "ACTIVE"];
const pageSize = 25;


function formatDate(value) {
  if (!value) return "Not available";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Not available";
  return parsed.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function statusClass(value) {
  return String(value || "active").toLowerCase();
}

function InfoBlock({ label, value }) {
  return (
    <div className="admin-detail-block">
      <span>{label}</span>
      <strong>{value || "Not provided"}</strong>
    </div>
  );
}

function AdminUserManagement() {
  const [filters, setFilters] = useState({ search: "", role: "", account_status: "" });
  const [page, setPage] = useState(0);
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [selectedUser, setSelectedUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [showAddAdmin, setShowAddAdmin] = useState(false);
  const [adminForm, setAdminForm] = useState({ name: "", email: "", password: "", confirm_password: "" });
  const [savingAdmin, setSavingAdmin] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getAdminUsers({
        ...filters,
        limit: pageSize,
        offset: page * pageSize,
      });
      setUsers(Array.isArray(data.users) ? data.users : []);
      setTotal(Number(data.total) || 0);
    } catch (error) {
      setError(error.message || "Failed to load users.");
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    const timeout = setTimeout(loadUsers, 250);
    return () => clearTimeout(timeout);
  }, [loadUsers]);

  const totalPages = Math.max(Math.ceil(total / pageSize), 1);

  const filteredRange = useMemo(() => {
    if (total === 0) return "0 users";
    const start = page * pageSize + 1;
    const end = Math.min((page + 1) * pageSize, total);
    return `${start}-${end} of ${total} users`;
  }, [page, total]);

  function handleFilter(event) {
    const { name, value } = event.target;
    setFilters((current) => ({ ...current, [name]: value }));
    setPage(0);
  }

  async function openUser(userId) {
    setDetailLoading(true);
    setError("");
    try {
      const data = await getAdminUserDetail(userId);
      setSelectedUser(data);
    } catch (error) {
      setError(error.message || "Failed to load user details.");
    } finally {
      setDetailLoading(false);
    }
  }

  function updateAdminForm(event) {
    const { name, value } = event.target;
    setAdminForm((current) => ({ ...current, [name]: value }));
  }

  async function handleCreateAdmin(event) {
    event.preventDefault();
    setSavingAdmin(true);
    setError("");
    setSuccess("");

    if (!adminForm.name.trim() || !adminForm.email.trim() || !adminForm.password || !adminForm.confirm_password) {
      setError("Full name, email, password, and confirmation are required.");
      setSavingAdmin(false);
      return;
    }

    if (adminForm.password !== adminForm.confirm_password) {
      setError("Passwords do not match.");
      setSavingAdmin(false);
      return;
    }

    if (adminForm.password.length < 8) {
      setError("Password must be at least 8 characters.");
      setSavingAdmin(false);
      return;
    }

    try {
      await createAdministrator(adminForm);
      setSuccess("Administrator account created.");
      setShowAddAdmin(false);
      setAdminForm({ name: "", email: "", password: "", confirm_password: "" });
      await loadUsers();
    } catch (error) {
      setError(error.message || "Failed to create administrator.");
    } finally {
      setSavingAdmin(false);
    }
  }

  return (
    <DashboardLayout>
      <main className="admin-page">
        <section className="admin-page-header">
          <div>
            <p className="page-eyebrow">ADMIN</p>
            <h1>User Management</h1>
            <p>Manage platform users, roles, and account status.</p>
          </div>
          <button className="admin-primary-button" type="button" onClick={() => setShowAddAdmin(true)}>
            <Plus size={18} />
            Add Administrator
          </button>
        </section>

        <section className="admin-filter-card">
          <label className="admin-search-field">
            <Search size={17} />
            <input name="search" value={filters.search} onChange={handleFilter} placeholder="Search by name or email" />
          </label>
          <select name="role" value={filters.role} onChange={handleFilter}>
            {roles.map((role) => <option key={role || "ALL"} value={role}>{role || "All roles"}</option>)}
          </select>
          <select name="account_status" value={filters.account_status} onChange={handleFilter}>
            {statuses.map((status) => <option key={status || "ALL"} value={status}>{status || "All statuses"}</option>)}
          </select>
        </section>

        {success && <section className="admin-success-card">{success}</section>}
        {error && <section className="admin-error-card">{error}</section>}
        {detailLoading && <section className="admin-empty-card">Loading user details...</section>}

        <section className="admin-panel-card">
          <div className="admin-panel-heading">
            <div><h2>Users</h2><p>{loading ? "Loading users..." : filteredRange}</p></div>
          </div>

          {loading ? (
            <div className="admin-empty-state">Loading users...</div>
          ) : users.length === 0 ? (
            <div className="admin-empty-state">No users match the current filters.</div>
          ) : (
            <>
              <div className="admin-user-table admin-user-table-head">
                <span>User</span><span>Email</span><span>Role</span><span>Status</span><span>Joined</span><span>Actions</span>
              </div>
              {users.map((user) => (
                <article className="admin-user-table" key={user.user_id}>
                  <div className="admin-user-cell"><div className="admin-icon-box"><UserRound size={18} /></div><strong>{user.name}</strong></div>
                  <span>{user.email}</span>
                  <span>{user.role}</span>
                  <span><span className={`admin-status-pill ${statusClass(user.status)}`}>{user.status}</span></span>
                  <span>{formatDate(user.created_at)}</span>
                  <button className="admin-secondary-button" type="button" onClick={() => openUser(user.user_id)}>View</button>
                </article>
              ))}
            </>
          )}

          <div className="admin-pagination">
            <button className="admin-secondary-button" type="button" disabled={page === 0} onClick={() => setPage((current) => Math.max(current - 1, 0))}>Previous</button>
            <span>Page {page + 1} of {totalPages}</span>
            <button className="admin-secondary-button" type="button" disabled={page + 1 >= totalPages} onClick={() => setPage((current) => current + 1)}>Next</button>
          </div>
        </section>

        {selectedUser && (
          <div className="admin-modal-backdrop">
            <section className="admin-modal">
              <div className="admin-modal-heading">
                <div><p className="page-eyebrow">USER DETAILS</p><h2>{selectedUser.name}</h2><span>{selectedUser.email}</span></div>
                <button className="admin-icon-button" type="button" aria-label="Close user details" onClick={() => setSelectedUser(null)}><X size={20} /></button>
              </div>

              <div className="admin-detail-grid">
                <InfoBlock label="Role" value={selectedUser.role} />
                <InfoBlock label="Account Status" value={selectedUser.status} />
                <InfoBlock label="Joined" value={formatDate(selectedUser.created_at)} />
                <InfoBlock label="Phone" value={selectedUser.phone} />
                <InfoBlock label="Professional Status" value={selectedUser.professional_status} />
              </div>

              {selectedUser.athlete_profile && (
                <div className="admin-detail-section">
                  <h3>Athlete Profile</h3>
                  <div className="admin-detail-grid">
                    <InfoBlock label="Sport" value={selectedUser.athlete_profile.sport} />
                    <InfoBlock label="Position" value={selectedUser.athlete_profile.position} />
                    <InfoBlock label="Age" value={selectedUser.athlete_profile.age} />
                    <InfoBlock label="Training Load" value={selectedUser.athlete_profile.training_load} />
                  </div>
                </div>
              )}

              {selectedUser.professional_profiles?.length > 0 && (
                <div className="admin-detail-section">
                  <h3>Professional Profiles</h3>
                  {selectedUser.professional_profiles.map((profile) => (
                    <div className="admin-profile-row" key={profile.professional_profile_id}>
                      <ShieldCheck size={17} />
                      <div>
                        <strong>{profile.professional_role}</strong>
                        <span>{profile.verification_status} • {profile.organization || profile.primary_sport || "No organization"}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {selectedUser.professional_requests?.length > 0 && (
                <div className="admin-detail-section">
                  <h3>Professional Requests</h3>
                  {selectedUser.professional_requests.map((request) => (
                    <div className="admin-profile-row" key={request.request_id}>
                      <BadgeCheck size={17} />
                      <div>
                        <strong>{request.requested_role}</strong>
                        <span>{request.status} • submitted {formatDate(request.submitted_at)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="admin-empty-state">
                Account activation/deactivation is not supported by the current user model. Professional approval remains managed in Professional Requests.
              </div>
            </section>
          </div>
        )}

        {showAddAdmin && (
          <div className="admin-modal-backdrop">
            <section className="admin-modal">
              <div className="admin-modal-heading">
                <div><p className="page-eyebrow">ADD ADMINISTRATOR</p><h2>Create administrator account</h2></div>
                <button className="admin-icon-button" type="button" aria-label="Close add administrator" onClick={() => setShowAddAdmin(false)}><X size={20} /></button>
              </div>

              <form className="admin-form" onSubmit={handleCreateAdmin}>
                <label><span>Full Name</span><input name="name" value={adminForm.name} onChange={updateAdminForm} required /></label>
                <label><span>Email</span><input name="email" type="email" value={adminForm.email} onChange={updateAdminForm} required /></label>
                <label><span>Password</span><input name="password" type="password" value={adminForm.password} onChange={updateAdminForm} minLength={8} required /></label>
                <label><span>Confirm Password</span><input name="confirm_password" type="password" value={adminForm.confirm_password} onChange={updateAdminForm} minLength={8} required /></label>
                <div className="admin-modal-actions">
                  <button className="admin-secondary-button" type="button" onClick={() => setShowAddAdmin(false)}>Cancel</button>
                  <button className="admin-primary-button" type="submit" disabled={savingAdmin}>{savingAdmin ? "Creating..." : "Create Administrator"}</button>
                </div>
              </form>
            </section>
          </div>
        )}
      </main>
    </DashboardLayout>
  );
}


export default AdminUserManagement;
