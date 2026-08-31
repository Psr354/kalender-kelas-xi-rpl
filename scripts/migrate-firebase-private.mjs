import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import crypto from "node:crypto";

const PROJECT_ID = "kalenderpl";
const FIRESTORE_BASE = `https://firestore.googleapis.com/v1/projects/${PROJECT_ID}/databases/(default)/documents`;
const SERVER_BASE = process.env.PSR354_SERVER_BASE || "http://10.172.210.53:5050";
const ADMIN_EMAIL = process.env.PSR354_ADMIN_EMAIL || "admin@psr354.local";
const ADMIN_PASSWORD = process.env.PSR354_ADMIN_PASSWORD;
const AUTH_EXPORT_PATH = process.env.PSR354_AUTH_EXPORT || "firebase-export/auth-users.json";
const OUTPUT_DIR = "migration-output";

if (!ADMIN_PASSWORD) {
  console.error("Set PSR354_ADMIN_PASSWORD before running this script.");
  process.exit(1);
}

function readFirebaseAccessToken() {
  const configPath = path.join(os.homedir(), ".config", "configstore", "firebase-tools.json");
  const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
  const token = config.tokens?.access_token;
  if (!token) throw new Error("Firebase CLI access token was not found.");
  return token;
}

function firestoreValue(value) {
  if (!value || typeof value !== "object") return null;
  if ("stringValue" in value) return value.stringValue;
  if ("integerValue" in value) return Number(value.integerValue);
  if ("doubleValue" in value) return Number(value.doubleValue);
  if ("booleanValue" in value) return Boolean(value.booleanValue);
  if ("timestampValue" in value) return value.timestampValue;
  if ("arrayValue" in value) return (value.arrayValue.values || []).map(firestoreValue);
  if ("mapValue" in value) return firestoreDocument(value.mapValue.fields || {});
  return null;
}

function firestoreDocument(fields) {
  return Object.fromEntries(Object.entries(fields).map(([key, value]) => [key, firestoreValue(value)]));
}

async function getCollection(name, accessToken) {
  const response = await fetch(`${FIRESTORE_BASE}/${name}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (response.status === 404) return [];
  const data = await response.json();
  if (!response.ok) throw new Error(`Failed to fetch ${name}: ${response.status} ${JSON.stringify(data)}`);
  return (data.documents || []).map((doc) => ({
    id: doc.name.split("/").pop(),
    ...firestoreDocument(doc.fields || {}),
  }));
}

async function serverRequest(pathname, options = {}, cookie = "") {
  const response = await fetch(`${SERVER_BASE}${pathname}`, {
    headers: {
      "Content-Type": "application/json",
      ...(cookie ? { Cookie: cookie } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });
  const setCookie = response.headers.get("set-cookie") || "";
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(`${pathname} failed: ${response.status} ${JSON.stringify(body)}`);
  return { body, cookie: setCookie.split(";")[0] || cookie };
}

function temporaryPassword() {
  return crypto.randomBytes(12).toString("base64url");
}

const accessToken = readFirebaseAccessToken();
const authExport = JSON.parse(fs.readFileSync(AUTH_EXPORT_PATH, "utf8"));
const firebaseUsers = authExport.users || [];
const userDataDocs = await getCollection("userData", accessToken);
const adminDocs = await getCollection("admins", accessToken);
const userDataById = new Map(userDataDocs.map((doc) => [doc.id, doc]));
const adminIds = new Set(adminDocs.map((doc) => doc.id));

const users = firebaseUsers
  .filter((user) => user.localId && user.email && !user.disabled)
  .map((user) => ({
    id: user.localId,
    email: user.email,
    password: temporaryPassword(),
    isAdmin: adminIds.has(user.localId),
    userData: userDataById.get(user.localId) || {},
  }));

const login = await serverRequest("/api/login", {
  method: "POST",
  body: JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASSWORD }),
});

const imported = await serverRequest("/api/admin/import-users", {
  method: "POST",
  body: JSON.stringify({ users }),
}, login.cookie);

fs.mkdirSync(OUTPUT_DIR, { recursive: true });
const passwordReport = users.map(({ email, password, id, isAdmin }) => ({ email, password, id, isAdmin }));
fs.writeFileSync(path.join(OUTPUT_DIR, "temporary-passwords.json"), JSON.stringify(passwordReport, null, 2));

console.log(JSON.stringify({
  firebaseUsers: firebaseUsers.length,
  userDataDocs: userDataDocs.length,
  adminDocs: adminDocs.length,
  imported: imported.body.imported,
  passwordReport: path.join(OUTPUT_DIR, "temporary-passwords.json"),
}, null, 2));
