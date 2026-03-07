import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProfile, updateProfile, uploadMedicalReport } from '../api/apiClient';

const physicalActivityOptions = ['Sedentary', 'Light', 'Moderate', 'Active'];
const primaryGoalOptions = ['Maintenance', 'Weight Loss', 'Glycemic Control'];
const dietaryPreferenceOptions = ['Vegetarian', 'Non-Vegetarian'];
const medicalReportAccept = '.pdf,.txt,.doc,.docx,image/*';

export default function Profile() {
  const navigate = useNavigate();
  const userId = localStorage.getItem('userId');

  const [form, setForm] = useState({
    user_id: userId || '',
    age: '',
    gender: '',
    height_cm: '',
    weight_kg: '',
    bmi: '',
    physical_activity_level: '',
    steps_per_day: '',
    sleep_hours: '',
    diabetes_duration_years: '',
    hba1c_percent: '',
    fasting_glucose_mg_dl: '',
    postprandial_glucose_mg_dl: '',
    triglycerides_mg_dl: '',
    ldl_cholesterol_mg_dl: '',
    hdl_cholesterol_mg_dl: '',
    systolic_bp_mmHg: '',
    diastolic_bp_mmHg: '',
    egfr_ml_min_1_73m2: '',
    smoking_status: '',
    alcohol_use: '',
    primary_goal: '',
    dietary_preference: ''
  });
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  useEffect(() => {
    if (!userId) {
      navigate('/login');
    }
  }, [userId, navigate]);

  useEffect(() => {
    const fetchProfile = async () => {
      if (!userId) return;
      setLoading(true);
      try {
        const { data } = await getProfile(userId);
        setForm((prev) => ({
          ...prev,
          ...Object.fromEntries(
            Object.entries(data).map(([k, v]) => [k, v ?? ''])
          )
        }));
      } catch {
        setError('Failed to load profile data.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [userId]);

  useEffect(() => {
    const h = parseFloat(form.height_cm);
    const w = parseFloat(form.weight_kg);
    if (h > 0 && w > 0) {
      const bmi = w / Math.pow(h / 100, 2);
      setForm((prev) => ({ ...prev, bmi: bmi.toFixed(1) }));
    }
  }, [form.height_cm, form.weight_kg]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleUpload = async (e) => {
    if (!userId) return;
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    setInfo('');
    setUploading(true);
    try {
      const { data } = await uploadMedicalReport(userId, file);
      const extracted = data.extracted_fields || {};
      setForm((prev) => ({
        ...prev,
        ...Object.fromEntries(
          Object.entries(extracted).map(([k, v]) => [k, v ?? ''])
        )
      }));
      setInfo('Values extracted from medical report. Please review and save.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process medical report');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userId) return;
    setSaving(true);
    setError('');
    setInfo('');
    try {
      const payload = {
        ...form,
        age: form.age ? Number(form.age) : null,
        height_cm: form.height_cm ? Number(form.height_cm) : null,
        weight_kg: form.weight_kg ? Number(form.weight_kg) : null,
        bmi: form.bmi ? Number(form.bmi) : null,
        steps_per_day: form.steps_per_day ? Number(form.steps_per_day) : null,
        sleep_hours: form.sleep_hours ? Number(form.sleep_hours) : null,
        diabetes_duration_years: form.diabetes_duration_years
          ? Number(form.diabetes_duration_years)
          : null,
        hba1c_percent: form.hba1c_percent ? Number(form.hba1c_percent) : null,
        fasting_glucose_mg_dl: form.fasting_glucose_mg_dl
          ? Number(form.fasting_glucose_mg_dl)
          : null,
        postprandial_glucose_mg_dl: form.postprandial_glucose_mg_dl
          ? Number(form.postprandial_glucose_mg_dl)
          : null,
        triglycerides_mg_dl: form.triglycerides_mg_dl
          ? Number(form.triglycerides_mg_dl)
          : null,
        ldl_cholesterol_mg_dl: form.ldl_cholesterol_mg_dl
          ? Number(form.ldl_cholesterol_mg_dl)
          : null,
        hdl_cholesterol_mg_dl: form.hdl_cholesterol_mg_dl
          ? Number(form.hdl_cholesterol_mg_dl)
          : null,
        systolic_bp_mmHg: form.systolic_bp_mmHg
          ? Number(form.systolic_bp_mmHg)
          : null,
        diastolic_bp_mmHg: form.diastolic_bp_mmHg
          ? Number(form.diastolic_bp_mmHg)
          : null,
        egfr_ml_min_1_73m2: form.egfr_ml_min_1_73m2
          ? Number(form.egfr_ml_min_1_73m2)
          : null,
        smoking_status: form.smoking_status
          ? Number(form.smoking_status)
          : 0,
        alcohol_use: form.alcohol_use ? Number(form.alcohol_use) : 0
      };
      await updateProfile(payload);
      localStorage.setItem('profileCompleted', 'true');
      setInfo('Profile saved successfully.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="layout-main">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Medical Profile</h1>
          <p className="text-sm text-slate-500">
            Complete your profile to unlock personalized nutrition and assistant features.
          </p>
        </div>
        <div className="hidden sm:flex items-center gap-2">
          <label className={`secondary-btn cursor-pointer text-xs sm:text-sm ${uploading ? 'opacity-50 pointer-events-none' : ''}`}>
            <span>{uploading ? 'Processing report...' : 'Upload medical report (PDF/Image/TXT/DOC/DOCX)'}</span>
            <input type="file" accept={medicalReportAccept} className="hidden" onChange={handleUpload} disabled={uploading} />
          </label>
        </div>
      </div>

      <div className="sm:hidden mb-4">
        <label className={`secondary-btn w-full justify-center cursor-pointer text-xs sm:text-sm ${uploading ? 'opacity-50 pointer-events-none' : ''}`}>
          <span>{uploading ? 'Processing report...' : 'Upload medical report (PDF/Image/TXT/DOC/DOCX)'}</span>
          <input type="file" accept={medicalReportAccept} className="hidden" onChange={handleUpload} disabled={uploading} />
        </label>
      </div>

      {loading && (
        <p className="mb-3 text-sm text-slate-500">Loading existing profile if available...</p>
      )}
      {uploading && (
        <div className="mb-3 flex items-center gap-2 rounded-md bg-blue-50 px-3 py-2 text-sm text-blue-700 border border-blue-100">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-700 border-t-transparent"></div>
          Analyzing your medical report, please wait...
        </div>
      )}
      {error && (
        <div className="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 border border-red-100">
          {error}
        </div>
      )}
      {info && (
        <div className="mb-3 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700 border border-emerald-100">
          {info}
        </div>
      )}

      <form onSubmit={handleSubmit} className={`card ${uploading ? 'opacity-60 pointer-events-none' : ''}`}>
        <div className="card-body space-y-6">
          <section className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="label">Age</label>
              <input
                name="age"
                className="input-field"
                value={form.age}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="label">Gender</label>
              <select
                name="gender"
                className="input-field"
                value={form.gender}
                onChange={handleChange}
              >
                <option value="">Select</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
            </div>
            <div>
              <label className="label">Dietary preference</label>
              <select
                name="dietary_preference"
                className="input-field"
                value={form.dietary_preference}
                onChange={handleChange}
              >
                <option value="">Select</option>
                {dietaryPreferenceOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-4">
            <div>
              <label className="label">Height (cm)</label>
              <input
                name="height_cm"
                className="input-field"
                value={form.height_cm}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="label">Weight (kg)</label>
              <input
                name="weight_kg"
                className="input-field"
                value={form.weight_kg}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="label">BMI</label>
              <input
                name="bmi"
                className="input-field bg-slate-50"
                value={form.bmi}
                readOnly
              />
            </div>
            <div>
              <label className="label">Primary goal</label>
              <select
                name="primary_goal"
                className="input-field"
                value={form.primary_goal}
                onChange={handleChange}
              >
                <option value="">Select</option>
                {primaryGoalOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="label">Physical activity</label>
              <select
                name="physical_activity_level"
                className="input-field"
                value={form.physical_activity_level}
                onChange={handleChange}
              >
                <option value="">Select</option>
                {physicalActivityOptions.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Steps per day</label>
              <input
                name="steps_per_day"
                className="input-field"
                value={form.steps_per_day}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="label">Sleep (hours)</label>
              <input
                name="sleep_hours"
                className="input-field"
                value={form.sleep_hours}
                onChange={handleChange}
              />
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-4">
            <div>
              <label className="label">Diabetes duration (years)</label>
              <input
                name="diabetes_duration_years"
                className="input-field"
                value={form.diabetes_duration_years}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="label">HbA1c (%)</label>
              <input
                name="hba1c_percent"
                className="input-field"
                value={form.hba1c_percent}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="label">Fasting glucose (mg/dL)</label>
              <input
                name="fasting_glucose_mg_dl"
                className="input-field"
                value={form.fasting_glucose_mg_dl}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="label">Postprandial glucose (mg/dL)</label>
              <input
                name="postprandial_glucose_mg_dl"
                className="input-field"
                value={form.postprandial_glucose_mg_dl}
                onChange={handleChange}
              />
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-4">
            <div>
              <label className="label">Triglycerides (mg/dL)</label>
              <input
                name="triglycerides_mg_dl"
                className="input-field"
                value={form.triglycerides_mg_dl}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="label">LDL (mg/dL)</label>
              <input
                name="ldl_cholesterol_mg_dl"
                className="input-field"
                value={form.ldl_cholesterol_mg_dl}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="label">HDL (mg/dL)</label>
              <input
                name="hdl_cholesterol_mg_dl"
                className="input-field"
                value={form.hdl_cholesterol_mg_dl}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="label">eGFR (ml/min/1.73m²)</label>
              <input
                name="egfr_ml_min_1_73m2"
                className="input-field"
                value={form.egfr_ml_min_1_73m2}
                onChange={handleChange}
              />
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="label">Systolic BP (mmHg)</label>
              <input
                name="systolic_bp_mmHg"
                className="input-field"
                value={form.systolic_bp_mmHg}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="label">Diastolic BP (mmHg)</label>
              <input
                name="diastolic_bp_mmHg"
                className="input-field"
                value={form.diastolic_bp_mmHg}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="label">Smoking / Alcohol</label>
              <div className="grid grid-cols-2 gap-2">
                <select
                  name="smoking_status"
                  className="input-field"
                  value={form.smoking_status}
                  onChange={handleChange}
                >
                  <option value="">Smoking</option>
                  <option value="0">No</option>
                  <option value="1">Yes</option>
                </select>
                <select
                  name="alcohol_use"
                  className="input-field"
                  value={form.alcohol_use}
                  onChange={handleChange}
                >
                  <option value="">Alcohol</option>
                  <option value="0">No</option>
                  <option value="1">Yes</option>
                </select>
              </div>
            </div>
          </section>

          <div className="flex justify-end gap-3 pt-2 border-t border-slate-100">
            <button
              type="submit"
              className="primary-btn"
              disabled={saving || uploading}
            >
              {saving ? 'Saving...' : 'Save profile'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}