// ==============================================================================
// Migraflow Unified MongoDB Initialization Script
// Automatically provisions all MongoDB databases in the single MongoDB container
// ==============================================================================

const mongoDatabases = [
  'analytics_db',
  'complex_nosql_enterprise',
  'retail_experience_mongo',
  'complex_mongo_db',
  'analytics_production'
];

mongoDatabases.forEach(function (dbName) {
  const targetDb = db.getSiblingDB(dbName);
  const existingCols = targetDb.getCollectionNames();
  if (!existingCols.includes('_init_healthcheck')) {
    targetDb.createCollection('_init_healthcheck');
    targetDb.getCollection('_init_healthcheck').insertOne({
      initialized_at: new Date().toISOString(),
      database: dbName,
      status: 'active'
    });
    print(`[Migraflow Init] Successfully initialized MongoDB database: ${dbName}`);
  }
});
