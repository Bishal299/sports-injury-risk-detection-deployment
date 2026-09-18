import React, { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Check, FileUp, Link, Send, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";

import DashboardLayout from "../layouts/DashboardLayout";
import {
  getCurrentUser,
  submitCoachApplication,
  submitPhysiotherapistApplication,
  submitProfessionalRoleRequest,
  submitSportsScientistApplication,
  updateCurrentUser,
} from "../services/api";
import "../styles/professional-role.css";


const roleConfig = {
  COACH: {
    eyebrow: "COACH VERIFICATION",
    title: "Coach Application",
    roleLabel: "Coach",
    intro: "Tell us about your coaching background so an administrator can review your request.",
    endpoint: "coach",
    fields: {
      primarySport: "Primary Sport",
      specialization: "Coaching Specialization",
      specializationPlaceholder: "Strength, technique, rehab return-to-play",
      organization: "Organization/Club",
      certifications: "Certifications",
      bioPlaceholder: "Briefly describe your coaching background.",
      documentHelp: "Upload one professional document if you want to support the application.",
    },
  },
  PHYSIOTHERAPIST: {
    eyebrow: "PHYSIOTHERAPIST VERIFICATION",
    title: "Physiotherapist Application",
    roleLabel: "Physiotherapist",
    intro: "Apply as a verified physiotherapist focused on rehabilitation, recovery, movement correction, and injury-risk monitoring.",
    endpoint: "physiotherapist",
  },
  SPORTS_SCIENTIST: {
    eyebrow: "SPORTS SCIENTIST VERIFICATION",
    title: "Sports Scientist Application",
    roleLabel: "Sports Scientist",
    intro: "Apply for verified access to biomechanical analytics, movement-pattern review, and research-oriented sports-science workflows.",
    endpoint: "sports-scientist",
  },
};

const initialForm = {
  full_name: "",
  email: "",
  phone: "",
  years_of_experience: "",
  primary_sport: "",
  other_sports: "",
  specialization: "",
  organization: "",
  certifications: "",
  professional_bio: "",
  supporting_document: null,
  supporting_document_url: "",
};

const PHYSIO_DRAFT_KEY = "professionalApplicationDraft:PHYSIOTHERAPIST";

const physiotherapistInitialForm = {
  full_name: "",
  email: "",
  phone: "",
  professional_bio: "",
  highest_qualification: "",
  qualification_other: "",
  specialization: "",
  specialization_other: "",
  registration_number: "",
  registration_authority: "",
  license_expiry_date: "",
  years_of_experience: "",
  sports_physiotherapy_experience: "",
  organization: "",
  sports_worked_with: [],
  other_sport: "",
  areas_of_expertise: [],
  certifications: [],
  platform_statement: "",
  athlete_support_statement: "",
  license_document_url: "",
  qualification_document_url: "",
  certification_documents_url: "",
  license_document: null,
  qualification_document: null,
  certification_documents: null,
  license_document_name: "",
  qualification_document_name: "",
  certification_documents_name: "",
  declaration_accuracy: false,
  declaration_verification: false,
  declaration_relationship_access: false,
};

const sportsScientistInitialForm = {
  full_name: "",
  email: "",
  phone: "",
  specialization: "",
  years_of_experience: "",
  organization: "",
  professional_bio: "",
  interested_sports: [],
  other_sport: "",
  analytical_expertise: [],
  supporting_document: null,
  supporting_document_url: "",
};

const physiotherapistSteps = [
  "Basic Information",
  "Qualification",
  "Experience & Expertise",
  "Certifications, Documents & Declaration",
];

const qualificationOptions = ["BPT", "MPT", "PhD", "Other"];
const specializationOptions = ["Sports Physiotherapy", "Orthopedic / Musculoskeletal", "Other"];
const sportsOptions = [
  "Football",
  "Cricket",
  "Athletics",
  "Basketball",
  "Badminton",
  "Tennis",
  "Gym / Fitness",
  "Other",
];
const expertiseOptions = [
  "Injury Rehabilitation",
  "Recovery Monitoring",
  "Movement Assessment",
  "Movement Correction",
  "Injury Prevention",
  "Return-to-Sport",
  "Mobility & Flexibility",
  "Strength & Stability",
  "Balance & Coordination",
];

const sportsScientistExpertiseOptions = [
  "Biomechanical Analysis",
  "Movement Quality Assessment",
  "Performance Analytics",
  "Injury Risk Factor Analysis",
  "Gait / Running Mechanics",
  "Landing Mechanics",
  "Symmetry Analysis",
  "Research Reporting",
];

function readPhysiotherapistDraft() {
  try {
    const stored = window.localStorage.getItem(PHYSIO_DRAFT_KEY);
    if (!stored) {
      return physiotherapistInitialForm;
    }

    return {
      ...physiotherapistInitialForm,
      ...JSON.parse(stored),
      license_document: null,
      qualification_document: null,
      certification_documents: null,
    };
  } catch {
    return physiotherapistInitialForm;
  }
}

function getPersistablePhysiotherapistForm(formData) {
  const {
    license_document,
    qualification_document,
    certification_documents,
    ...persistable
  } = formData;

  return persistable;
}

function formatCertifications(certifications) {
  const entries = certifications
    .filter((certification) => certification.name || certification.issuer || certification.year || certification.expiry_date)
    .map((certification, index) => {
      const meta = [
        certification.issuer ? `Issuing Organization: ${certification.issuer}` : null,
        certification.year ? `Year Obtained: ${certification.year}` : null,
        certification.expiry_date ? `Expiry Date: ${certification.expiry_date}` : null,
      ].filter(Boolean).join(", ");

      return `${index + 1}. ${certification.name || "Certification"}${meta ? ` (${meta})` : ""}`;
    });

  return entries.length ? entries.join("\n") : null;
}

function getDocumentLabel(file, rememberedName, fallback) {
  if (file?.name) {
    return file.name;
  }

  if (rememberedName) {
    return `${rememberedName} - reselect after refresh`;
  }

  return fallback;
}

function ProfessionalApplication({ requestedRole = "COACH" }) {
  const navigate = useNavigate();
  const config = roleConfig[requestedRole] || roleConfig.COACH;
  const isPhysiotherapist = requestedRole === "PHYSIOTHERAPIST";
  const isSportsScientist = requestedRole === "SPORTS_SCIENTIST";
  const [formData, setFormData] = useState(() => (
    isPhysiotherapist
      ? readPhysiotherapistDraft()
      : isSportsScientist
        ? sportsScientistInitialForm
        : initialForm
  ));
  const [currentStep, setCurrentStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [loadingUser, setLoadingUser] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(null);

  const fieldText = config.fields || {};

  useEffect(() => {
    let cancelled = false;

    async function loadUser() {
      setLoadingUser(true);
      setError("");

      try {
        const user = await getCurrentUser();

        if (!cancelled) {
          setFormData((current) => ({
            ...current,
            full_name: user.name || current.full_name || "",
            email: user.email || current.email || "",
            phone: user.phone || current.phone || "",
          }));
        }
      } catch {
        if (!cancelled) {
          setError("Unable to load your account details.");
        }
      } finally {
        if (!cancelled) {
          setLoadingUser(false);
        }
      }
    }

    loadUser();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!isPhysiotherapist || loadingUser) {
      return;
    }

    window.localStorage.setItem(
      PHYSIO_DRAFT_KEY,
      JSON.stringify(getPersistablePhysiotherapistForm(formData))
    );
  }, [formData, isPhysiotherapist, loadingUser]);

  const selectedFileName = useMemo(
    () => formData.supporting_document?.name || "Choose document",
    [formData.supporting_document]
  );

  const handleChange = (event) => {
    const { name, value, files, type, checked } = event.target;

    setFormData((current) => ({
      ...current,
      [name]: files ? files[0] : (type === "checkbox" ? checked : value),
    }));
  };

  const handlePhysioDocumentChange = (event) => {
    const { name, files } = event.target;
    const file = files?.[0] || null;

    setFormData((current) => ({
      ...current,
      [name]: file,
      [`${name}_name`]: file?.name || "",
    }));
  };

  const toggleMultiSelect = (name, value) => {
    setFormData((current) => {
      const currentValues = current[name] || [];
      const nextValues = currentValues.includes(value)
        ? currentValues.filter((item) => item !== value)
        : [...currentValues, value];

      return {
        ...current,
        [name]: nextValues,
      };
    });
  };

  const addCertification = () => {
    setFormData((current) => ({
      ...current,
      certifications: [
        ...current.certifications,
        { name: "", issuer: "", year: "", expiry_date: "" },
      ],
    }));
  };

  const updateCertification = (index, field, value) => {
    setFormData((current) => ({
      ...current,
      certifications: current.certifications.map((certification, currentIndex) => (
        currentIndex === index
          ? { ...certification, [field]: value }
          : certification
      )),
    }));
  };

  const removeCertification = (index) => {
    setFormData((current) => ({
      ...current,
      certifications: current.certifications.filter((_, currentIndex) => currentIndex !== index),
    }));
  };

  const validatePhysiotherapistStep = (step) => {
    if (step === 0) {
      if (!formData.full_name.trim() || !formData.email.trim() || !formData.professional_bio.trim()) {
        return "Complete your name, email, and professional introduction.";
      }
    }

    if (step === 1) {
      if (
        !formData.highest_qualification ||
        (formData.highest_qualification === "Other" && !formData.qualification_other.trim()) ||
        !formData.specialization ||
        (formData.specialization === "Other" && !formData.specialization_other.trim()) ||
        !formData.registration_number.trim() ||
        !formData.registration_authority.trim()
      ) {
        return "Complete qualification, specialization, registration number, and registration authority.";
      }
    }

    if (step === 2) {
      if (
        formData.years_of_experience === "" ||
        formData.sports_physiotherapy_experience === "" ||
        formData.sports_worked_with.length === 0 ||
        (formData.sports_worked_with.includes("Other") && !formData.other_sport.trim()) ||
        formData.areas_of_expertise.length === 0
      ) {
        return "Complete experience, sports worked with, and areas of expertise.";
      }
    }

    if (step === 3) {
      const certificationsValid = formData.certifications.every((certification) => {
        const hasAnyValue = certification.name || certification.issuer || certification.year || certification.expiry_date;
        if (!hasAnyValue) {
          return true;
        }

        return certification.name && certification.issuer && certification.year;
      });

      if (!certificationsValid) {
        return "Certification entries need a name, issuing organization, and year obtained.";
      }

      if (!formData.platform_statement.trim() || !formData.athlete_support_statement.trim()) {
        return "Complete both professional statement fields.";
      }

      if (
        !formData.declaration_accuracy ||
        !formData.declaration_verification ||
        !formData.declaration_relationship_access
      ) {
        return "Accept all declarations before submitting.";
      }
    }

    return "";
  };

  const goToNextStep = () => {
    const validationError = validatePhysiotherapistStep(currentStep);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError("");
    setCurrentStep((step) => Math.min(step + 1, physiotherapistSteps.length - 1));
  };

  const submitCoach = async () => {
    return submitCoachApplication({
      ...formData,
      coaching_specialization: formData.specialization,
      requested_role: "COACH",
      years_of_experience: formData.years_of_experience
        ? Number(formData.years_of_experience)
        : "",
    });
  };

  const submitGenericProfessional = async () => {
    await updateCurrentUser({
      name: formData.full_name,
      phone: formData.phone || null,
    });

    return submitProfessionalRoleRequest({
      requested_role: requestedRole,
      primary_sport: formData.primary_sport,
      organization: formData.organization || null,
      specialization: [
        formData.specialization,
        formData.other_sports ? `Other sports / areas: ${formData.other_sports}` : "",
      ].filter(Boolean).join("\n"),
      years_of_experience: formData.years_of_experience
        ? Number(formData.years_of_experience)
        : null,
      certifications: formData.certifications || null,
      professional_bio: formData.professional_bio,
      supporting_document_url: formData.supporting_document_url || null,
    });
  };

  const validateSportsScientistForm = () => {
    if (!formData.full_name.trim()) {
      return "Enter your full name.";
    }

    if (
      !formData.specialization.trim() ||
      formData.years_of_experience === "" ||
      !formData.organization.trim() ||
      !formData.professional_bio.trim()
    ) {
      return "Complete specialization, experience, organization, and professional bio.";
    }

    if (Number(formData.years_of_experience) < 0) {
      return "Years of experience cannot be negative.";
    }

    if (
      formData.interested_sports.length === 0 ||
      (formData.interested_sports.includes("Other") && !formData.other_sport.trim())
    ) {
      return "Select at least one interested sport.";
    }

    if (formData.analytical_expertise.length === 0) {
      return "Select at least one analytical expertise area.";
    }

    return "";
  };

  const submitSportsScientist = async () => {
    const interestedSports = [
      ...formData.interested_sports.filter((sport) => sport !== "Other"),
      formData.interested_sports.includes("Other") && formData.other_sport
        ? `Other: ${formData.other_sport}`
        : null,
    ].filter(Boolean);
    const primarySport = interestedSports[0] || "";

    return submitSportsScientistApplication({
      requested_role: "SPORTS_SCIENTIST",
      full_name: formData.full_name,
      phone: formData.phone || "",
      specialization: formData.specialization,
      years_of_experience: formData.years_of_experience
        ? Number(formData.years_of_experience)
        : "",
      organization: formData.organization,
      professional_bio: formData.professional_bio,
      primary_sport: primarySport,
      interested_sports: interestedSports.join(", "),
      analytical_expertise: formData.analytical_expertise.join(", "),
      supporting_document_url: formData.supporting_document_url,
      supporting_document: formData.supporting_document,
    });
  };

  const submitPhysiotherapist = async () => {
    const sportsWorkedWith = [
      ...formData.sports_worked_with.filter((sport) => sport !== "Other"),
      formData.sports_worked_with.includes("Other") && formData.other_sport
        ? `Other: ${formData.other_sport}`
        : null,
    ].filter(Boolean).join(", ");
    const primarySport = formData.sports_worked_with.includes("Other")
      ? (formData.sports_worked_with.find((sport) => sport !== "Other") || formData.other_sport)
      : formData.sports_worked_with[0];

    return submitPhysiotherapistApplication({
      requested_role: "PHYSIOTHERAPIST",
      full_name: formData.full_name,
      phone: formData.phone || "",
      professional_bio: formData.professional_bio,
      highest_qualification: formData.highest_qualification,
      qualification_other: formData.qualification_other,
      specialization: formData.specialization,
      specialization_other: formData.specialization_other,
      registration_number: formData.registration_number,
      registration_authority: formData.registration_authority,
      license_expiry_date: formData.license_expiry_date,
      years_of_experience: formData.years_of_experience
        ? Number(formData.years_of_experience)
        : "",
      sports_physiotherapy_experience: formData.sports_physiotherapy_experience
        ? Number(formData.sports_physiotherapy_experience)
        : "",
      organization: formData.organization,
      primary_sport: primarySport,
      sports_worked_with: sportsWorkedWith,
      areas_of_expertise: formData.areas_of_expertise.join(", "),
      certifications: formatCertifications(formData.certifications),
      platform_statement: formData.platform_statement,
      athlete_support_statement: formData.athlete_support_statement,
      license_document_url: formData.license_document_url,
      qualification_document_url: formData.qualification_document_url,
      certification_documents_url: formData.certification_documents_url,
      license_document: formData.license_document,
      qualification_document: formData.qualification_document,
      certification_documents: formData.certification_documents,
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setSuccess(null);

    try {
      let result;
      if (config.endpoint === "coach") {
        result = await submitCoach();
      } else if (isSportsScientist) {
        const validationError = validateSportsScientistForm();
        if (validationError) {
          setError(validationError);
          setSubmitting(false);
          return;
        }
        result = await submitSportsScientist();
      } else if (isPhysiotherapist) {
        const validationError = validatePhysiotherapistStep(currentStep);
        if (validationError) {
          setError(validationError);
          setSubmitting(false);
          return;
        }
        result = await submitPhysiotherapist();
        window.localStorage.removeItem(PHYSIO_DRAFT_KEY);
      } else {
        result = await submitGenericProfessional();
      }

      setSuccess(result);
      window.dispatchEvent(new Event("professional-role-request-updated"));
    } catch (error) {
      setError(error.message || `Failed to submit ${config.roleLabel} application.`);
    } finally {
      setSubmitting(false);
    }
  };

  const renderPhysiotherapistWizard = () => (
    <form className="professional-form" onSubmit={handleSubmit}>
      <div className="professional-stepper" aria-label="Physiotherapist application progress">
        {physiotherapistSteps.map((step, index) => (
          <button
            className={`professional-step ${index === currentStep ? "active" : ""} ${index < currentStep ? "complete" : ""}`}
            key={step}
            onClick={() => {
              if (index <= currentStep) {
                setCurrentStep(index);
                setError("");
              }
            }}
            type="button"
          >
            <span>{index < currentStep ? <Check size={15} /> : index + 1}</span>
            {step}
          </button>
        ))}
      </div>

      {error && <div className="professional-form-error">{error}</div>}

      {currentStep === 0 && (
        <section className="professional-card">
          <div className="professional-card-header">
            <h2>Basic Information</h2>
            <p>Use your existing account identity and a concise professional introduction.</p>
          </div>

          {loadingUser ? (
            <>
              <div className="professional-skeleton wide" />
              <div className="professional-skeleton" />
            </>
          ) : (
            <>
              <div className="professional-field-grid two">
                <label>
                  <span>Full Name</span>
                  <input
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    required
                  />
                </label>

                <label>
                  <span>Email</span>
                  <input
                    name="email"
                    value={formData.email}
                    readOnly
                  />
                </label>

                <label>
                  <span>Phone Number</span>
                  <input
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="Optional"
                  />
                </label>
              </div>

              <label className="professional-textarea-field">
                <span>Professional Bio / Short Introduction</span>
                <textarea
                  name="professional_bio"
                  value={formData.professional_bio}
                  onChange={handleChange}
                  rows="4"
                  maxLength="700"
                  placeholder="Summarize your physiotherapy background and athlete-care focus."
                  required
                />
              </label>
            </>
          )}
        </section>
      )}

      {currentStep === 1 && (
        <section className="professional-card">
          <div className="professional-card-header">
            <h2>Professional Qualification</h2>
            <p>Share registration and qualification details relevant to physiotherapy practice.</p>
          </div>

          <div className="professional-field-grid two">
            <label>
              <span>Highest Qualification</span>
              <select
                name="highest_qualification"
                value={formData.highest_qualification}
                onChange={handleChange}
                required
              >
                <option value="">Select qualification</option>
                {qualificationOptions.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>

            {formData.highest_qualification === "Other" && (
              <label>
                <span>Other Qualification</span>
                <input
                  name="qualification_other"
                  value={formData.qualification_other}
                  onChange={handleChange}
                  required
                />
              </label>
            )}

            <label>
              <span>Physiotherapy Specialization</span>
              <select
                name="specialization"
                value={formData.specialization}
                onChange={handleChange}
                required
              >
                <option value="">Select specialization</option>
                {specializationOptions.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>

            {formData.specialization === "Other" && (
              <label>
                <span>Other Specialization</span>
                <input
                  name="specialization_other"
                  value={formData.specialization_other}
                  onChange={handleChange}
                  required
                />
              </label>
            )}

            <label>
              <span>Professional Registration / License Number</span>
              <input
                name="registration_number"
                value={formData.registration_number}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              <span>Registration Authority / Council</span>
              <input
                name="registration_authority"
                value={formData.registration_authority}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              <span>License Expiry Date</span>
              <input
                name="license_expiry_date"
                type="date"
                value={formData.license_expiry_date}
                onChange={handleChange}
              />
            </label>
          </div>
        </section>
      )}

      {currentStep === 2 && (
        <section className="professional-card">
          <div className="professional-card-header">
            <h2>Experience & Expertise</h2>
            <p>Focus on sports physiotherapy, rehabilitation, and movement-correction experience.</p>
          </div>

          <div className="professional-field-grid two">
            <label>
              <span>Years of Professional Experience</span>
              <input
                min="0"
                name="years_of_experience"
                type="number"
                value={formData.years_of_experience}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              <span>Years of Sports Physiotherapy Experience</span>
              <input
                min="0"
                name="sports_physiotherapy_experience"
                type="number"
                value={formData.sports_physiotherapy_experience}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              <span>Current / Previous Organization</span>
              <input
                name="organization"
                value={formData.organization}
                onChange={handleChange}
                placeholder="Optional"
              />
            </label>
          </div>

          <div className="professional-choice-section">
            <span>Sports Worked With</span>
            <div className="professional-choice-grid">
              {sportsOptions.map((sport) => (
                <label className="professional-choice" key={sport}>
                  <input
                    checked={formData.sports_worked_with.includes(sport)}
                    onChange={() => toggleMultiSelect("sports_worked_with", sport)}
                    type="checkbox"
                  />
                  {sport}
                </label>
              ))}
            </div>
            {formData.sports_worked_with.includes("Other") && (
              <input
                className="professional-inline-input"
                name="other_sport"
                value={formData.other_sport}
                onChange={handleChange}
                placeholder="Other sport or athlete group"
              />
            )}
          </div>

          <div className="professional-choice-section">
            <span>Areas of Expertise</span>
            <div className="professional-choice-grid">
              {expertiseOptions.map((expertise) => (
                <label className="professional-choice" key={expertise}>
                  <input
                    checked={formData.areas_of_expertise.includes(expertise)}
                    onChange={() => toggleMultiSelect("areas_of_expertise", expertise)}
                    type="checkbox"
                  />
                  {expertise}
                </label>
              ))}
            </div>
          </div>
        </section>
      )}

      {currentStep === 3 && (
        <section className="professional-card">
          <div className="professional-card-header">
            <h2>Certifications, Documents & Declaration</h2>
            <p>Add relevant optional certifications, upload or link documents, and confirm the verification rules.</p>
          </div>

          <div className="professional-certification-list">
            <div className="professional-section-row">
              <h3>Certifications</h3>
              <button className="secondary-button" onClick={addCertification} type="button">
                Add Certification
              </button>
            </div>

            {formData.certifications.length === 0 && (
              <p className="professional-muted">No certification entries added.</p>
            )}

            {formData.certifications.map((certification, index) => (
              <div className="professional-certification-row" key={`certification-${index}`}>
                <div className="professional-field-grid two">
                  <label>
                    <span>Certification Name</span>
                    <input
                      value={certification.name}
                      onChange={(event) => updateCertification(index, "name", event.target.value)}
                    />
                  </label>
                  <label>
                    <span>Issuing Organization</span>
                    <input
                      value={certification.issuer}
                      onChange={(event) => updateCertification(index, "issuer", event.target.value)}
                    />
                  </label>
                  <label>
                    <span>Year Obtained</span>
                    <input
                      min="1950"
                      type="number"
                      value={certification.year}
                      onChange={(event) => updateCertification(index, "year", event.target.value)}
                    />
                  </label>
                  <label>
                    <span>Expiry Date</span>
                    <input
                      type="date"
                      value={certification.expiry_date}
                      onChange={(event) => updateCertification(index, "expiry_date", event.target.value)}
                    />
                  </label>
                </div>
                <button className="secondary-button" onClick={() => removeCertification(index)} type="button">
                  Remove
                </button>
              </div>
            ))}
          </div>

          <div className="professional-documents-grid">
            <PhysiotherapistDocumentInput
              fileName={getDocumentLabel(formData.license_document, formData.license_document_name, "Upload license document")}
              fileNameField="license_document"
              linkName="license_document_url"
              linkValue={formData.license_document_url}
              onFileChange={handlePhysioDocumentChange}
              onTextChange={handleChange}
              title="Professional Registration / License Document"
            />
            <PhysiotherapistDocumentInput
              fileName={getDocumentLabel(formData.qualification_document, formData.qualification_document_name, "Upload qualification certificate")}
              fileNameField="qualification_document"
              linkName="qualification_document_url"
              linkValue={formData.qualification_document_url}
              onFileChange={handlePhysioDocumentChange}
              onTextChange={handleChange}
              title="Qualification Certificate"
            />
            <PhysiotherapistDocumentInput
              fileName={getDocumentLabel(formData.certification_documents, formData.certification_documents_name, "Upload certification documents")}
              fileNameField="certification_documents"
              linkName="certification_documents_url"
              linkValue={formData.certification_documents_url}
              onFileChange={handlePhysioDocumentChange}
              onTextChange={handleChange}
              title="Relevant Certification Documents"
              optional
            />
          </div>

          <div className="professional-field-grid two">
            <label className="professional-textarea-field">
              <span>Why do you want to join this platform?</span>
              <textarea
                name="platform_statement"
                value={formData.platform_statement}
                onChange={handleChange}
                rows="4"
                maxLength="700"
                required
              />
            </label>

            <label className="professional-textarea-field">
              <span>What type of athlete support can you provide?</span>
              <textarea
                name="athlete_support_statement"
                value={formData.athlete_support_statement}
                onChange={handleChange}
                rows="4"
                maxLength="700"
                required
              />
            </label>
          </div>

          <div className="professional-declaration-list">
            <label>
              <input
                checked={formData.declaration_accuracy}
                name="declaration_accuracy"
                onChange={handleChange}
                type="checkbox"
              />
              Information provided is accurate.
            </label>
            <label>
              <input
                checked={formData.declaration_verification}
                name="declaration_verification"
                onChange={handleChange}
                type="checkbox"
              />
              I understand that professional access requires admin verification.
            </label>
            <label>
              <input
                checked={formData.declaration_relationship_access}
                name="declaration_relationship_access"
                onChange={handleChange}
                type="checkbox"
              />
              I understand that approval does not automatically grant access to athlete private data.
            </label>
          </div>
        </section>
      )}

      <div className="professional-form-actions split">
        <button
          className="secondary-button"
          disabled={currentStep === 0 || submitting}
          onClick={() => {
            setCurrentStep((step) => Math.max(step - 1, 0));
            setError("");
          }}
          type="button"
        >
          Back
        </button>

        {currentStep < physiotherapistSteps.length - 1 ? (
          <button className="primary-button" disabled={loadingUser} onClick={goToNextStep} type="button">
            Continue
          </button>
        ) : (
          <button
            className="primary-button"
            disabled={submitting || loadingUser}
            type="submit"
          >
            <Send size={17} />
            {submitting ? "Submitting..." : "Submit Application"}
          </button>
        )}
      </div>
    </form>
  );

  const renderSportsScientistForm = () => (
    <form className="professional-form" onSubmit={handleSubmit}>
      {error && <div className="professional-form-error">{error}</div>}

      <section className="professional-card">
        <div className="professional-card-header">
          <h2>Personal Details</h2>
          <p>These use your existing account identity where possible.</p>
        </div>

        {loadingUser ? (
          <>
            <div className="professional-skeleton wide" />
            <div className="professional-skeleton" />
          </>
        ) : (
          <div className="professional-field-grid two">
            <label>
              <span>Full Name</span>
              <input
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              <span>Email</span>
              <input
                name="email"
                value={formData.email}
                readOnly
              />
            </label>

            <label>
              <span>Phone</span>
              <input
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="Optional"
              />
            </label>
          </div>
        )}
      </section>

      <section className="professional-card">
        <div className="professional-card-header">
          <h2>Sports Science Profile</h2>
          <p>Share the analytical background an administrator should verify.</p>
        </div>

        <div className="professional-field-grid two">
          <label>
            <span>Area of Specialization</span>
            <input
              name="specialization"
              value={formData.specialization}
              onChange={handleChange}
              placeholder="Biomechanics, performance analytics, movement science"
              required
            />
          </label>

          <label>
            <span>Years of Experience</span>
            <input
              min="0"
              name="years_of_experience"
              type="number"
              value={formData.years_of_experience}
              onChange={handleChange}
              required
            />
          </label>

          <label>
            <span>Current Organization / Institution</span>
            <input
              name="organization"
              value={formData.organization}
              onChange={handleChange}
              required
            />
          </label>
        </div>

        <label className="professional-textarea-field">
          <span>Professional Bio / Experience Summary</span>
          <textarea
            name="professional_bio"
            value={formData.professional_bio}
            onChange={handleChange}
            rows="5"
            maxLength="900"
            placeholder="Summarize your sports-science background, analysis experience, and relevant athlete or research work."
            required
          />
        </label>
      </section>

      <section className="professional-card">
        <div className="professional-card-header">
          <h2>Analytical Scope</h2>
          <p>Select the sports and analysis areas relevant to your application.</p>
        </div>

        <div className="professional-choice-section">
          <span>Interested Sports</span>
          <div className="professional-choice-grid">
            {sportsOptions.map((sport) => (
              <label className="professional-choice" key={sport}>
                <input
                  checked={formData.interested_sports.includes(sport)}
                  onChange={() => toggleMultiSelect("interested_sports", sport)}
                  type="checkbox"
                />
                {sport}
              </label>
            ))}
          </div>
        </div>

        {formData.interested_sports.includes("Other") && (
          <div className="professional-field-grid two">
            <label>
              <span>Other Sport / Area</span>
              <input
                name="other_sport"
                value={formData.other_sport}
                onChange={handleChange}
                required
              />
            </label>
          </div>
        )}

        <div className="professional-choice-section">
          <span>Analytical Expertise</span>
          <div className="professional-choice-grid">
            {sportsScientistExpertiseOptions.map((expertise) => (
              <label className="professional-choice" key={expertise}>
                <input
                  checked={formData.analytical_expertise.includes(expertise)}
                  onChange={() => toggleMultiSelect("analytical_expertise", expertise)}
                  type="checkbox"
                />
                {expertise}
              </label>
            ))}
          </div>
        </div>
      </section>

      <section className="professional-card">
        <div className="professional-card-header">
          <h2>Supporting Documentation</h2>
          <p>Provide a document or secure link if you want to support the application.</p>
        </div>

        <label className="professional-support-link">
          <span>
            <Link size={17} />
            Supporting Document Link
          </span>
          <input
            name="supporting_document_url"
            type="url"
            value={formData.supporting_document_url}
            onChange={handleChange}
            placeholder="https://..."
          />
        </label>

        <label className="professional-file-drop compact">
          <FileUp size={22} />
          <span>{selectedFileName}</span>
          <input
            name="supporting_document"
            type="file"
            onChange={handleChange}
            accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
          />
        </label>
      </section>

      <div className="professional-form-actions">
        <button
          className="primary-button"
          disabled={submitting || loadingUser}
          type="submit"
        >
          <Send size={17} />
          {submitting ? "Submitting..." : "Submit Application"}
        </button>
      </div>
    </form>
  );

  const renderDefaultForm = () => (
    <form className="professional-form" onSubmit={handleSubmit}>
      {error && <div className="professional-form-error">{error}</div>}

      <section className="professional-card">
        <div className="professional-card-header">
          <h2>Personal Details</h2>
          <p>These use your existing account identity where possible.</p>
        </div>

        {loadingUser ? (
          <>
            <div className="professional-skeleton wide" />
            <div className="professional-skeleton" />
          </>
        ) : (
          <div className="professional-field-grid two">
            <label>
              <span>Full Name</span>
              <input
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              <span>Phone</span>
              <input
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="Optional"
              />
            </label>
          </div>
        )}
      </section>

      <section className="professional-card">
        <div className="professional-card-header">
          <h2>Professional Details</h2>
          <p>{config.roleLabel} verification is based on experience, professional context, and credentials.</p>
        </div>

        <div className="professional-field-grid two">
          <label>
            <span>Years of Experience</span>
            <input
              min="0"
              name="years_of_experience"
              type="number"
              value={formData.years_of_experience}
              onChange={handleChange}
              required
            />
          </label>

          <label>
            <span>{fieldText.primarySport}</span>
            <input
              name="primary_sport"
              value={formData.primary_sport}
              onChange={handleChange}
              required
            />
          </label>

          <label>
            <span>Other Sports / Areas</span>
            <input
              name="other_sports"
              value={formData.other_sports}
              onChange={handleChange}
              placeholder="Optional"
            />
          </label>

          <label>
            <span>{fieldText.specialization}</span>
            <input
              name="specialization"
              value={formData.specialization}
              onChange={handleChange}
              placeholder={fieldText.specializationPlaceholder}
              required
            />
          </label>

          <label>
            <span>{fieldText.organization}</span>
            <input
              name="organization"
              value={formData.organization}
              onChange={handleChange}
              placeholder="Optional"
            />
          </label>

          <label>
            <span>{fieldText.certifications}</span>
            <input
              name="certifications"
              value={formData.certifications}
              onChange={handleChange}
              placeholder="Optional"
            />
          </label>
        </div>

        <label className="professional-textarea-field">
          <span>Professional Bio</span>
          <textarea
            name="professional_bio"
            value={formData.professional_bio}
            onChange={handleChange}
            rows="5"
            placeholder={fieldText.bioPlaceholder}
            required
          />
        </label>
      </section>

      <section className="professional-card">
        <div className="professional-card-header">
          <h2>Supporting Documentation</h2>
          <p>{fieldText.documentHelp}</p>
        </div>

        {config.endpoint === "coach" ? (
          <label className="professional-file-drop">
            <FileUp size={24} />
            <span>{selectedFileName}</span>
            <input
              name="supporting_document"
              type="file"
              onChange={handleChange}
              accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
            />
          </label>
        ) : (
          <label className="professional-support-link">
            <span>
              <Link size={17} />
              Supporting Document Link
            </span>
            <input
              name="supporting_document_url"
              type="url"
              value={formData.supporting_document_url}
              onChange={handleChange}
              placeholder="https://..."
            />
          </label>
        )}
      </section>

      <div className="professional-form-actions">
        <button
          className="primary-button"
          disabled={submitting || loadingUser}
          type="submit"
        >
          <Send size={17} />
          {submitting ? "Submitting..." : "Submit Application"}
        </button>
      </div>
    </form>
  );

  return (
    <DashboardLayout>
      <main className="professional-page">
        <section className="page-header professional-header-row">
          <div>
            <p className="page-eyebrow">{config.eyebrow}</p>
            <h1>{config.title}</h1>
            <p>{config.intro}</p>
          </div>

          <button
            className="secondary-button"
            onClick={() => navigate("/request-professional-role")}
            type="button"
          >
            <ArrowLeft size={17} />
            Back
          </button>
        </section>

        {success ? (
          <section className="professional-status-card pending">
            <div className="professional-status-icon">
              <ShieldCheck size={24} />
            </div>

            <div>
              <span>Professional Role Request</span>
              <h2>Role: {config.roleLabel}</h2>
              <p>Status: Pending Review</p>
              <button
                className="primary-button"
                onClick={() => navigate("/request-professional-role")}
                type="button"
              >
                View Status
              </button>
            </div>
          </section>
        ) : (
          isPhysiotherapist
            ? renderPhysiotherapistWizard()
            : isSportsScientist
              ? renderSportsScientistForm()
              : renderDefaultForm()
        )}
      </main>
    </DashboardLayout>
  );
}

function PhysiotherapistDocumentInput({
  fileName,
  fileNameField,
  linkName,
  linkValue,
  onFileChange,
  onTextChange,
  optional = false,
  title,
}) {
  return (
    <div className="professional-document-control">
      <div>
        <h3>{title}</h3>
        <p>{optional ? "Optional" : "Upload a file or provide a secure link."}</p>
      </div>

      <label className="professional-support-link">
        <span>
          <Link size={17} />
          Document Link
        </span>
        <input
          name={linkName}
          type="url"
          value={linkValue}
          onChange={onTextChange}
          placeholder="https://..."
        />
      </label>

      <label className="professional-file-drop compact">
        <FileUp size={22} />
        <span>{fileName}</span>
        <input
          name={fileNameField}
          type="file"
          onChange={onFileChange}
          accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
        />
      </label>
    </div>
  );
}


export default ProfessionalApplication;
