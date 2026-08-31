const FIRESTORE_BASE = "https://firestore.googleapis.com/v1/projects/kalenderpl/databases/(default)/documents";
const FIREBASE_API_KEY = "AIzaSyAQrQdRkPyThLHxgGGHj0gQshtQ_ifCntE";
const SERVER_BASE = process.env.PSR354_SERVER_BASE || "http://10.172.210.53:5050";
const ADMIN_EMAIL = process.env.PSR354_ADMIN_EMAIL || "admin@psr354.local";
const ADMIN_PASSWORD = process.env.PSR354_ADMIN_PASSWORD;

if (!ADMIN_PASSWORD) {
  console.error("Set PSR354_ADMIN_PASSWORD before running this script.");
  process.exit(1);
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

async function getCollection(name) {
  const response = await fetch(`${FIRESTORE_BASE}/${name}?key=${FIREBASE_API_KEY}`);
  if (!response.ok) throw new Error(`Failed to fetch ${name}: ${response.status}`);
  const data = await response.json();
  return (data.documents || []).map((doc) => ({
    id: doc.name.split("/").pop(),
    ...firestoreDocument(doc.fields || {}),
  }));
}

async function serverRequest(path, options = {}, cookie = "") {
  const response = await fetch(`${SERVER_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(cookie ? { Cookie: cookie } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });
  const setCookie = response.headers.get("set-cookie") || "";
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(`${path} failed: ${response.status} ${JSON.stringify(body)}`);
  return { body, cookie: setCookie.split(";")[0] || cookie };
}

const login = await serverRequest("/api/login", {
  method: "POST",
  body: JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASSWORD }),
});
const cookie = login.cookie;

const events = await getCollection("events");
const schedule = await getCollection("schedule");
const announcements = await getCollection("announcements");

for (const item of events) {
  if (!item.date || !item.title) continue;
  await serverRequest("/api/events", {
    method: "POST",
    body: JSON.stringify({ date: item.date, title: item.title }),
  }, cookie);
}

for (const item of schedule) {
  await serverRequest(`/api/schedule/${encodeURIComponent(item.id)}`, {
    method: "PUT",
    body: JSON.stringify({ lessons: Array.isArray(item.lessons) ? item.lessons : [] }),
  }, cookie);
}

for (const item of announcements) {
  if (!item.text) continue;
  await serverRequest("/api/announcements", {
    method: "POST",
    body: JSON.stringify({ text: item.text }),
  }, cookie);
}

console.log(JSON.stringify({
  imported: {
    events: events.length,
    schedule: schedule.length,
    announcements: announcements.length,
  },
}, null, 2));
