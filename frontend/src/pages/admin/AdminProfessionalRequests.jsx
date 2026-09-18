import React, { useCallback, useEffect, useState } from "react";
import {
  BadgeCheck,
  Clock3,
  ExternalLink,
  Filter,
  Search,
  ShieldCheck,
  XCircle,
} from "lucide-react";

import DashboardLayout from "../../layouts/DashboardLayout";
import {
  approveProfessionalRoleRequest,
  getAdminProfessionalRoleRequest,
  getAdminProfessionalRoleRequests,
  rejectProfessionalRoleRequest,
  resolveApiAssetUrl,
} from "../../services/api";
import "../../styles/professional-role.css";


const statusOptions = ["", "PENDING", "APPROVED", "REJECTED"];
const roleOptions = ["", "COACH", "PHYSIOTHERAPIST", "SPORTS_SCIENTIST"];


function formatRole(value) {
  return String(value || "").replaceAll("_", " ");
}

function roleLabel(value) {
  const role = formatRole(value).toLowerCase();
  return role.charAt(0).toUpperCase() + role.slice(1);
}


function formatDate(value) {
  if (!value) {
    return "Recently";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return "Recently";
  }

  return parsed.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function parseSupportingDocuments(value) {
  if (!value) {
    return [];
  }

  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) {
      return parsed
        .filter((document) => document?.url)
        .map((document) => ({
          label: document.label || "Supporting document",
          url: document.url,
        }));
    }
  } catch {
    return [{ label: "Supporting document", url: value }];
  }

  return [{ label: "Supporting document", url: value }];
}


function AdminProfessionalRequests() {
  const [requests, setRequests] = useState([]);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [requestStatus, setRequestStatus] = useState("");
  const [requestedRole, setRequestedRole] = useState("");
  const [search, setSearch] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState("");
  const supportingDocuments = parseSupportingDocuments(selectedRequest?.supporting_document_url);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadRequests = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getAdminProfessionalRoleRequests({
        requestStatus,
        requestedRole,
        search: search.trim(),
      });
      setRequests(Array.isArray(data) ? data : []);
    } catch (error) {
      setError(error.message || "Failed to load professional requests.");
    } finally {
      setLoading(false);
    }
  }, [requestStatus, requestedRole, search]);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  const handleReview = async (requestId) => {
    setReviewLoading(true);
    setSuccess("");
    setError("");

    try {
      const request = await getAdminProfessionalRoleRequest(requestId);
      setSelectedRequest(request);
      setRejectionReason("");
    } catch (error) {
      setError(error.message || "Failed to open request.");
    } finally {
      setReviewLoading(false);
    }
  };

  const refreshAfterAction = async (message) => {
    setSuccess(message);
    setSelectedRequest(null);
    setRejectionReason("");
    await loadRequests();
  };

  const handleApprove = async () => {
    if (!selectedRequest) {
      return;
    }

    if (!window.confirm(`Approve ${selectedRequest.applicant_name || "this applicant"} as ${roleLabel(selectedRequest.requested_role)}?`)) {
      return;
    }

    setActionLoading("approve");
    setError("");

    try {
      await approveProfessionalRoleRequest(selectedRequest.request_id);
      await refreshAfterAction("Professional request approved.");
    } catch (error) {
      setError(error.message || "Failed to approve request.");
    } finally {
      setActionLoading("");
    }
  };

  const handleReject = async () => {
    if (!selectedRequest) {
      return;
    }

    const reason = rejectionReason.trim();
    if (!reason) {
      setError("Rejection reason is required.");
      return;
    }

    if (!window.confirm(`Reject ${selectedRequest.applicant_name || "this applicant"}'s ${roleLabel(selectedRequest.requested_role)} request?`)) {
      return;
    }

    setActionLoading("reject");
    setError("");

    try {
      await rejectProfessionalRoleRequest(
        selectedRequest.request_id,
        reason
      );
      await refreshAfterAction("Professional request rejected.");
    } catch (error) {
      setError(error.message || "Failed to reject request.");
    } finally {
      setActionLoading("");
    }
  };

  return (
    <DashboardLayout>
      <main className="professional-page admin-professional-page">
        <section className="page-header professional-header-row">
          <div>
            <p className="page-eyebrow">ADMIN VERIFICATION</p>
            <h1>Professional Requests</h1>
            <p>Review professional role applications and activate verified professional accounts.</p>
          </div>

          <div className="admin-filter-group">
            <label>
              <Filter size={16} />
              <select
                value={requestStatus}
                onChange={(event) => setRequestStatus(event.target.value)}
              >
                {statusOptions.map((status) => (
                  <option key={status || "ALL"} value={status}>
                    {status || "ALL"}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <ShieldCheck size={16} />
              <select
                value={requestedRole}
                onChange={(event) => setRequestedRole(event.target.value)}
              >
                {roleOptions.map((role) => (
                  <option key={role || "ALL_ROLES"} value={role}>
                    {role ? formatRole(role) : "ALL ROLES"}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </section>

        <section className="professional-card">
          <div className="professional-toolbar">
            <label className="professional-search">
              <Search size={17} />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search applicant, email, sport, organization, specialization"
              />
            </label>
            {(search || requestStatus || requestedRole) && (
              <button
                className="secondary-button"
                type="button"
                onClick={() => {
                  setSearch("");
                  setRequestStatus("");
                  setRequestedRole("");
                }}
              >
                Clear Filters
              </button>
            )}
          </div>

          {success && <div className="professional-form-success">{success}</div>}
          {error && <div className="professional-form-error">{error}</div>}

          {loading ? (
            <div className="professional-table-empty">Loading requests...</div>
          ) : requests.length === 0 ? (
            <div className="professional-table-empty">
              No professional requests found.
            </div>
          ) : (
            <div className="professional-table-wrap">
              <table className="professional-table">
                <thead>
                  <tr>
                    <th>Applicant</th>
                    <th>Requested Role</th>
                    <th>Sport</th>
                    <th>Experience</th>
                    <th>Submitted</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {requests.map((request) => (
                    <tr key={request.request_id}>
                      <td>
                        <strong>{request.applicant_name || "Applicant"}</strong>
                        <span>{request.applicant_email || request.user_id}</span>
                      </td>
                      <td>{formatRole(request.requested_role)}</td>
                      <td>{request.primary_sport || "Not provided"}</td>
                      <td>
                        {request.years_of_experience !== null &&
                        request.years_of_experience !== undefined
                          ? `${request.years_of_experience} years`
                          : "Not provided"}
                      </td>
                      <td>{formatDate(request.submitted_at)}</td>
                      <td>
                        <span className={`request-status ${request.status.toLowerCase()}`}>
                          {request.status}
                        </span>
                      </td>
                      <td>
                        <button
                          className="secondary-button"
                          disabled={reviewLoading}
                          onClick={() => handleReview(request.request_id)}
                          type="button"
                        >
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {selectedRequest && (
          <div className="professional-modal-backdrop">
            <section className="professional-review-modal">
              <div className="professional-card-header review-header">
                <div>
                  <p className="page-eyebrow">REQUEST REVIEW</p>
                  <h2>{roleLabel(selectedRequest.requested_role)}</h2>
                  <p>Submitted {formatDate(selectedRequest.submitted_at)}</p>
                </div>
                <span className={`request-status ${selectedRequest.status.toLowerCase()}`}>
                  {selectedRequest.status}
                </span>
              </div>

              <div className="review-detail-grid">
                <div>
                  <span>Applicant</span>
                  <strong>{selectedRequest.applicant_name || "Applicant"}</strong>
                </div>
                <div>
                  <span>Email</span>
                  <strong>{selectedRequest.applicant_email || "Not provided"}</strong>
                </div>
                <div>
                  <span>Requested Role</span>
                  <strong>{roleLabel(selectedRequest.requested_role)}</strong>
                </div>
                <div>
                  <span>Phone</span>
                  <strong>{selectedRequest.applicant_phone || "Not provided"}</strong>
                </div>
                <div>
                  <span>Sport / Interested Sports</span>
                  <strong>{selectedRequest.primary_sport || "Not provided"}</strong>
                </div>
                <div>
                  <span>Experience</span>
                  <strong>
                    {selectedRequest.years_of_experience !== null &&
                    selectedRequest.years_of_experience !== undefined
                      ? `${selectedRequest.years_of_experience} years`
                      : "Not provided"}
                  </strong>
                </div>
                <div>
                  <span>Organization / Institution</span>
                  <strong>{selectedRequest.organization || "Not provided"}</strong>
                </div>
              </div>

              <div className="review-copy-block">
                <span>Specialization</span>
                <p>{selectedRequest.specialization || "Not provided"}</p>
              </div>

              {selectedRequest.requested_role === "SPORTS_SCIENTIST" && (
                <div className="review-copy-block">
                  <span>Analytical Expertise</span>
                  <p>{selectedRequest.certifications || selectedRequest.specialization || "Not provided"}</p>
                </div>
              )}

              <div className="review-copy-block">
                <span>Certifications</span>
                <p>{selectedRequest.certifications || "Not provided"}</p>
              </div>

              <div className="review-copy-block">
                <span>Professional Bio</span>
                <p>{selectedRequest.professional_bio || "Not provided"}</p>
              </div>

              {supportingDocuments.length > 0 && (
                <div className="review-copy-block">
                  <span>Professional Documents</span>
                  <div className="professional-document-list">
                    {supportingDocuments.map((document) => (
                      <a
                        className="professional-document-link"
                        href={resolveApiAssetUrl(document.url)}
                        key={`${document.label}-${document.url}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <ExternalLink size={16} />
                        {document.label}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {selectedRequest.status === "PENDING" && (
                <label className="professional-textarea-field">
                  <span>Rejection Reason</span>
                  <textarea
                    rows="3"
                    value={rejectionReason}
                    onChange={(event) => setRejectionReason(event.target.value)}
                    placeholder="Required when rejecting."
                  />
                </label>
              )}

              {selectedRequest.status !== "PENDING" && selectedRequest.rejection_reason && (
                <div className="professional-rejection">
                  {selectedRequest.rejection_reason}
                </div>
              )}

              <div className="professional-review-actions">
                <button
                  className="secondary-button"
                  onClick={() => setSelectedRequest(null)}
                  type="button"
                >
                  Close
                </button>

                {selectedRequest.status === "PENDING" && (
                  <>
                    <button
                      className="danger-button"
                      disabled={Boolean(actionLoading) || !rejectionReason.trim()}
                      onClick={handleReject}
                      type="button"
                    >
                      <XCircle size={17} />
                      {actionLoading === "reject" ? "Rejecting..." : "Reject"}
                    </button>

                    <button
                      className="primary-button"
                      disabled={Boolean(actionLoading)}
                      onClick={handleApprove}
                      type="button"
                    >
                      <BadgeCheck size={17} />
                      {actionLoading === "approve" ? "Approving..." : "Approve"}
                    </button>
                  </>
                )}
              </div>
            </section>
          </div>
        )}
      </main>
    </DashboardLayout>
  );
}


export default AdminProfessionalRequests;
