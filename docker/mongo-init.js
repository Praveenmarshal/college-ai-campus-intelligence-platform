// docker/mongo-init.js
// Runs once when the MongoDB container is first created.
// Creates the application database and a dedicated app user (least privilege).
//
// Credentials come from environment variables injected via docker-compose.yml
// (MONGO_APP_USERNAME / MONGO_APP_PASSWORD, themselves sourced from your .env
// file) — nothing is hardcoded here.

const appUsername = process.env.MONGO_APP_USERNAME || 'campus_app';
const appPassword = process.env.MONGO_APP_PASSWORD;

if (!appPassword) {
  print('❌ MONGO_APP_PASSWORD is not set — refusing to create app user with no password.');
  print('   Set MONGO_APP_PASSWORD in your .env file before starting the mongo container.');
  quit(1);
}

db = db.getSiblingDB('campus_ai');

db.createUser({
  user: appUsername,
  pwd: appPassword,
  roles: [{ role: 'readWrite', db: 'campus_ai' }],
});

// Create collections up front so indexes can attach cleanly
const collections = [
  'users', 'students', 'faculty', 'attendance', 'placements',
  'fees', 'documents', 'chats', 'analytics', 'events',
  'library', 'hostel', 'notifications', 'audit_logs',
];

collections.forEach((name) => {
  db.createCollection(name);
});

print('✅ campus_ai database initialised with ' + collections.length + ' collections');
print('✅ App user "' + appUsername + '" created with readWrite role');

